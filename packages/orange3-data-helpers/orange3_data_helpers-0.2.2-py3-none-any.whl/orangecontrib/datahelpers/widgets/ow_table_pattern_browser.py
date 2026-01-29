from AnyQt import QtWidgets, QtCore
from AnyQt.QtCore import Qt
from Orange.widgets.widget import OWWidget, Input, Output, Msg
from orangewidget.settings import Setting
from orangewidget import gui

import pandas as pd
import sqlalchemy as sa
from sqlalchemy import text
from typing import Optional, List, Dict, Any

from Orange.data.pandas_compat import table_from_frame
from Orange.data import Table


# ========= Helper: model sederhana utk preview DataFrame =========
def df_to_qt_model(df: pd.DataFrame) -> QtCore.QAbstractTableModel:
    class _DFModel(QtCore.QAbstractTableModel):
        def __init__(self, df_: pd.DataFrame, parent=None):
            super().__init__(parent)
            self._df = df_.reset_index(drop=True)

        def rowCount(self, parent=QtCore.QModelIndex()):
            return 0 if parent.isValid() else len(self._df)

        def columnCount(self, parent=QtCore.QModelIndex()):
            return 0 if parent.isValid() else len(self._df.columns)

        def data(self, index, role=Qt.DisplayRole):
            if not index.isValid() or role not in (Qt.DisplayRole, Qt.EditRole):
                return None
            val = self._df.iat[index.row(), index.column()]
            return "" if pd.isna(val) else str(val)

        def headerData(self, section, orientation, role=Qt.DisplayRole):
            if role != Qt.DisplayRole:
                return None
            if orientation == Qt.Horizontal:
                try:
                    return str(self._df.columns[section])
                except Exception:
                    return str(section)
            return str(section + 1)

    return _DFModel(df)


class OWHTablePattern(OWWidget):
    name = "Query Table Pattern"
    id = "datahelpers-table-pattern"
    description = (
        "Menampilkan daftar tabel dari database dan membantu mendeteksi pola prefix/suffix "
        "berdasarkan 'strip' (bagian yang dipisah underscore)."
    )
    icon = "icons/table_pattern.png"
    priority = 13
    want_main_area = True

    class Inputs:
        Connection = Input("Connection", object, auto_summary=False)

    class Outputs:
        Data = Output("Data", Table, auto_summary=False)

    # ===== Settings: Pola suffix berbasis strip =====
    # 0 = dari Belakang, 1 = dari Depan
    take_from: int = Setting(0)
    start_strip: int = Setting(1)     # 1-based
    take_count: int = Setting(1)      # berapa strip diambil

    # Validasi digit
    validate_digits: bool = Setting(True)
    digits_only: bool = Setting(True)
    min_digits: int = Setting(6)
    max_digits: int = Setting(8)      # 0 berarti tidak dibatasi

    # Filter UI
    prefix_filter: str = Setting("")          # startswith BASE
    suffix_filter: str = Setting("")          # contains/endswith SUFFIX
    search_filter: str = Setting("")          # contains TABLE_NAME
    use_contains_for_suffix: bool = Setting(True)

    class Error(OWWidget.Error):
        no_connection = Msg("Belum ada koneksi.")
        load_failed = Msg("Gagal memuat tabel: {}")

    class Info(OWWidget.Information):
        conn = Msg("Terhubung ke database.")
        status = Msg("{}")

    def __init__(self):
        super().__init__()

        # ===== Control Area =====
        cbox = gui.widgetBox(self.controlArea, "Koneksi")
        self.lbl_conn = QtWidgets.QLabel("-")
        self.lbl_conn.setTextInteractionFlags(Qt.TextSelectableByMouse)
        cbox.layout().addWidget(self.lbl_conn)

        sbox = gui.widgetBox(self.controlArea, "Sumber Tabel")
        self.btn_refresh = gui.button(sbox, self, "Refresh", callback=self._refresh)

        pbox = gui.widgetBox(self.controlArea, "Penentuan Pola (Strip)")

        self.rb_take = gui.radioButtons(
            pbox, self, "take_from",
            btnLabels=["Belakang", "Depan"],
            orientation=Qt.Horizontal
        )
        for b in self.rb_take.buttons:
            b.clicked.connect(self._reparse_and_apply)

        # start strip + count
        row1 = gui.widgetBox(pbox, orientation=Qt.Horizontal)
        row1.layout().addWidget(QtWidgets.QLabel("Mulai dari strip ke:"))
        self.sp_start = QtWidgets.QSpinBox()
        self.sp_start.setMinimum(1)
        self.sp_start.setMaximum(50)
        self.sp_start.setValue(int(self.start_strip or 1))
        self.sp_start.valueChanged.connect(self._on_start_changed)
        row1.layout().addWidget(self.sp_start)

        row2 = gui.widgetBox(pbox, orientation=Qt.Horizontal)
        row2.layout().addWidget(QtWidgets.QLabel("Jumlah strip diambil:"))
        self.sp_count = QtWidgets.QSpinBox()
        self.sp_count.setMinimum(1)
        self.sp_count.setMaximum(10)
        self.sp_count.setValue(int(self.take_count or 1))
        self.sp_count.valueChanged.connect(self._on_count_changed)
        row2.layout().addWidget(self.sp_count)

        # Validasi digit
        vbox = gui.widgetBox(pbox, "Validasi Digit (Opsional)")
        gui.checkBox(vbox, self, "validate_digits", "Aktifkan validasi digit", callback=self._reparse_and_apply)
        gui.checkBox(vbox, self, "digits_only", "Strip suffix harus angka saja", callback=self._reparse_and_apply)

        row3 = gui.widgetBox(vbox, orientation=Qt.Horizontal)
        row3.layout().addWidget(QtWidgets.QLabel("Minimal digit:"))
        self.sp_min = QtWidgets.QSpinBox()
        self.sp_min.setMinimum(1)
        self.sp_min.setMaximum(20)
        self.sp_min.setValue(int(self.min_digits or 6))
        self.sp_min.valueChanged.connect(self._on_min_changed)
        row3.layout().addWidget(self.sp_min)

        row4 = gui.widgetBox(vbox, orientation=Qt.Horizontal)
        row4.layout().addWidget(QtWidgets.QLabel("Maksimal digit:"))
        self.sp_max = QtWidgets.QSpinBox()
        self.sp_max.setMinimum(0)   # 0 = unlimited
        self.sp_max.setMaximum(50)
        self.sp_max.setValue(int(self.max_digits or 8))
        self.sp_max.valueChanged.connect(self._on_max_changed)
        row4.layout().addWidget(self.sp_max)

        # ===== Filter =====
        flt = gui.widgetBox(self.controlArea, "Filter")
        gui.lineEdit(flt, self, "prefix_filter", "Prefix (startswith, BASE):", callback=self._apply_filters_and_emit)
        gui.lineEdit(flt, self, "suffix_filter", "Suffix filter:", callback=self._apply_filters_and_emit)
        gui.checkBox(
            flt, self, "use_contains_for_suffix",
            "Suffix pakai contains (bukan endswith)",
            callback=self._apply_filters_and_emit
        )
        gui.lineEdit(flt, self, "search_filter", "Search (contains, TABLE_NAME):", callback=self._apply_filters_and_emit)

        # ===== Ringkasan =====
        sumbox = gui.widgetBox(self.controlArea, "Ringkasan Pola")
        self.lbl_stats = QtWidgets.QLabel("-")
        self.lbl_stats.setWordWrap(True)
        sumbox.layout().addWidget(self.lbl_stats)

        # ===== Main Area =====
        self.view = QtWidgets.QTableView(self.mainArea)
        if self.mainArea.layout() is None:
            self.mainArea.setLayout(QtWidgets.QVBoxLayout())
        self.mainArea.layout().addWidget(self.view)

        # state
        self._engine: Optional[sa.Engine] = None
        self._raw_df: Optional[pd.DataFrame] = None

    # ===== input connection =====
    @Inputs.Connection
    def set_engine(self, engine: Optional[object]):
        self._engine = engine if isinstance(engine, sa.Engine) else None
        self.Error.clear(); self.Info.clear()

        if not self._engine:
            self.lbl_conn.setText("-")
            self.Error.no_connection()
            self._set_output(None)
            return

        try:
            url = self._engine.url
            host = getattr(url, "host", None) or "-"
            port = getattr(url, "port", None) or "-"
            dbnm = getattr(url, "database", None) or "-"
            info = f"{url.get_backend_name()} | {host}:{port} | DB: {dbnm}"
            self.lbl_conn.setText(info)
            self.Info.conn(info)
        except Exception:
            self.lbl_conn.setText("(koneksi aktif)")
            self.Info.conn("Koneksi aktif.")

        self._refresh()

    # ===== UI handlers =====
    def _on_start_changed(self, v: int):
        self.start_strip = int(v)
        self._reparse_and_apply()

    def _on_count_changed(self, v: int):
        self.take_count = int(v)
        self._reparse_and_apply()

    def _on_min_changed(self, v: int):
        self.min_digits = int(v)
        self._reparse_and_apply()

    def _on_max_changed(self, v: int):
        self.max_digits = int(v)
        self._reparse_and_apply()

    def _reparse_and_apply(self):
        # parsing ulang raw_df dari table_name list (lebih aman: refresh DF dari names yang sudah ada)
        # Jika _raw_df belum ada, cukup apply filter saja
        if self._raw_df is None or self._raw_df.empty:
            self._apply_filters_and_emit()
            return

        # kita simpan ulang dari TABLE_NAME
        names = self._raw_df["TABLE_NAME"].tolist() if "TABLE_NAME" in self._raw_df.columns else []
        df = self._build_df(names)
        self._raw_df = df
        self._apply_filters_and_emit()

    # ===== fetch table list (USER_TABLES only) =====
    def _fetch_table_names(self) -> List[str]:
        backend = ""
        try:
            backend = self._engine.url.get_backend_name().lower()
        except Exception:
            backend = ""

        if "oracle" in backend:
            with self._engine.connect() as con:
                rows = con.execute(text("SELECT TABLE_NAME FROM USER_TABLES")).fetchall()
                return [str(r[0]) for r in rows]

        # fallback non-oracle
        insp = sa.inspect(self._engine)
        return insp.get_table_names()

    def _refresh(self):
        self.Error.clear()
        self.Info.status("Memuat daftar tabel…")

        if not self._engine:
            self.Error.no_connection()
            return

        try:
            names = self._fetch_table_names()
            df = self._build_df(names)
            self._raw_df = df
            self.Info.status(f"Loaded {len(df)} tabel.")
            self._apply_filters_and_emit()
        except Exception as e:
            self.Error.load_failed(str(e))
            self._set_output(None)

    # ===== Parsing pola strip =====
    def _is_valid_suffix_parts(self, parts: List[str]) -> bool:
        """
        Validasi: setiap strip suffix harus memenuhi aturan digit (jika aktif).
        """
        if not self.validate_digits:
            return True

        min_d = int(self.min_digits or 1)
        max_d = int(self.max_digits or 0)  # 0 = unlimited

        for p in parts:
            if self.digits_only and not p.isdigit():
                return False
            ln = len(p)
            if ln < min_d:
                return False
            if max_d > 0 and ln > max_d:
                return False
        return True

    def _extract_suffix_by_strip(self, name_u: str) -> Dict[str, Any]:
        """
        Pecah table name jadi BASE & SUFFIX berdasarkan:
        - Depan/Belakang
        - start_strip (1-based)
        - take_count
        - validasi digit (opsional)
        """
        parts = [p for p in name_u.split("_") if p != ""]
        total = len(parts)

        start = int(self.start_strip or 1)
        count = int(self.take_count or 1)
        if start < 1:
            start = 1
        if count < 1:
            count = 1

        # jika parts terlalu sedikit → tidak bisa
        if total == 0 or total < (start + count - 1):
            return {
                "BASE": name_u,
                "SUFFIX": "",
                "HAS_PATTERN": False,
                "STRIP_TOTAL": total,
                "SUFFIX_STRIPS": 0,
                "SUFFIX_DIGITS_OK": False,
            }

        # hitung index berdasarkan depan/belakang
        if self.take_from == 1:
            # dari depan
            i0 = start - 1
            i1 = i0 + count  # exclusive
            suffix_parts = parts[i0:i1]
            base_parts = parts[:i0] + parts[i1:]
        else:
            # dari belakang
            end_excl = total - (start - 1)
            begin = end_excl - count
            if begin < 0:
                begin = 0
            suffix_parts = parts[begin:end_excl]
            base_parts = parts[:begin] 

        digits_ok = self._is_valid_suffix_parts(suffix_parts)

        if not digits_ok:
            # kalau validasi aktif dan gagal → anggap tidak terdeteksi
            return {
                "BASE": name_u,
                "SUFFIX": "",
                "HAS_PATTERN": False,
                "STRIP_TOTAL": total,
                "SUFFIX_STRIPS": len(suffix_parts),
                "SUFFIX_DIGITS_OK": False,
            }

        suffix = "_".join(suffix_parts)
        base = "_".join(base_parts) if base_parts else name_u

        if not base.strip():
            base = name_u

        return {
            "BASE": base,
            "SUFFIX": suffix,
            "HAS_PATTERN": True if suffix else False,
            "STRIP_TOTAL": total,
            "SUFFIX_STRIPS": len(suffix_parts),
            "SUFFIX_DIGITS_OK": True,
        }

    def _parse_table(self, name: str) -> Dict[str, Any]:
        nm_u = (name or "").strip().upper()
        parsed = self._extract_suffix_by_strip(nm_u)
        return {
            "TABLE_NAME": nm_u,
            "BASE": parsed["BASE"],
            "SUFFIX": parsed["SUFFIX"],
            "HAS_PATTERN": parsed["HAS_PATTERN"],
            "STRIP_TOTAL": parsed["STRIP_TOTAL"],
            "SUFFIX_STRIPS": parsed["SUFFIX_STRIPS"],
            "SUFFIX_DIGITS_OK": parsed["SUFFIX_DIGITS_OK"],
        }

    def _build_df(self, names: List[str]) -> pd.DataFrame:
        rows = [self._parse_table(n) for n in (names or [])]
        df = pd.DataFrame(rows)
        if df.empty:
            return df

        df["BASE_VARIANTS"] = df.groupby("BASE")["TABLE_NAME"].transform("count")
        return df.sort_values(["BASE", "TABLE_NAME"]).reset_index(drop=True)

    # ===== filtering + stats =====
    def _apply_filters_and_emit(self):
        if self._raw_df is None or self._raw_df.empty:
            self.view.setModel(None)
            if hasattr(self, "lbl_stats"):
                self.lbl_stats.setText("-")
            self._set_output(None)
            return

        df = self._raw_df.copy()

        pf = (self.prefix_filter or "").strip().upper()
        if pf:
            df = df[df["BASE"].str.startswith(pf, na=False)]

        sf = (self.suffix_filter or "").strip().upper()
        if sf:
            if self.use_contains_for_suffix:
                df = df[df["SUFFIX"].str.contains(sf, na=False)]
            else:
                df = df[df["SUFFIX"].str.endswith(sf, na=False)]

        q = (self.search_filter or "").strip().upper()
        if q:
            df = df[df["TABLE_NAME"].str.contains(q, na=False)]

        self._update_stats_label(df)

        self.view.setModel(df_to_qt_model(df))
        self._set_output(df)

    def _update_stats_label(self, df: pd.DataFrame):
        try:
            total = len(df)
            base_u = df["BASE"].nunique(dropna=True) if "BASE" in df.columns else 0
            has_pat = int(df["HAS_PATTERN"].sum()) if "HAS_PATTERN" in df.columns else 0

            # top suffix
            top = "-"
            if "SUFFIX" in df.columns:
                sfx = df[df["SUFFIX"].astype(str).str.len() > 0]
                if not sfx.empty:
                    vc = sfx["SUFFIX"].value_counts().head(5)
                    top = "\n".join([f"- {k}: {int(v)}" for k, v in vc.items()])

            take_from = "Belakang" if self.take_from == 0 else "Depan"
            maxd = int(self.max_digits or 0)
            maxd_txt = str(maxd) if maxd > 0 else "∞"

            if hasattr(self, "lbl_stats"):
                self.lbl_stats.setText(
                    f"Arah suffix: {take_from}\n"
                    f"Mulai strip ke: {int(self.start_strip)} | Jumlah strip: {int(self.take_count)}\n"
                    f"Validasi digit: {'ON' if self.validate_digits else 'OFF'}"
                    f" | digits-only: {'ON' if self.digits_only else 'OFF'}"
                    f" | digit: {int(self.min_digits)}..{maxd_txt}\n\n"
                    f"Tabel tampil: {total}\n"
                    f"Base unik: {base_u}\n"
                    f"Ter-detect pattern: {has_pat}\n\n"
                    f"Top suffix (freq):\n{top}"
                )
        except Exception:
            if hasattr(self, "lbl_stats"):
                self.lbl_stats.setText("-")

    def _set_output(self, df: Optional[pd.DataFrame]):
        if df is None or df.empty:
            self.Outputs.Data.send(None)
            return
        self.Outputs.Data.send(table_from_frame(df))
