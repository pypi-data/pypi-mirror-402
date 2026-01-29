import sys
import platform
from importlib import import_module
from typing import Optional, Tuple, List

from AnyQt.QtCore import Qt
from AnyQt.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QTextEdit,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QLabel,
)

from Orange.widgets.widget import OWWidget


# Daftar “tipe koneksi” yang ada di add-on DB Connections
# Fokus: modul Python & catatan OS/driver
CONNECTION_SPECS = [
    {
        "id": "mssql",
        "label": "SQL Server (pyodbc + ODBC)",
        "module": "pyodbc",
        "pip": "pyodbc",
        "note": "Butuh ODBC Driver 17/18 for SQL Server di Windows.",
    },
    {
        "id": "postgresql",
        "label": "PostgreSQL (psycopg2-binary)",
        "module": "psycopg2",
        "pip": "psycopg2-binary",
        "note": "Butuh psycopg2 (bisa binary).",
    },
    {
        "id": "mysql",
        "label": "MySQL (pymysql)",
        "module": "pymysql",
        "pip": "pymysql",
        "note": "Driver pure Python, tidak perlu client tambahan.",
    },
    {
        "id": "sqlite",
        "label": "SQLite (builtin sqlite3)",
        "module": "sqlite3",
        "pip": None,
        "note": "Sudah bawaan Python, seharusnya selalu tersedia.",
    },
    {
        "id": "clickhouse",
        "label": "ClickHouse (clickhouse-connect)",
        "module": "clickhouse_connect",
        "pip": "clickhouse-connect",
        "note": "Tidak perlu client tambahan.",
    },
    {
        "id": "oracle",
        "label": "Oracle (python-oracledb)",
        "module": "oracledb",
        "pip": "oracledb",
        "note": "Default Thin mode (tanpa Instant Client). Thick mode opsional jika butuh fitur tertentu.",
    },
]


def _check_module(mod_name: str) -> Tuple[str, str]:
    """
    Coba import modul. Return (status, detail).
    status: 'OK' | 'Missing' | 'Warning'
    """
    try:
        mod = import_module(mod_name)
        version = getattr(mod, "__version__", "?")
        return "OK", f"Terpasang (versi {version})"
    except Exception as e:
        return "Missing", f"Tidak ditemukan: {e.__class__.__name__}: {e}"


def _check_odbc() -> Tuple[str, str, List[str]]:
    """
    Cek daftar ODBC driver (kalau pyodbc tersedia).
    """
    try:
        import pyodbc
    except ImportError:
        return "Missing", "pyodbc belum terpasang, tidak bisa cek ODBC driver.", []

    drivers = list(pyodbc.drivers())
    if not drivers:
        return (
            "Warning",
            "pyodbc ada, tapi tidak ada ODBC driver terdeteksi. "
            "Pastikan ODBC Driver 17 atau 18 for SQL Server sudah terinstal.",
            [],
        )

    return "OK", f"Ditemukan {len(drivers)} driver ODBC.", drivers


def _check_oracle_oracledb():
    status, detail = _check_module("oracledb")

    if status != "OK":
        return "Missing", detail, ""

    try:
        import oracledb

        try:
            thin = oracledb.is_thin_mode()
        except Exception:
            thin = None

        if thin is True:
            return "OK", f"{detail}; Mode: Thin (tanpa Instant Client).", ""

        if thin is False:
            try:
                cv = oracledb.clientversion()
                return "OK", f"{detail}; Mode: Thick (clientversion={cv}).", ""
            except Exception as e:
                return (
                    "Warning",
                    f"{detail}; Mode: Thick tapi Oracle Client belum siap: {e}",
                    "",
                )

        return "Warning", f"{detail}; Tidak bisa memastikan Thin/Thick mode.", ""

    except Exception as e:
        return "Warning", f"{detail}; Gagal cek mode: {e}", ""


class OWDbEnvCheck(OWWidget):
    """
    Widget khusus DB Connections:
    - Menampilkan info Python/OS yang dipakai Orange
    - Mengecek modul driver DB (pyodbc, psycopg2, dll.)
    - Mengecek ODBC driver (kalau pyodbc tersedia)
    - Khusus Oracle: cek python-oracledb + Thin/Thick mode
    """

    name = "Env Check"
    description = "Cek environment untuk koneksi database (driver Python & ODBC)."
    icon = "icons/db_env_check.svg"
    priority = 100

    want_main_area = True
    want_control_area = False

    def __init__(self):
        super().__init__()

        self.btn_scan = QPushButton("🔍 Scan DB Environment")
        self.btn_scan.clicked.connect(self.scan_environment)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(
            ["Connection", "Python Module", "Status", "Detail", "Cara Perbaikan"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setMinimumHeight(240)

        self.txt_summary = QTextEdit()
        self.txt_summary.setReadOnly(True)
        self.txt_summary.setMinimumHeight(160)

        main = QVBoxLayout()
        main.addWidget(
            QLabel(
                "<b>Bidics DB Connections – Environment Check</b><br/>"
                "Scan modul Python & driver ODBC yang dibutuhkan oleh widget koneksi database."
            )
        )
        main.addWidget(self.btn_scan)
        main.addWidget(self.table)
        main.addWidget(QLabel("<b>Ringkasan</b>"))
        main.addWidget(self.txt_summary)

        w = QWidget()
        w.setLayout(main)
        self.mainArea.layout().addWidget(w)

    def _build_fix_command(self, pip_name: Optional[str]) -> str:
        python_exe = sys.executable
        if pip_name:
            return f'"{python_exe}" -m pip install {pip_name}'
        return "(builtin; kalau error, cek instalasi Python/Orange)."

    def scan_environment(self):
        self.table.setRowCount(0)

        py_info_lines = [
            f"Python Executable : {sys.executable}",
            f"Python Version    : {sys.version.split()[0]}",
            f"Platform          : {platform.platform()}",
            f"Arch              : {platform.architecture()[0]}",
            "",
            "=== Status Driver Python ===",
        ]

        rows = []
        for spec in CONNECTION_SPECS:
            if spec["id"] == "oracle":
                # Oracle special check (oracledb + Thin/Thick)
                o_status, o_detail, o_fix_hint = _check_oracle_oracledb()
                fix_cmd = o_fix_hint or self._build_fix_command(spec.get("pip"))
                rows.append((spec["label"], spec["module"], o_status, o_detail, fix_cmd))
                py_info_lines.append(f"- {spec['label']}: {o_status} ({o_detail})")
                continue

            status, detail = _check_module(spec["module"])
            fix_cmd = self._build_fix_command(spec.get("pip"))
            rows.append((spec["label"], spec["module"], status, detail, fix_cmd))
            py_info_lines.append(f"- {spec['label']}: {status} ({detail})")

        py_info_lines.append("")
        py_info_lines.append("=== Status ODBC (SQL Server) ===")
        odbc_status, odbc_detail, odbc_drivers = _check_odbc()
        py_info_lines.append(f"ODBC Drivers: {odbc_status} ({odbc_detail})")
        if odbc_drivers:
            py_info_lines.append("Daftar driver:")
            for drv in odbc_drivers:
                py_info_lines.append(f"  - {drv}")

        for row_data in rows:
            r = self.table.rowCount()
            self.table.insertRow(r)
            for c, value in enumerate(row_data):
                item = QTableWidgetItem(str(value))
                if c == 2:  # kolom Status
                    if value == "Missing":
                        item.setForeground(Qt.red)
                    elif value == "Warning":
                        item.setForeground(Qt.darkYellow)
                self.table.setItem(r, c, item)

        self.txt_summary.setText("\n".join(py_info_lines))
