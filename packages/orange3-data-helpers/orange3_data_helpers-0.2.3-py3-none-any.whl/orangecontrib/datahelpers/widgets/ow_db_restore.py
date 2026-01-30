# orangecontrib/datahelpers/widgets/ow_db_restore.py
from __future__ import annotations

import io
import json
import re
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple, List

import pandas as pd
import sqlalchemy as sa

from AnyQt.QtCore import QObject, QThread, pyqtSignal, pyqtSlot, QTimer
from AnyQt import QtWidgets, QtCore

from orangewidget import gui
from orangewidget.settings import Setting
from Orange.widgets.widget import OWWidget, Input, Output, Msg
from Orange.data import Table


# -----------------------------
# Helpers
# -----------------------------

from Orange.data import Table as OrangeTable

def unwrap_engine(conn_input: Any):
    """
    Terima:
      - SQLAlchemy Engine
      - dict {"engine": Engine}
      - object yang punya attribute .engine (wrapper)
    """
    if conn_input is None:
        raise ValueError("DB Connection kosong.")

    # 1) Proteksi: kalau yang masuk ternyata Data/Table
    if isinstance(conn_input, OrangeTable):
        raise TypeError(
            "Input 'Connection' menerima Orange Table (Data), bukan DB Engine. "
            "Periksa wiring di Canvas: sambungkan output 'Connection' dari widget DB Connections "
            "ke input 'Connection' widget Restore Database (jangan output 'Data')."
        )

    # 2) Kalau wrapper object punya .engine
    if hasattr(conn_input, "engine"):
        try:
            eng = getattr(conn_input, "engine")
            if eng is not None:
                return unwrap_engine(eng)  # recursive sampai ketemu Engine beneran
        except Exception:
            pass

    # 3) SQLAlchemy Engine langsung
    try:
        from sqlalchemy.engine import Engine
        if isinstance(conn_input, Engine):
            return conn_input
    except Exception:
        # duck-typing
        if hasattr(conn_input, "connect") and hasattr(conn_input, "dialect"):
            return conn_input

    # 4) dict {"engine": Engine}
    if isinstance(conn_input, dict):
        eng = conn_input.get("engine")
        if eng is None:
            raise TypeError("dict Connection tidak punya key 'engine'.")
        return unwrap_engine(eng)

    raise TypeError(
        "Format DB Connection tidak dikenali. Harus SQLAlchemy Engine, dict {'engine': Engine}, "
        "atau object wrapper yang punya attribute .engine."
    )

def dialect_name(engine) -> str:
    try:
        return (engine.dialect.name or "").lower()
    except Exception:
        return ""


def default_schema_for_engine(engine) -> Optional[str]:
    """
    MSSQL: default dbo
    Postgres: biarkan None (default search_path)
    ClickHouse: schema=database bisa diisi dari UI, default None
    """
    d = dialect_name(engine)
    if "mssql" in d:
        return "dbo"
    return None


def target_fullname(schema: Optional[str], table: str) -> str:
    t = (table or "").strip()
    s = (schema or "").strip()
    return f"{s}.{t}" if s else t


def sanitize_columns(cols: List[str]) -> List[str]:
    seen: Dict[str, int] = {}
    out: List[str] = []
    for c in cols:
        c0 = (c or "").strip().lower()
        c0 = re.sub(r"[^a-z0-9_]+", "_", c0)
        c0 = re.sub(r"_+", "_", c0).strip("_")
        if not c0:
            c0 = "col"
        if c0[0].isdigit():
            c0 = f"col_{c0}"

        base = c0
        k = seen.get(base, 0) + 1
        seen[base] = k
        if k > 1:
            c0 = f"{base}_{k}"
        out.append(c0)
    return out

TABLE_PREFIX = "ODM_"
TABLE_NAME_MAXLEN = 50

def sanitize_table_suffix(raw: str) -> str:
    """
    - Tidak boleh spasi/titik/karakter aneh -> jadi underscore
    - Hanya boleh: a-z A-Z 0-9 _
    - Tidak boleh mulai dengan angka
    - Trim underscore berlebih
    """
    s = (raw or "").strip()

    # ganti spasi, titik, dan karakter non [a-zA-Z0-9_] jadi _
    s = re.sub(r"[^a-zA-Z0-9_]+", "_", s)

    # rapikan underscore
    s = re.sub(r"_+", "_", s).strip("_")

    if not s:
        s = "table"

    # tidak boleh mulai digit
    if s[0].isdigit():
        s = f"t_{s}"

    return s


def build_final_table_name(user_suffix: str) -> str:
    """
    - Prefix ODM_
    - Nama tabel lowercase semua
    - Karakter ilegal -> _
    - Maksimal 50 karakter (TOTAL)
    """
    suffix = sanitize_table_suffix(user_suffix)

    # gabungkan prefix
    name = f"{TABLE_PREFIX}{suffix}"

    # lowercase SEMUA (ini poin penting)
    name = name.lower()

    # batasi panjang total
    if len(name) > TABLE_NAME_MAXLEN:
        name = name[:TABLE_NAME_MAXLEN].rstrip("_")

    return name



def orange_table_to_df(data: Table) -> pd.DataFrame:
    if hasattr(data, "to_pandas_df"):
        return data.to_pandas_df()
    if hasattr(data, "to_pandas"):
        return data.to_pandas()
    from Orange.data.pandas_compat import table_to_frame
    return table_to_frame(data)


def normalize_df_for_db(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out.columns = [str(c) for c in out.columns]

    if len(set(out.columns)) != len(out.columns):
        out.columns = sanitize_columns(out.columns)

    # timezone-aware datetime -> naive
    for c in out.columns:
        if pd.api.types.is_datetime64_any_dtype(out[c]):
            try:
                if getattr(out[c].dt, "tz", None) is not None:
                    out[c] = out[c].dt.tz_convert(None)
            except Exception:
                pass

    def _is_na(v: Any) -> bool:
        try:
            return pd.isna(v)
        except Exception:
            return False

    for c in out.columns:
        if out[c].dtype == "object":
            def _norm(v: Any) -> Any:
                if v is None or _is_na(v):
                    return None
                if isinstance(v, (dict, list, tuple, set)):
                    try:
                        return json.dumps(v, ensure_ascii=False)
                    except Exception:
                        return str(v)
                return v
            out[c] = out[c].map(_norm)

    return out


# -----------------------------
# ClickHouse type support
# -----------------------------

def _try_import_clickhouse_types():
    """
    clickhouse-sqlalchemy menyediakan:
      from clickhouse_sqlalchemy import types as ch_types
    Jika tidak ada, return None.
    """
    try:
        from clickhouse_sqlalchemy import types as ch_types  # type: ignore
        return ch_types
    except Exception:
        return None


def _is_clickhouse(engine) -> bool:
    return "clickhouse" in dialect_name(engine)


def parse_type(type_str: str) -> sa.types.TypeEngine:
    """
    Parse string tipe ke SQLAlchemy type.
    Sekarang mendukung:
    - SQL Server / Postgres / Oracle common (lama)
    - ClickHouse common (jika clickhouse_sqlalchemy tersedia)
    """
    t = (type_str or "").strip()
    if not t:
        return sa.Text()

    t_up = t.upper().strip()

    # ---------- ClickHouse parsing (best-effort) ----------
    # Kita parse berdasar string, dan jika clickhouse_sqlalchemy ada, pakai type aslinya.
    ch_types = _try_import_clickhouse_types()
    if ch_types is not None:
        # Nullable(T)
        m = re.match(r"^NULLABLE\((.+)\)$", t_up)
        if m:
            inner = m.group(1).strip()
            inner_tp = parse_type(inner)
            try:
                return ch_types.Nullable(inner_tp)
            except Exception:
                return inner_tp

        # FixedString(N)
        m = re.match(r"^FIXEDSTRING\((\d+)\)$", t_up)
        if m:
            try:
                return ch_types.FixedString(int(m.group(1)))
            except Exception:
                return sa.String(int(m.group(1)))

        # Decimal(P,S)
        m = re.match(r"^DECIMAL\((\d+),\s*(\d+)\)$", t_up)
        if m:
            try:
                return ch_types.Decimal(int(m.group(1)), int(m.group(2)))
            except Exception:
                return sa.Numeric(int(m.group(1)), int(m.group(2)))

        # Date / DateTime
        if t_up in ("DATE",):
            try:
                return ch_types.Date()
            except Exception:
                return sa.Date()

        if t_up in ("DATETIME", "DATETIME64", "TIMESTAMP"):
            try:
                # DateTime64 mungkin butuh params, kita fallback DateTime
                return ch_types.DateTime()
            except Exception:
                return sa.DateTime()

        # String
        if t_up in ("STRING",):
            try:
                return ch_types.String()
            except Exception:
                return sa.Text()

        # Integers
        if t_up in ("INT8", "INT16", "INT32", "INT64"):
            try:
                return getattr(ch_types, t_up.title())()  # Int8/Int16/Int32/Int64
            except Exception:
                return sa.BigInteger()

        if t_up in ("UINT8", "UINT16", "UINT32", "UINT64"):
            try:
                # UInt8/UInt16/...
                return getattr(ch_types, "U" + t_up[1:].title())()
            except Exception:
                return sa.BigInteger()

        # Float
        if t_up in ("FLOAT32", "FLOAT64"):
            try:
                return getattr(ch_types, t_up.title())()
            except Exception:
                return sa.Float()

        # Bool
        if t_up in ("BOOL", "BOOLEAN"):
            try:
                return ch_types.UInt8()  # ClickHouse umumnya represent boolean sebagai UInt8
            except Exception:
                return sa.Boolean()

        # UUID
        if t_up == "UUID":
            try:
                return ch_types.UUID()
            except Exception:
                return sa.Text()

        # Jika user menulis "NUMERIC(18,2)" untuk ClickHouse, map ke Decimal
        m = re.match(r"^NUMERIC\((\d+),(\d+)\)$", t_up)
        if m:
            try:
                return ch_types.Decimal(int(m.group(1)), int(m.group(2)))
            except Exception:
                return sa.Numeric(int(m.group(1)), int(m.group(2)))

    # ---------- Generic / existing parsing (lama) ----------
    t = t_up

    if t in ("NVARCHAR(MAX)", "NVARCHARMAX"):
        return sa.UnicodeText()
    if t in ("VARCHAR(MAX)", "VARCHARMAX"):
        return sa.Text()

    if t == "TEXT":
        return sa.Text()
    if t == "NTEXT":
        return sa.UnicodeText()

    if t == "DATE":
        return sa.Date()
    if t in ("DATETIME", "TIMESTAMP", "DATETIME2"):
        return sa.DateTime()

    if t in ("BOOLEAN", "BOOL"):
        return sa.Boolean()
    if t == "BIT":
        return sa.Boolean()

    if t in ("INT", "INTEGER"):
        return sa.Integer()
    if t == "BIGINT":
        return sa.BigInteger()
    if t in ("FLOAT", "DOUBLE", "DOUBLE PRECISION"):
        return sa.Float()

    # Oracle common
    if t == "CLOB":
        return sa.Text()

    m = re.match(r"^VARCHAR2\((\d+)\)$", t)
    if m:
        return sa.String(int(m.group(1)))

    m = re.match(r"^VARCHAR\((\d+)\)$", t)
    if m:
        return sa.String(int(m.group(1)))

    m = re.match(r"^NVARCHAR\((\d+)\)$", t)
    if m:
        return sa.Unicode(int(m.group(1)))

    m = re.match(r"^NUMBER\((\d+),(\d+)\)$", t)
    if m:
        return sa.Numeric(int(m.group(1)), int(m.group(2)))

    m = re.match(r"^NUMERIC\((\d+),(\d+)\)$", t)
    if m:
        return sa.Numeric(int(m.group(1)), int(m.group(2)))

    m = re.match(r"^DECIMAL\((\d+),(\d+)\)$", t)
    if m:
        return sa.Numeric(int(m.group(1)), int(m.group(2)))

    return sa.Text()


def default_sqlalchemy_dtype_map(df: pd.DataFrame) -> Dict[str, sa.types.TypeEngine]:
    m: Dict[str, sa.types.TypeEngine] = {}
    for col in df.columns:
        s = df[col]
        if pd.api.types.is_integer_dtype(s):
            m[col] = sa.BigInteger()
        elif pd.api.types.is_float_dtype(s):
            m[col] = sa.Float()
        elif pd.api.types.is_bool_dtype(s):
            m[col] = sa.Boolean()
        elif pd.api.types.is_datetime64_any_dtype(s):
            m[col] = sa.DateTime()
        else:
            m[col] = sa.Text()
    return m


def default_clickhouse_dtype_map(df: pd.DataFrame) -> Dict[str, sa.types.TypeEngine]:
    """
    Default mapping untuk ClickHouse (kalau clickhouse_sqlalchemy tersedia).
    Kalau tidak tersedia, fallback ke default_sqlalchemy_dtype_map.
    """
    ch_types = _try_import_clickhouse_types()
    if ch_types is None:
        return default_sqlalchemy_dtype_map(df)

    m: Dict[str, sa.types.TypeEngine] = {}
    for col in df.columns:
        s = df[col]
        if pd.api.types.is_integer_dtype(s):
            # aman: Int64
            m[col] = ch_types.Int64()
        elif pd.api.types.is_float_dtype(s):
            m[col] = ch_types.Float64()
        elif pd.api.types.is_bool_dtype(s):
            # ClickHouse boolean sering UInt8
            m[col] = ch_types.UInt8()
        elif pd.api.types.is_datetime64_any_dtype(s):
            m[col] = ch_types.DateTime()
        else:
            m[col] = ch_types.String()
    return m


def merge_dtype_overrides(
    base: Dict[str, sa.types.TypeEngine],
    overrides_json: str
) -> Tuple[Dict[str, sa.types.TypeEngine], Dict[str, str]]:
    overrides_json = (overrides_json or "").strip()
    if not overrides_json:
        return base, {}

    try:
        obj = json.loads(overrides_json)
        if not isinstance(obj, dict):
            raise ValueError("Override JSON harus object/dict.")
    except Exception as e:
        raise ValueError(
            f"Override JSON tidak valid: {e}. "
            r'Contoh: {"nilai_kontrak":"NUMERIC(18,2)","tgl_sp2d":"DATE"}'
        )

    merged = dict(base)
    readable: Dict[str, str] = {}
    for k, v in obj.items():
        if isinstance(k, str) and isinstance(v, str):
            kk = k.strip()
            vv = v.strip()
            if kk:
                merged[kk] = parse_type(vv)
                readable[kk] = vv
    return merged, readable


def remap_overrides_keys(overrides_json: str, col_map: Dict[str, str]) -> str:
    overrides_json = (overrides_json or "").strip()
    if not overrides_json:
        return ""

    obj = json.loads(overrides_json)
    if not isinstance(obj, dict):
        raise ValueError("Override JSON harus object/dict.")

    remapped: Dict[str, Any] = {}
    for k, v in obj.items():
        if not isinstance(k, str) or not isinstance(v, str):
            continue
        kk = k.strip()
        if kk in col_map:
            kk2 = col_map[kk]
        else:
            kk2 = sanitize_columns([kk])[0]
        remapped[kk2] = v.strip()

    return json.dumps(remapped, ensure_ascii=False)


def parse_override_json(overrides_json: str) -> Dict[str, str]:
    s = (overrides_json or "").strip()
    if not s:
        return {}
    obj = json.loads(s)
    if not isinstance(obj, dict):
        raise ValueError("Override JSON harus object/dict.")
    out: Dict[str, str] = {}
    for k, v in obj.items():
        if isinstance(k, str) and isinstance(v, str):
            out[k.strip()] = v.strip()
    return out


def pythonize_records(df: pd.DataFrame) -> List[Dict[str, Any]]:
    cdf = df.where(pd.notna(df), None)
    records: List[Dict[str, Any]] = []
    for row in cdf.to_dict(orient="records"):
        r2 = {}
        for k, v in row.items():
            if hasattr(v, "item"):
                try:
                    v = v.item()
                except Exception:
                    pass
            r2[k] = v
        records.append(r2)
    return records


# -----------------------------
# Insert Strategies
# -----------------------------

class InsertStrategy:
    def insert(
        self,
        df: pd.DataFrame,
        engine,
        table: str,
        schema: Optional[str],
        if_exists: str,
        chunksize: int,
        dtype_map: Dict[str, sa.types.TypeEngine],
        index: bool,
        status_cb,
        progress_cb,
        cancel_cb,
    ) -> int:
        raise NotImplementedError


class MSSQLCoreStrategy(InsertStrategy):
    def _enable_fast_executemany(self, engine) -> None:
        try:
            from sqlalchemy import event

            @event.listens_for(engine, "before_cursor_execute")
            def _fast_exec(conn, cursor, statement, parameters, context, executemany):
                if executemany:
                    try:
                        cursor.fast_executemany = True
                    except Exception:
                        pass
        except Exception:
            pass

    def _build_table(self, metadata: sa.MetaData, table: str, schema: Optional[str],
                     dtype_map: Dict[str, sa.types.TypeEngine]) -> sa.Table:
        cols = [sa.Column(name, tp) for name, tp in dtype_map.items()]
        return sa.Table(table, metadata, *cols, schema=schema)

    def insert(self, df, engine, table, schema, if_exists, chunksize, dtype_map, index,
               status_cb, progress_cb, cancel_cb) -> int:
        self._enable_fast_executemany(engine)

        total = len(df)
        if total == 0:
            return 0

        chunk = max(1, int(chunksize))
        n = (total + chunk - 1) // chunk
        inserted = 0

        meta = sa.MetaData()
        insp = sa.inspect(engine)
        has_tbl = insp.has_table(table_name=table, schema=schema)

        if if_exists == "fail" and has_tbl:
            raise ValueError(f"Tabel {target_fullname(schema, table)} sudah ada (if_exists=fail).")

        with engine.begin() as conn:
            if if_exists == "replace" and has_tbl:
                status_cb(f"Dropping table {target_fullname(schema, table)}…")
                t = sa.Table(table, meta, schema=schema)
                t.drop(conn, checkfirst=True)
                has_tbl = False

            if not has_tbl:
                status_cb(f"Creating table {target_fullname(schema, table)}…")
                meta2 = sa.MetaData()
                tcreate = self._build_table(meta2, table, schema, dtype_map)
                tcreate.create(conn, checkfirst=False)

        meta3 = sa.MetaData()
        t_ins = sa.Table(table, meta3, schema=schema, autoload_with=engine)

        for i in range(n):
            if cancel_cb():
                break
            start = i * chunk
            end = min((i + 1) * chunk, total)
            cdf = df.iloc[start:end]

            status_cb(f"MSSQL insert chunk {i+1}/{n} rows {start+1}-{end}")
            records = pythonize_records(cdf)

            with engine.begin() as conn:
                conn.execute(t_ins.insert(), records)

            inserted += len(records)
            pct = int((inserted / total) * 100)
            progress_cb(min(100, max(0, pct)))

        return inserted


class ClickHouseCoreStrategy(InsertStrategy):
    """
    ClickHouse strategy yang robust lintas dialect:
    - CREATE TABLE pakai SQL mentah, karena ClickHouse butuh ENGINE.
    - INSERT chunked pakai INSERT INTO ... VALUES via sa.text() (executemany).
    - Tidak bergantung pada clickhouse_sqlalchemy.engines.MergeTree.
    """

    def _ch_type_sql(self, tp: sa.types.TypeEngine) -> str:
        """
        Konversi SQLAlchemy type -> ClickHouse SQL type string.
        (Best-effort; override JSON tetap disarankan untuk akurasi.)
        """
        # Numeric(precision, scale) -> Decimal(p,s)
        if isinstance(tp, sa.Numeric):
            p = getattr(tp, "precision", None) or 18
            s = getattr(tp, "scale", None) or 2
            return f"Decimal({int(p)},{int(s)})"

        # Integer types
        if isinstance(tp, (sa.BigInteger,)):
            return "Int64"
        if isinstance(tp, (sa.Integer, sa.SmallInteger)):
            return "Int32"

        # Float
        if isinstance(tp, (sa.Float,)):
            return "Float64"

        # Bool
        if isinstance(tp, (sa.Boolean,)):
            return "UInt8"

        # Date / DateTime
        if isinstance(tp, (sa.Date,)):
            return "Date"
        if isinstance(tp, (sa.DateTime,)):
            return "DateTime"

        # Text / String
        if isinstance(tp, (sa.Text, sa.UnicodeText)):
            return "String"
        if isinstance(tp, (sa.String, sa.Unicode)):
            return "String"

        # Fallback
        return "String"

    def _full_table_name(self, schema: Optional[str], table: str) -> str:
        """
        schema di ClickHouse dianggap database. Kita quote dengan backtick.
        """
        t = (table or "").strip()
        s = (schema or "").strip()
        if s:
            return f"`{s}`.`{t}`"
        return f"`{t}`"

    def _create_table_sql(
        self,
        schema: Optional[str],
        table: str,
        dtype_map: Dict[str, sa.types.TypeEngine],
        engine_sql: str = "MergeTree ORDER BY tuple()",
        if_not_exists: bool = True,
    ) -> str:
        full = self._full_table_name(schema, table)
        ine = "IF NOT EXISTS " if if_not_exists else ""

        col_defs = []
        for col, tp in dtype_map.items():
            colname = f"`{col}`"
            coltype = self._ch_type_sql(tp)
            col_defs.append(f"{colname} {coltype}")

        cols_sql = ", ".join(col_defs)
        return f"CREATE TABLE {ine}{full} ({cols_sql}) ENGINE = {engine_sql}"

    def _drop_table_sql(self, schema: Optional[str], table: str) -> str:
        full = self._full_table_name(schema, table)
        return f"DROP TABLE IF EXISTS {full}"

    def _insert_sql(self, schema: Optional[str], table: str, cols: List[str]) -> str:
        full = self._full_table_name(schema, table)
        col_list = ", ".join([f"`{c}`" for c in cols])
        # Named parameters -> sa.text() + list of dict records
        val_list = ", ".join([f":{c}" for c in cols])
        return f"INSERT INTO {full} ({col_list}) VALUES ({val_list})"

    def insert(
        self,
        df: pd.DataFrame,
        engine,
        table: str,
        schema: Optional[str],
        if_exists: str,
        chunksize: int,
        dtype_map: Dict[str, sa.types.TypeEngine],
        index: bool,
        status_cb,
        progress_cb,
        cancel_cb,
    ) -> int:
        total = len(df)
        if total == 0:
            return 0

        chunk = max(1, int(chunksize))
        n = (total + chunk - 1) // chunk
        inserted = 0

        # ClickHouse engine clause default (aman & persisten)
        # Kalau Anda mau bisa dijadikan setting UI nanti.
        engine_sql = "MergeTree ORDER BY tuple()"

        # --- create/drop table ---
        with engine.begin() as conn:
            if if_exists == "replace":
                status_cb(f"Dropping table {target_fullname(schema, table)}…")
                conn.exec_driver_sql(self._drop_table_sql(schema, table))

                status_cb(f"Creating table {target_fullname(schema, table)} (ENGINE={engine_sql})…")
                sql_create = self._create_table_sql(schema, table, dtype_map, engine_sql=engine_sql, if_not_exists=False)
                conn.exec_driver_sql(sql_create)

            elif if_exists == "fail":
                # Cek eksistensi via SHOW TABLES (lebih kompatibel ClickHouse)
                # Jika schema kosong, pakai currentDatabase()
                if schema and schema.strip():
                    chk_sql = "EXISTS TABLE " + self._full_table_name(schema, table)
                else:
                    chk_sql = "EXISTS TABLE " + self._full_table_name(None, table)
                exists = conn.exec_driver_sql(chk_sql).scalar()
                if int(exists or 0) == 1:
                    raise ValueError(f"Tabel {target_fullname(schema, table)} sudah ada (if_exists=fail).")

                status_cb(f"Creating table {target_fullname(schema, table)} (ENGINE={engine_sql})…")
                sql_create = self._create_table_sql(schema, table, dtype_map, engine_sql=engine_sql, if_not_exists=False)
                conn.exec_driver_sql(sql_create)

            else:  # append
                status_cb(f"Ensuring table {target_fullname(schema, table)} exists (ENGINE={engine_sql})…")
                sql_create = self._create_table_sql(schema, table, dtype_map, engine_sql=engine_sql, if_not_exists=True)
                conn.exec_driver_sql(sql_create)

        # --- insert data ---
        cols = list(df.columns)
        sql_ins = self._insert_sql(schema, table, cols)
        stmt = sa.text(sql_ins)

        for i in range(n):
            if cancel_cb():
                break

            start = i * chunk
            end = min((i + 1) * chunk, total)
            cdf = df.iloc[start:end]

            status_cb(f"ClickHouse insert chunk {i+1}/{n} rows {start+1}-{end}")

            records = pythonize_records(cdf)

            with engine.begin() as conn:
                # executemany
                conn.execute(stmt, records)

            inserted += len(records)
            pct = int((inserted / total) * 100)
            progress_cb(min(100, max(0, pct)))

        return inserted



class GenericToSQLStrategy(InsertStrategy):
    def insert(self, df, engine, table, schema, if_exists, chunksize, dtype_map, index,
               status_cb, progress_cb, cancel_cb) -> int:
        total = len(df)
        if total == 0:
            return 0

        chunk = max(1, int(chunksize))
        n = (total + chunk - 1) // chunk
        inserted = 0

        for i in range(n):
            if cancel_cb():
                break
            start = i * chunk
            end = min((i + 1) * chunk, total)
            df_chunk = df.iloc[start:end]

            chunk_if_exists = if_exists
            if if_exists == "replace":
                chunk_if_exists = "replace" if i == 0 else "append"

            status_cb(f"Insert chunk {i+1}/{n} rows {start+1}-{end}")

            with engine.begin() as conn:
                df_chunk.to_sql(
                    name=table,
                    con=conn,
                    schema=schema,
                    if_exists=chunk_if_exists,
                    index=index,
                    method="multi",
                    dtype=dtype_map,
                    chunksize=None,
                )

            inserted += len(df_chunk)
            pct = int((inserted / total) * 100)
            progress_cb(min(100, max(0, pct)))

        return inserted


class PostgresCopyStrategy(InsertStrategy):
    def insert(self, df, engine, table, schema, if_exists, chunksize, dtype_map, index,
               status_cb, progress_cb, cancel_cb) -> int:
        if if_exists in ("replace", "fail"):
            return GenericToSQLStrategy().insert(df, engine, table, schema, if_exists, chunksize, dtype_map, index,
                                                 status_cb, progress_cb, cancel_cb)

        total = len(df)
        if total == 0:
            return 0

        chunk = max(1, int(chunksize))
        n = (total + chunk - 1) // chunk

        with engine.begin() as conn:
            df.head(0).to_sql(table, conn, schema=schema, if_exists="append", index=index, dtype=dtype_map)

        inserted = 0
        raw = engine.raw_connection()
        try:
            cur = raw.cursor()
            full = f"{schema}.{table}" if schema else table
            cols = list(df.columns)
            col_list = ", ".join([f'"{c}"' for c in cols])

            for i in range(n):
                if cancel_cb():
                    break
                start = i * chunk
                end = min((i + 1) * chunk, total)
                cdf = df.iloc[start:end]

                status_cb(f"COPY chunk {i+1}/{n} rows {start+1}-{end}")

                buf = io.StringIO()
                cdf.to_csv(buf, index=False, header=False, sep="\t", na_rep="\\N")
                buf.seek(0)

                sql = f'COPY {full} ({col_list}) FROM STDIN WITH (FORMAT csv, DELIMITER E\'\\t\', NULL \'\\N\')'
                cur.copy_expert(sql, buf)
                raw.commit()

                inserted += len(cdf)
                pct = int((inserted / total) * 100)
                progress_cb(min(100, max(0, pct)))

        finally:
            try:
                raw.close()
            except Exception:
                pass

        return inserted


def pick_strategy(engine) -> InsertStrategy:
    d = dialect_name(engine)
    if "mssql" in d:
        return MSSQLCoreStrategy()
    if d in ("postgresql", "postgres"):
        return PostgresCopyStrategy()
    if "clickhouse" in d:
        return ClickHouseCoreStrategy()
    return GenericToSQLStrategy()


# -----------------------------
# Worker
# -----------------------------

@dataclass
class RestoreJobConfig:
    table_name: str
    schema: Optional[str]
    if_exists: str
    chunk_size: int
    sanitize_cols: bool
    dtype_overrides_json: str
    write_index: bool
    type_mode: str  # "auto" | "strict"


class RestoreWorker(QObject):
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    finished = pyqtSignal(dict)
    failed = pyqtSignal(str)

    def __init__(self, data: Table, conn_input: Any, cfg: RestoreJobConfig):
        super().__init__()
        self.data = data
        self.conn_input = conn_input
        self.cfg = cfg
        self._cancel = False

    def cancel(self):
        self._cancel = True

    def _cancelled(self) -> bool:
        return self._cancel

    @pyqtSlot()
    def run(self):
        t0 = time.time()
        try:
            engine = unwrap_engine(self.conn_input)
            dname = dialect_name(engine)

            if not self.cfg.table_name.strip():
                raise ValueError("Nama table tujuan belum diisi.")

            schema = self.cfg.schema or default_schema_for_engine(engine)

            self.status.emit("Menyiapkan data…")
            df = orange_table_to_df(self.data)
            df.columns = [str(c) for c in df.columns]

            original_cols = [str(c) for c in df.columns]
            col_map: Dict[str, str] = {}
            if self.cfg.sanitize_cols:
                new_cols = sanitize_columns(original_cols)
                col_map = dict(zip(original_cols, new_cols))
                df.columns = new_cols

            df = normalize_df_for_db(df)

            total_rows = int(len(df))
            if total_rows == 0:
                raise ValueError("Data kosong (0 baris).")

            overrides_json = (self.cfg.dtype_overrides_json or "").strip()
            if overrides_json and self.cfg.sanitize_cols and col_map:
                overrides_json = remap_overrides_keys(overrides_json, col_map)

            # Default dtype map: pilih ClickHouse map kalau dialect clickhouse
            if "clickhouse" in dname:
                base_dtype = default_clickhouse_dtype_map(df)
            else:
                base_dtype = default_sqlalchemy_dtype_map(df)

            if self.cfg.type_mode == "strict":
                if not overrides_json:
                    raise ValueError("Mode strict: Override JSON wajib diisi.")

                obj = parse_override_json(overrides_json)
                df_cols = list(df.columns)
                missing = [c for c in df_cols if c not in obj]
                if missing:
                    raise ValueError("Mode strict: JSON belum mendefinisikan kolom: " + ", ".join(missing))

                dtype_map: Dict[str, sa.types.TypeEngine] = {c: parse_type(obj[c]) for c in df_cols}
                overrides_readable = {c: obj[c] for c in df_cols}
            else:
                dtype_map, overrides_readable = merge_dtype_overrides(base_dtype, overrides_json)

            self.progress.emit(0)
            self.status.emit(
                f"Mulai restore ke {target_fullname(schema, self.cfg.table_name)} "
                f"(dialect={dname}, cols={len(df.columns)}, rows={total_rows}, type_mode={self.cfg.type_mode})…"
            )

            strategy = pick_strategy(engine)

            inserted = strategy.insert(
                df=df,
                engine=engine,
                table=self.cfg.table_name.strip(),
                schema=(schema.strip() if schema else None),
                if_exists=self.cfg.if_exists,
                chunksize=int(self.cfg.chunk_size),
                dtype_map=dtype_map,
                index=bool(self.cfg.write_index),
                status_cb=self.status.emit,
                progress_cb=self.progress.emit,
                cancel_cb=self._cancelled,
            )

            if self._cancelled():
                self.status.emit("Dibatalkan oleh user.")
                ok = False
                cancelled = True
            else:
                self.progress.emit(100)
                self.status.emit("Selesai.")
                ok = True
                cancelled = False

            dur = max(0.0001, time.time() - t0)
            rps = inserted / dur

            report = {
                "ok": ok,
                "cancelled": cancelled,
                "dialect": dname,
                "target": target_fullname(schema, self.cfg.table_name),
                "inserted_rows": int(inserted),
                "total_rows": int(total_rows),
                "chunk_size": int(self.cfg.chunk_size),
                "if_exists": self.cfg.if_exists,
                "sanitize_cols": bool(self.cfg.sanitize_cols),
                "column_rename_map": col_map,
                "dtype_overrides": overrides_readable,
                "type_mode": self.cfg.type_mode,
                "duration_sec": float(dur),
                "rows_per_sec": float(rps),
                "columns": list(df.columns),
            }
            self.finished.emit(report)

        except Exception as e:
            self.failed.emit(f"{type(e).__name__}: {e}")


# -----------------------------
# Widget
# -----------------------------

class OWDBRestore(OWWidget):
    name = "Restore Database"
    id = "datahelpers-restore-to-db"
    description = "Restore/Load data dari Table ke DB Connection (batch + progress)."
    icon = "icons/restore.png"
    priority = 1200
    want_main_area = False

    class Inputs:
        data = Input("Data", Table)
        connection = Input("Connection", object, auto_summary=False)
        type_json = Input("Type JSON", str, auto_summary=False)

    class Outputs:
        report = Output("Report", dict, auto_summary=False)

    class Error(OWWidget.Error):
        missing_inputs = Msg("Butuh input Data dan Connection.")
        restore_failed = Msg("Restore gagal: {}")
        bad_dtype_override = Msg("{}")
        strict_json_required = Msg("Mode strict: Override JSON wajib diisi.")
        strict_missing_columns = Msg("Mode strict: JSON belum mendefinisikan kolom: {}")

    class Warning(OWWidget.Warning):
        cancelled = Msg("Restore dibatalkan.")
        json_extra_keys = Msg("JSON berisi kolom yang tidak ada di data: {}")

    table_suffix: str = Setting("")   # user input only (tanpa prefix)
    schema: str = Setting("")
    if_exists: int = Setting(1)  # 0 fail, 1 append, 2 replace
    chunk_size: int = Setting(5000)
    sanitize_cols: bool = Setting(True)
    write_index: bool = Setting(False)
    dtype_override_json: str = Setting("")

    type_mode: int = Setting(0)  # 0 auto, 1 strict
    auto_use_incoming_json: bool = Setting(True)


    def _on_table_suffix_changed(self):
        """
        Saat user mengetik suffix, kita sanitasi dan batasi panjang.
        Supaya user langsung lihat bentuk final yang akan dibuat.
        """
        raw = (self.table_suffix or "")
        clean_suffix = sanitize_table_suffix(raw)

        # pastikan total <= 50 saat digabung ODM_
        final_name = build_final_table_name(clean_suffix)
        # ambil suffix hasil final (tanpa prefix) untuk ditampilkan kembali
        final_suffix = final_name[len(TABLE_PREFIX):] if final_name.startswith(TABLE_PREFIX) else clean_suffix

        if final_suffix != raw:
            self.table_suffix = final_suffix


    def __init__(self):
        super().__init__()
        self.data: Optional[Table] = None
        self.conn_input: Any = None
        self._incoming_type_json: str = ""

        self._thread: Optional[QThread] = None
        self._worker: Optional[RestoreWorker] = None

        # ===== Target =====
        box = gui.widgetBox(self.controlArea, "Target", spacing=8)

        row = gui.widgetBox(box, orientation=QtCore.Qt.Horizontal, spacing=6)
        gui.label(row, self, "Table name:")

        self.lbl_prefix = gui.label(row, self, TABLE_PREFIX)
        self.lbl_prefix.setMinimumWidth(60)

        self.le_suffix = gui.lineEdit(
            row, self, "table_suffix",
            orientation=QtCore.Qt.Horizontal,
            callback=self._on_table_suffix_changed
        )

        gui.lineEdit(box, self, "schema", label="Schema (opsional)")

        # ===== Options =====
        box2 = gui.widgetBox(self.controlArea, "Options", spacing=8)
        gui.comboBox(
            box2, self, "if_exists",
            label="If exists:",
            items=["fail", "append", "replace"],
            orientation=QtCore.Qt.Horizontal
        )
        gui.spin(box2, self, "chunk_size", minv=100, maxv=500_000, step=1000, label="Chunk size:")
        gui.checkBox(box2, self, "sanitize_cols", "Sanitasi nama kolom (recommended)")
        gui.checkBox(box2, self, "write_index", "Tulis index DataFrame")

        gui.comboBox(
            box2, self, "type_mode",
            label="Type mode:",
            items=["auto (infer + override parsial)", "strict (JSON wajib & lengkap)"],
            orientation=QtCore.Qt.Horizontal,
            callback=self._on_type_mode_changed
        )

        gui.checkBox(
            box2, self, "auto_use_incoming_json",
            "Auto pakai Type JSON dari input (jika ada)",
            callback=self._on_auto_use_incoming_changed
        )

        # ===== Type mapping =====
        box3 = gui.widgetBox(self.controlArea, "Type mapping (opsional)", spacing=6)
        gui.label(box3, self, 'Override JSON (contoh: {"nilai_kontrak":"NUMERIC(18,2)","tgl_sp2d":"DATE"})')

        self._dtype_editor = QtWidgets.QPlainTextEdit()
        self._dtype_editor.setPlaceholderText('{"nilai_kontrak":"NUMERIC(18,2)","tgl_sp2d":"DATE"}')
        self._dtype_editor.setPlainText(self.dtype_override_json or "")
        self._dtype_editor.textChanged.connect(self._on_dtype_changed)
        self._dtype_editor.setMinimumHeight(180)
        box3.layout().addWidget(self._dtype_editor)

        btn_row = gui.widgetBox(box3, orientation=QtCore.Qt.Horizontal, spacing=6)
        self.btn_use_incoming = gui.button(
            btn_row, self, "Load from Type Inspector",
            callback=self._use_incoming_json
        )
        self.btn_validate = gui.button(
            btn_row, self, "Validate JSON",
            callback=self._validate_json
        )
        self.btn_template = gui.button(
            btn_row, self, "Create empty schema",
            callback=self._generate_template
        )

        # ===== Column info =====
        box_info = gui.widgetBox(self.controlArea, "Info Kolom", spacing=4)
        self.lbl_cols = gui.label(box_info, self, "Kolom: -")
        self.lbl_json = gui.label(box_info, self, "Type JSON input: -")

        # ===== Run =====
        box4 = gui.widgetBox(self.controlArea, "Run", spacing=8)
        self.btn_start = gui.button(box4, self, "Start Restore", callback=self.start_restore)
        self.btn_cancel = gui.button(box4, self, "Cancel", callback=self.cancel_restore)
        self.btn_cancel.setEnabled(False)

        self.lbl_status = gui.label(box4, self, "Status: -")

        self.progressBarInit()
        self.progressBarSet(0)

        self._refresh_info_labels()

    # --- penting: saat workflow restore ---
    def onInitialize(self):
        # pastikan tidak ada thread nyangkut dari state sebelumnya
        self._safe_stop_thread(reset_only=True)
        super().onInitialize()

    def onDeleteWidget(self):
        # kalau widget dihapus / orange ditutup, hentikan thread aman
        self._safe_stop_thread(reset_only=False)
        super().onDeleteWidget()

    def _safe_stop_thread(self, reset_only: bool = False):
        # cancel worker
        try:
            if self._worker is not None:
                self._worker.cancel()
        except Exception:
            pass

        # stop thread
        t = self._thread
        if t is not None:
            try:
                if t.isRunning():
                    t.quit()
                    t.wait(2000)
            except Exception:
                pass

        # cleanup refs
        if self._worker is not None:
            try:
                self._worker.deleteLater()
            except Exception:
                pass
        if self._thread is not None:
            try:
                self._thread.deleteLater()
            except Exception:
                pass

        self._worker = None
        self._thread = None

        if reset_only:
            # jangan sentuh data/conn, hanya thread state
            return

    # ---------- UI helpers ----------
    def _refresh_info_labels(self):
        cols = "-"
        if self.data is not None:
            try:
                df = orange_table_to_df(self.data)
                cols = f"{len(df.columns)}"
            except Exception:
                cols = "?"

        has_in = "ada" if (self._incoming_type_json or "").strip() else "tidak ada"
        self.lbl_cols.setText(f"Kolom: {cols}")
        self.lbl_json.setText(f"Type JSON input: {has_in}")

    def _on_type_mode_changed(self):
        if int(self.type_mode) == 1:
            self._dtype_editor.setPlaceholderText(
                'STRICT MODE: JSON wajib lengkap untuk semua kolom.\n'
                'Contoh: {"col1":"NVARCHAR(MAX)","col2":"NUMERIC(18,2)"}\n'
                'ClickHouse contoh: {"col1":"String","col2":"Nullable(Int64)","col3":"DateTime"}'
            )
        else:
            self._dtype_editor.setPlaceholderText('{"nilai_kontrak":"NUMERIC(18,2)","tgl_sp2d":"DATE"}')

    def _on_auto_use_incoming_changed(self):
        if self.auto_use_incoming_json:
            self._use_incoming_json()

    def _on_dtype_changed(self):
        self.dtype_override_json = self._dtype_editor.toPlainText()

    def _set_dtype_editor_text(self, txt: str):
        self._dtype_editor.blockSignals(True)
        self._dtype_editor.setPlainText(txt or "")
        self._dtype_editor.blockSignals(False)
        self.dtype_override_json = txt or ""

    # ---------- Inputs ----------
    @Inputs.data
    def set_data(self, data: Optional[Table]) -> None:
        self.data = data
        QTimer.singleShot(0, self._refresh_info_labels)

    @Inputs.connection
    def set_connection(self, conn: Any) -> None:
        self.conn_input = conn
        try:
            eng = unwrap_engine(conn)
            if eng is not None and not (self.schema or "").strip():
                if "mssql" in dialect_name(eng):
                    self.schema = "dbo"
        except Exception:
            pass

    @Inputs.type_json
    def set_type_json(self, s: Optional[str]) -> None:
        self._incoming_type_json = (s or "").strip()
        self._refresh_info_labels()
        if self.auto_use_incoming_json and self._incoming_type_json:
            self._use_incoming_json()

    # ---------- JSON actions ----------
    def _use_incoming_json(self):
        if (self._incoming_type_json or "").strip():
            self._set_dtype_editor_text(self._incoming_type_json)

    def _get_df_columns_with_optional_sanitize(self) -> Tuple[List[str], Dict[str, str]]:
        if self.data is None:
            return [], {}
        df = orange_table_to_df(self.data)
        orig = [str(c) for c in df.columns]
        if self.sanitize_cols:
            new = sanitize_columns(orig)
            return new, dict(zip(orig, new))
        return orig, {}

    def _validate_json(self):
        self.Error.clear()
        self.Warning.clear()
        try:
            cols, col_map = self._get_df_columns_with_optional_sanitize()
            s = (self.dtype_override_json or "").strip()
            if not s:
                if int(self.type_mode) == 1:
                    self.Error.strict_json_required()
                else:
                    self.lbl_status.setText("Status: JSON kosong (auto mode: OK).")
                return

            if self.sanitize_cols and col_map:
                s2 = remap_overrides_keys(s, col_map)
            else:
                s2 = s

            obj = parse_override_json(s2)

            df_cols_set = set(cols)
            json_cols_set = set(obj.keys())

            missing = sorted(list(df_cols_set - json_cols_set))
            extra = sorted(list(json_cols_set - df_cols_set))

            if int(self.type_mode) == 1 and missing:
                self.Error.strict_missing_columns(", ".join(missing))
                return

            if extra:
                self.Warning.json_extra_keys(", ".join(extra))

            self.lbl_status.setText("Status: JSON valid.")
        except Exception as e:
            self.Error.bad_dtype_override(str(e))

    def _generate_template(self):
        self.Error.clear()
        try:
            cols, _ = self._get_df_columns_with_optional_sanitize()
            if not cols:
                self.Error.restore_failed("Data belum ada, tidak bisa generate template.")
                return
            template = {c: "" for c in cols}
            txt = json.dumps(template, ensure_ascii=False, indent=2)
            self._set_dtype_editor_text(txt)
            self.lbl_status.setText("Status: Template dibuat. Isi tipe untuk tiap kolom.")
        except Exception as e:
            self.Error.restore_failed(str(e))

    # ---------- Config ----------
    def _cfg(self) -> RestoreJobConfig:
        if_exists_str = ["fail", "append", "replace"][int(self.if_exists)]
        schema = (self.schema or "").strip() or None
        type_mode_str = ["auto", "strict"][int(self.type_mode)]
        return RestoreJobConfig(
            table_name=build_final_table_name(self.table_suffix),
            schema=schema,
            if_exists=if_exists_str,
            chunk_size=int(self.chunk_size),
            sanitize_cols=bool(self.sanitize_cols),
            dtype_overrides_json=(self.dtype_override_json or "").strip(),
            write_index=bool(self.write_index),
            type_mode=type_mode_str,
        )

    # ---------- Run ----------
    def start_restore(self):
        self.Error.clear()
        self.Warning.clear()

        if self.data is None or self.conn_input is None:
            self.Error.missing_inputs()
            return

        cfg = self._cfg()

        if not cfg.table_name.lower().startswith(TABLE_PREFIX.lower()):
            self.Error.restore_failed(f"Nama table harus diawali prefix {TABLE_PREFIX}.")
            return


        if len(cfg.table_name) > TABLE_NAME_MAXLEN:
            self.Error.restore_failed(f"Nama table maksimal {TABLE_NAME_MAXLEN} karakter.")
            return

        if cfg.type_mode == "strict" and not (cfg.dtype_overrides_json or "").strip():
            self.Error.strict_json_required()
            return

        try:
            if (cfg.dtype_overrides_json or "").strip():
                _ = parse_override_json(cfg.dtype_overrides_json)
        except Exception as e:
            self.Error.bad_dtype_override(str(e))
            return

        if self._thread is not None:
            return

        self.progressBarSet(0)
        self.lbl_status.setText("Status: Menjalankan…")

        self._thread = QThread(self)
        self._worker = RestoreWorker(self.data, self.conn_input, cfg)
        self._worker.moveToThread(self._thread)

        self._thread.started.connect(self._worker.run)
        self._worker.status.connect(self._on_status)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.failed.connect(self._on_failed)

        self._worker.finished.connect(self._thread.quit)
        self._worker.failed.connect(self._thread.quit)
        self._thread.finished.connect(self._cleanup)

        self.btn_start.setEnabled(False)
        self.btn_cancel.setEnabled(True)
        self._thread.start()

    def cancel_restore(self):
        if self._worker:
            self._worker.cancel()
            self.lbl_status.setText("Status: Membatalkan…")

    def _cleanup(self):
        self.btn_start.setEnabled(True)
        self.btn_cancel.setEnabled(False)

        if self._worker:
            try:
                self._worker.deleteLater()
            except Exception:
                pass
        self._worker = None

        if self._thread:
            try:
                self._thread.deleteLater()
            except Exception:
                pass
        self._thread = None

    def _on_progress(self, pct: int):
        self.progressBarSet(int(pct))

    def _on_status(self, text: str):
        self.lbl_status.setText(f"Status: {text}")

    def _on_finished(self, report: dict):
        if report.get("cancelled"):
            self.Warning.cancelled()
        self.Outputs.report.send(report)
        self.lbl_status.setText("Status: Selesai." if report.get("ok") else "Status: Selesai (tidak ok).")

    def _on_failed(self, msg: str):
        self.Error.restore_failed(msg)
        self.lbl_status.setText("Status: Gagal.")
        self.Outputs.report.send({"ok": False, "error": msg})
