from importlib import import_module
from typing import Tuple, Dict, Any


def _check_module(modname: str) -> Tuple[bool, str]:
    try:
        import_module(modname)
        return True, f"Module {modname} tersedia."
    except Exception as e:
        return False, f"Module {modname} belum terpasang: {e}"


def ensure_driver(kind: str) -> Tuple[bool, str, Dict[str, Any]]:
    """Pastikan driver Python untuk DB terkait sudah tersedia.

    Parameters
    ----------
    kind:
        Nama jenis DB, misal: "PostgreSQL", "MySQL", "SQLite",
        "SQL Server", "ClickHouse", "Oracle".

    Returns
    -------
    ok, log, extra
    """
    k = kind.lower()

    if "postgres" in k:
        return (*_check_module("psycopg2"), {})

    if "mysql" in k:
        return (*_check_module("pymysql"), {})
    
    if "sql server" in k or "mssql" in k or "pyodbc" in k:
        return (*_check_module("pyodbc"), {})

    if "clickhouse" in k:
        return (*_check_module("clickhouse_connect"), {})

    if "oracle" in k:
        ok, log = _check_module("oracledb")
        if ok:
            return ok, log, {}

        # (Opsional) fallback legacy cx_Oracle
        ok2, log2 = _check_module("cx_Oracle")
        if ok2:
            return ok2, "Fallback ke cx_Oracle (legacy).", {}

        return False, (
            "Driver Oracle tidak tersedia.\n"
            "- Install driver baru (disarankan): pip install oracledb\n"
            "- Atau legacy (tidak disarankan): pip install cx_Oracle\n\n"
            f"Detail:\n{log}\n{log2}"
        ), {}


    return False, f"Jenis DB tidak dikenali: {kind}", {}
