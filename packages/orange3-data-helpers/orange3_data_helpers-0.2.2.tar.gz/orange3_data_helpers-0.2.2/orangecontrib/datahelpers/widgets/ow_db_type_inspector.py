from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, Optional, List, Tuple

import pandas as pd
import sqlalchemy as sa

from AnyQt import QtWidgets, QtCore
from AnyQt.QtCore import Qt

from orangewidget import gui
from orangewidget.settings import Setting
from Orange.widgets.widget import OWWidget, Input, Output, Msg
from Orange.data import Table


# -----------------------------
# Helpers
# -----------------------------

def unwrap_engine(conn_input: Any) -> Optional[sa.Engine]:
    if conn_input is None:
        return None
    if isinstance(conn_input, sa.Engine):
        return conn_input
    if isinstance(conn_input, dict) and isinstance(conn_input.get("engine"), sa.Engine):
        return conn_input["engine"]
    return None


def dialect_name(engine: Optional[sa.Engine]) -> str:
    if engine is None:
        return ""
    try:
        return (engine.dialect.name or "").lower()
    except Exception:
        return ""


def orange_table_to_df(data: Table) -> pd.DataFrame:
    if hasattr(data, "to_pandas_df"):
        return data.to_pandas_df()
    if hasattr(data, "to_pandas"):
        return data.to_pandas()
    from Orange.data.pandas_compat import table_to_frame
    return table_to_frame(data)


def is_datetime(s: pd.Series) -> bool:
    return pd.api.types.is_datetime64_any_dtype(s)


def is_bool(s: pd.Series) -> bool:
    return pd.api.types.is_bool_dtype(s)


def is_int(s: pd.Series) -> bool:
    return pd.api.types.is_integer_dtype(s)


def is_float(s: pd.Series) -> bool:
    return pd.api.types.is_float_dtype(s)


def series_null_count(s: pd.Series) -> int:
    try:
        return int(pd.isna(s).sum())
    except Exception:
        return 0


def safe_len(v: Any) -> int:
    if v is None:
        return 0
    try:
        return len(str(v))
    except Exception:
        return 0


def infer_string_max_len(s: pd.Series, sample_limit: int = 20000) -> int:
    # gunakan sample untuk cepat (tetap cukup akurat)
    try:
        ss = s.dropna()
        if len(ss) > sample_limit:
            ss = ss.sample(sample_limit, random_state=1)
        return int(ss.astype(str).map(len).max()) if len(ss) else 0
    except Exception:
        return 0


def infer_numeric_min_max(s: pd.Series) -> Tuple[Optional[float], Optional[float]]:
    try:
        ss = pd.to_numeric(s, errors="coerce")
        ss = ss.dropna()
        if len(ss) == 0:
            return None, None
        return float(ss.min()), float(ss.max())
    except Exception:
        return None, None


def infer_decimal_precision_scale(s: pd.Series, sample_limit: int = 20000) -> Tuple[Optional[int], Optional[int]]:
    """
    Deteksi precision/scale untuk DECIMAL/NUMERIC dari nilai numeric.
    precision = total digit (tanpa tanda & titik)
    scale = digit di belakang koma
    """
    try:
        ss = s.dropna()
        if len(ss) > sample_limit:
            ss = ss.sample(sample_limit, random_state=1)

        max_p = 0
        max_s = 0
        any_ok = False

        for v in ss:
            if v is None or (isinstance(v, float) and (math.isnan(v) or math.isinf(v))):
                continue
            try:
                d = Decimal(str(v))
            except (InvalidOperation, ValueError):
                continue

            # normalisasi: hilangkan exponent
            tup = d.as_tuple()
            digits = len(tup.digits)
            scale = max(0, -tup.exponent)
            # precision ~ digits (untuk 0 bisa 1)
            if digits == 0:
                digits = 1

            max_p = max(max_p, digits)
            max_s = max(max_s, scale)
            any_ok = True

        if not any_ok:
            return None, None

        # pastikan precision >= scale
        max_p = max(max_p, max_s)
        return int(max_p), int(max_s)
    except Exception:
        return None, None


def pick_sample_value(s: pd.Series) -> str:
    try:
        ss = s.dropna()
        if len(ss) == 0:
            return "-"
        v = ss.iloc[0]
        st = str(v)
        return st[:120] + ("…" if len(st) > 120 else "")
    except Exception:
        return "-"


# -----------------------------
# Dialect type suggestions
# -----------------------------

@dataclass
class ColProfile:
    name: str
    pandas_dtype: str
    nulls: int
    non_nulls: int
    max_len: int
    min_val: Optional[float]
    max_val: Optional[float]
    precision: Optional[int]
    scale: Optional[int]
    sample: str


def suggest_type_for_col(profile: ColProfile, target: str) -> str:
    """
    target: oracle | mssql | postgres | mysql | mariadb | clickhouse
    Return type string (SQL-ish) to be used in override JSON.
    """
    target = (target or "").lower()

    # ClickHouse: tentukan apakah kolom nullable
    # (kalau ada null, sebaiknya Nullable(Type) agar insert tidak error)
    def _wrap_nullable(ch_type: str) -> str:
        if profile.nulls and profile.nulls > 0:
            # hindari Nullable(Nullable(...))
            if ch_type.startswith("Nullable("):
                return ch_type
            return f"Nullable({ch_type})"
        return ch_type

    # helper: pilih int vs bigint
    def _int_type():
        # pakai min/max kalau ada
        if target == "clickhouse":
            # ClickHouse lebih eksplisit: Int32 / Int64
            if profile.min_val is None or profile.max_val is None:
                return _wrap_nullable("Int64")
            lo, hi = profile.min_val, profile.max_val
            if lo >= -2147483648 and hi <= 2147483647:
                return _wrap_nullable("Int32")
            return _wrap_nullable("Int64")

        if profile.min_val is None or profile.max_val is None:
            return "BIGINT" if target in ("mssql", "mysql", "mariadb", "postgres") else "NUMBER(19,0)"
        lo, hi = profile.min_val, profile.max_val
        if lo >= -2147483648 and hi <= 2147483647:
            if target == "oracle":
                return "NUMBER(10,0)"
            if target in ("mysql", "mariadb"):
                return "INT"
            return "INT"
        else:
            if target == "oracle":
                return "NUMBER(19,0)"
            return "BIGINT"

    # numeric decimal
    def _decimal_type():
        p = profile.precision or 18
        s = profile.scale or 0
        # batas aman
        p = max(1, min(38, int(p)))
        s = max(0, min(p, int(s)))

        if target == "clickhouse":
            # ClickHouse: Decimal(p,s)
            return _wrap_nullable(f"Decimal({p},{s})")

        if target == "oracle":
            return f"NUMBER({p},{s})"
        if target == "postgres":
            return f"NUMERIC({p},{s})"
        if target in ("mysql", "mariadb"):
            return f"DECIMAL({p},{s})"
        return f"NUMERIC({p},{s})"  # mssql

    # string
    def _string_type():
        L = int(profile.max_len or 0)

        if target == "clickhouse":
            # ClickHouse umumnya pakai String. Kalau ingin hemat, bisa FixedString(n)
            # Tapi FixedString ketat; default aman: String
            return _wrap_nullable("String")

        if target == "oracle":
            if L <= 0:
                return "VARCHAR2(255)"
            if L > 4000:
                return "CLOB"
            return f"VARCHAR2({min(max(L, 1), 4000)})"

        if target == "mssql":
            if L <= 0:
                return "NVARCHAR(255)"
            if L > 4000:
                return "NVARCHAR(MAX)"
            return f"NVARCHAR({min(max(L, 1), 4000)})"

        if target == "postgres":
            if L <= 0:
                return "TEXT"
            if L <= 1000:
                return f"VARCHAR({max(L, 1)})"
            return "TEXT"

        if target in ("mysql", "mariadb"):
            if L <= 0:
                return "VARCHAR(255)"
            if L <= 2000:
                return f"VARCHAR({max(L, 1)})"
            if L <= 65535:
                return "TEXT"
            return "LONGTEXT"

        return "TEXT"

    # datetime/date
    def _datetime_type():
        if target == "clickhouse":
            # ClickHouse: Date / DateTime
            # Kita pakai DateTime sebagai default (paling aman)
            return _wrap_nullable("DateTime")

        if target == "oracle":
            return "TIMESTAMP"
        if target == "mssql":
            return "DATETIME2"
        if target == "postgres":
            return "TIMESTAMP"
        if target in ("mysql", "mariadb"):
            return "DATETIME"
        return "TIMESTAMP"

    # boolean
    def _bool_type():
        if target == "clickhouse":
            # ClickHouse punya Bool di versi baru, tapi UInt8 lebih kompatibel
            return _wrap_nullable("UInt8")

        if target == "oracle":
            return "NUMBER(1,0)"
        if target == "mssql":
            return "BIT"
        if target == "postgres":
            return "BOOLEAN"
        if target in ("mysql", "mariadb"):
            return "TINYINT(1)"
        return "BOOLEAN"

    # float
    def _float_type():
        if target == "clickhouse":
            return _wrap_nullable("Float64")

        if target == "oracle":
            return "BINARY_DOUBLE"
        if target == "postgres":
            return "DOUBLE PRECISION"
        if target in ("mysql", "mariadb"):
            return "DOUBLE"
        return "FLOAT"

    # --- routing berdasarkan dtype pandas ---
    dt = (profile.pandas_dtype or "").lower()

    # datetime
    if "datetime" in dt:
        return _datetime_type()

    # bool
    if "bool" in dt:
        return _bool_type()

    # integer
    if "int" in dt and "datetime" not in dt:
        return _int_type()

    # float
    if "float" in dt:
        # default float; kalau presisi fixed => decimal (dari precision/scale)
        # jika precision terdeteksi, lebih baik decimal
        if profile.precision is not None and profile.scale is not None:
            return _decimal_type()
        return _float_type()

    # object/string fallback
    # jika precision/scale terdeteksi (kadang numeric terbaca object), gunakan decimal
    if profile.precision is not None:
        return _decimal_type()

    return _string_type()

def infer_profiles(df: pd.DataFrame) -> List[ColProfile]:
    profiles: List[ColProfile] = []
    for c in df.columns:
        s = df[c]
        nulls = series_null_count(s)
        non_nulls = int(len(s) - nulls)

        pd_dtype = str(s.dtype)

        max_len = 0
        min_v = None
        max_v = None
        prec = None
        scale = None

        if pd.api.types.is_object_dtype(s):
            # string len
            max_len = infer_string_max_len(s)
            # coba deteksi decimal dari object numeric-ish
            # jika banyak yang bisa dikonversi, ambil precision/scale
            ss_num = pd.to_numeric(s, errors="coerce")
            if int(ss_num.notna().sum()) > 0:
                prec, scale = infer_decimal_precision_scale(ss_num)
                min_v, max_v = infer_numeric_min_max(ss_num)

        elif is_int(s) or is_float(s):
            min_v, max_v = infer_numeric_min_max(s)
            # scale untuk float tidak dipaksa; tapi bisa deteksi jika perlu
            if is_float(s):
                prec, scale = infer_decimal_precision_scale(s)

        elif is_datetime(s):
            # tak perlu panjang
            pass
        elif is_bool(s):
            pass
        else:
            # fallback
            max_len = infer_string_max_len(s)

        sample = pick_sample_value(s)

        profiles.append(ColProfile(
            name=str(c),
            pandas_dtype=pd_dtype,
            nulls=nulls,
            non_nulls=non_nulls,
            max_len=int(max_len or 0),
            min_val=min_v,
            max_val=max_v,
            precision=prec,
            scale=scale,
            sample=sample
        ))
    return profiles


# -----------------------------
# Widget
# -----------------------------
TARGET_ITEMS = ["auto", "oracle", "mssql", "postgres", "mysql", "mariadb", "clickhouse"]

class OWDBTypeInspector(OWWidget):
    name = "Data Type Inspector"
    id = "datahelpers-db-type-inspector"
    description = "Baca profil kolom (panjang string, range numeric) dan generate JSON override tipe data sesuai DB tujuan."
    icon = "icons/db_query.png"  # ganti icon jika ada
    priority = 1199
    want_main_area = True

    class Inputs:
        Data = Input("Data", Table)
        Connection = Input("Connection", object, auto_summary=False)

    class Outputs:
        TypeJSON = Output("Type JSON", str, auto_summary=False)
        Report = Output("Report", dict, auto_summary=False)

    class Error(OWWidget.Error):
        missing_data = Msg("Input Data belum ada.")
        failed = Msg("Gagal membaca tipe: {}")

    # target dialect pilihan user (default ikut connection kalau ada)
    target_db: int = Setting(0)   # 0=auto, 1=oracle, 2=mssql, 3=postgres, 4=mysql, 5=mariadb
    json_only_changed: bool = Setting(False)

    def __init__(self):
        super().__init__()
        # migrasi setting lama (jika pernah tersimpan string)
        if isinstance(self.target_db, str):
            s = self.target_db.strip().lower()
            if s in TARGET_ITEMS:
                self.target_db = TARGET_ITEMS.index(s)
            else:
                self.target_db = 0

        self._data: Optional[Table] = None
        self._engine: Optional[sa.Engine] = None
        self._profiles: List[ColProfile] = []
        self._suggested: Dict[str, str] = {}
        self._overrides: Dict[str, str] = {}

        # ===== Controls =====
        box = gui.widgetBox(self.controlArea, "Target", spacing=6)

        self.cmb_target = gui.comboBox(
            box, self, "target_db",
            label="DB tujuan:",
            items=TARGET_ITEMS,
            orientation=Qt.Horizontal,
            callback=self._refresh_suggestions
        )


        gui.checkBox(
            box, self, "json_only_changed",
            "JSON hanya kolom yang diubah (override saja)",
            callback=self._emit_json
        )

        btn_box = gui.widgetBox(self.controlArea, "Aksi", spacing=6)
        self.btn_scan = gui.button(btn_box, self, "Scan / Refresh", callback=self._scan)
        self.btn_apply_suggest = gui.button(btn_box, self, "Pakai semua rekomendasi", callback=self._apply_all_suggestions)
        self.btn_generate = gui.button(btn_box, self, "Generate JSON", callback=self._emit_json)

        # ===== JSON editor =====
        jbox = gui.widgetBox(self.controlArea, "Override JSON", spacing=6)
        self.json_edit = QtWidgets.QPlainTextEdit()
        self.json_edit.setPlaceholderText('{"nama_kolom":"NVARCHAR(MAX)","tgl":"DATE","nilai":"NUMERIC(18,2)"}')
        self.json_edit.setMinimumHeight(140)
        jbox.layout().addWidget(self.json_edit)

        # ===== Main area table =====
        self.table = QtWidgets.QTableWidget(self.mainArea)
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels([
            "Kolom", "pandas dtype", "Null", "Non-null",
            "MaxLen", "Min", "Max", "Prec", "Scale",
            "Tipe (edit)"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.mainArea.layout().addWidget(self.table)

        self.table.itemChanged.connect(self._on_item_changed)

    # -------- Inputs --------
    @Inputs.Data
    def set_data(self, data: Optional[Table]):
        self._data = data
        self._scan()

    @Inputs.Connection
    def set_connection(self, conn: Any):
        self._engine = unwrap_engine(conn)
        # kalau user pilih auto, sesuaikan dari connection
        if self.target_db == 0:
            self._refresh_suggestions()

    # -------- Core --------
    def _resolve_target(self) -> str:
        # kompatibel: bisa int (index) atau string ("oracle")
        v = getattr(self, "target_db", 0)

        if isinstance(v, int):
            try:
                choice = TARGET_ITEMS[v]
            except Exception:
                choice = "auto"
        else:
            choice = str(v).strip().lower() or "auto"

        if choice != "auto":
            return choice

        d = dialect_name(self._engine)

        # ---- ClickHouse detection (penting) ----
        # Bisa muncul sebagai: clickhouse, clickhouse+native, clickhouse+http, clickhouse_connect, dll
        if "clickhouse" in d:
            return "clickhouse"

        if "mssql" in d:
            return "mssql"
        if d in ("postgresql", "postgres"):
            return "postgres"
        if d == "oracle":
            return "oracle"
        if d in ("mysql",):
            return "mysql"
        if d in ("mariadb",):
            return "mariadb"

        return "postgres"


    def _scan(self):
        self.Error.clear()
        self._profiles = []
        self._suggested = {}
        self._overrides = {}

        if self._data is None:
            self.table.setRowCount(0)
            self.Error.missing_data()
            self.Outputs.TypeJSON.send("")
            self.Outputs.Report.send({"ok": False, "error": "missing data"})
            return

        try:
            df = orange_table_to_df(self._data)
            df.columns = [str(c) for c in df.columns]

            self._profiles = infer_profiles(df)
            self._refresh_suggestions()
            self._render_table()
            self._emit_json()

        except Exception as e:
            self.table.setRowCount(0)
            self.Error.failed(str(e))
            self.Outputs.TypeJSON.send("")
            self.Outputs.Report.send({"ok": False, "error": str(e)})

    def _refresh_suggestions(self):
        if not self._profiles:
            return
        tgt = self._resolve_target()
        self._suggested = {p.name: suggest_type_for_col(p, tgt) for p in self._profiles}

        # jika belum ada override manual, gunakan suggestion sebagai default di kolom "Tipe (edit)"
        # tapi user bisa edit per baris
        if not self._overrides:
            self._overrides = dict(self._suggested)

        self._render_table()
        self._emit_json()

    def _apply_all_suggestions(self):
        self._overrides = dict(self._suggested)
        self._render_table()
        self._emit_json()

    def _render_table(self):
        if not self._profiles:
            self.table.setRowCount(0)
            return

        self.table.blockSignals(True)
        self.table.setRowCount(len(self._profiles))

        for r, p in enumerate(self._profiles):
            def _set(col: int, text: str):
                item = QtWidgets.QTableWidgetItem(text)
                # readonly kecuali kolom tipe
                if col != 9:
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(r, col, item)

            _set(0, p.name)
            _set(1, p.pandas_dtype)
            _set(2, str(p.nulls))
            _set(3, str(p.non_nulls))
            _set(4, str(p.max_len))
            _set(5, "-" if p.min_val is None else str(p.min_val))
            _set(6, "-" if p.max_val is None else str(p.max_val))
            _set(7, "-" if p.precision is None else str(p.precision))
            _set(8, "-" if p.scale is None else str(p.scale))

            # editable type
            t = self._overrides.get(p.name) or self._suggested.get(p.name) or "TEXT"
            _set(9, t)

            # tooltip sample
            self.table.item(r, 0).setToolTip(f"Sample: {p.sample}")
            self.table.item(r, 9).setToolTip("Edit tipe di sini (mis: NUMERIC(18,2), DATE, NVARCHAR(MAX), VARCHAR2(4000), CLOB)")

        self.table.blockSignals(False)

    def _on_item_changed(self, item: QtWidgets.QTableWidgetItem):
        # kolom tipe (index 9)
        if item.column() != 9:
            return
        row = item.row()
        colname_item = self.table.item(row, 0)
        if not colname_item:
            return
        colname = colname_item.text()
        self._overrides[colname] = (item.text() or "").strip()
        self._emit_json()

    def _emit_json(self):
        if not self._profiles:
            self.json_edit.setPlainText("")
            self.Outputs.TypeJSON.send("")
            self.Outputs.Report.send({"ok": False, "error": "no profiles"})
            return

        # JSON bisa all columns atau hanya yang beda dari suggestion
        out: Dict[str, str] = {}
        for p in self._profiles:
            col = p.name
            chosen = (self._overrides.get(col) or "").strip()
            sug = (self._suggested.get(col) or "").strip()

            if not chosen:
                chosen = sug or "TEXT"

            if self.json_only_changed:
                if chosen and sug and chosen != sug:
                    out[col] = chosen
            else:
                out[col] = chosen

        txt = json.dumps(out, ensure_ascii=False, indent=2)
        # update editor tanpa bikin loop itemChanged
        self.json_edit.blockSignals(True)
        self.json_edit.setPlainText(txt)
        self.json_edit.blockSignals(False)

        self.Outputs.TypeJSON.send(txt)
        self.Outputs.Report.send({
            "ok": True,
            "target_db": self._resolve_target(),
            "columns": len(self._profiles),
            "json_only_changed": bool(self.json_only_changed),
            "mapping": out
        })
