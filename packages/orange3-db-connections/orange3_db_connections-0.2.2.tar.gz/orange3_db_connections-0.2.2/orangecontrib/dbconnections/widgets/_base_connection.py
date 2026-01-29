# orangecontrib/dbconnections/widgets/_base_connection.py

from AnyQt import QtWidgets, QtCore
from AnyQt.QtCore import QThread, pyqtSignal, QTimer
from Orange.widgets.widget import OWWidget, Output, Msg
from orangewidget.settings import Setting
from orangewidget import gui

import sqlalchemy as sa
from typing import Dict, Any, Optional, Callable
import sys


# ===================== Worker =====================
class ConnectWorker(QThread):
    finished_ok = pyqtSignal(object)   # engine
    failed = pyqtSignal(str)

    def __init__(
        self,
        driver_kind: str,
        params: Dict[str, Any],
        build_url: Callable[[Dict[str, Any]], str],
        parent=None,
    ):
        super().__init__(parent)
        from orangecontrib.dbconnections.utils import ensure_driver

        self.driver_kind = driver_kind
        self.params = params
        self.build_url = build_url
        self._ensure_driver = ensure_driver

    def _pick_test_sql(self, engine: sa.Engine) -> str:
        try:
            dname = (engine.dialect.name or "").lower()
        except Exception:
            dname = ""

        if "oracle" in dname:
            return "SELECT 1 FROM DUAL"
        return "SELECT 1"

    def run(self):
        ok, log, _ = self._ensure_driver(self.driver_kind)
        if not ok:
            self.failed.emit(
                f"Driver Python belum tersedia untuk {self.driver_kind}.\n{log}\n"
                "Catatan: beberapa DB juga butuh ODBC/Client di OS."
            )
            return

        try:
            url = self.build_url(self.params)
            engine = sa.create_engine(url, pool_pre_ping=True)

            with engine.connect() as con:
                con.exec_driver_sql(self._pick_test_sql(engine))

            self.finished_ok.emit(engine)
        except Exception as e:
            self.failed.emit(str(e))


# ===================== Base Widget =====================
class BaseDBConnectionWidget(OWWidget, openclass=True):
    DB_KIND: str = "Generic DB"
    DEFAULT_PORT: int = 0

    icon = "icons/db_connection.svg"
    priority = 10
    want_main_area = False

    class Outputs:
        Connection = Output("Connection", object, auto_summary=False)

    # ---- settings umum ----
    host: str = Setting("localhost")
    port: int = Setting(0)
    database: str = Setting("")
    user: str = Setting("")
    remember_password: bool = Setting(False)

    # Tetap ada, tapi tidak ditampilkan di UI (default aktif)
    auto_connect_on_start: bool = Setting(True)
    require_user_for_autoconnect: bool = Setting(True)

    _password_mem: str = ""  # tidak disimpan sebagai Setting

    class Error(OWWidget.Error):
        connect_error = Msg("Gagal konek: {}")

    class Info(OWWidget.Information):
        connected = Msg("Terkoneksi ke database.")
        disconnected = Msg("Belum terkoneksi.")
        hint = Msg("")

    class Warning(OWWidget.Warning):
        generic_warn = Msg("{}")

    def __init__(self):
        super().__init__()

        self._engine: Optional[sa.Engine] = None

        # --- form umum ---
        box = gui.widgetBox(self.controlArea, "Koneksi")

        gui.lineEdit(box, self, "host", label="Host:")
        gui.spin(box, self, "port", 0, 65535, label="Port:", step=1)
        gui.lineEdit(box, self, "database", label="Database/Schema/Path:")
        gui.lineEdit(box, self, "user", label="Username:")
        gui.lineEdit(
            box, self, "_password_mem",
            label="Password:",
            echoMode=QtWidgets.QLineEdit.Password,
        )

        # (Dihilangkan) box "Opsi" + 2 checkbox
        # - auto_connect_on_start
        # - require_user_for_autoconnect
        # Default tetap aktif via Setting(True) di atas.

        # area ekstra untuk subclass
        self._extra_controls(box)

        btns = gui.widgetBox(box, orientation=QtCore.Qt.Horizontal)
        self.btn_connect = gui.button(btns, self, "Connect", callback=self._connect)
        self.btn_disconnect = gui.button(btns, self, "Disconnect", callback=self._disconnect)
        self.btn_disconnect.setDisabled(True)

        self.Info.hint()
        self._worker: Optional[ConnectWorker] = None

        if not self.port:
            self._apply_default_port()

        QTimer.singleShot(0, self._maybe_autoconnect_on_start)
        self.Info.disconnected()

    # ===== hooks untuk subclass =====
    def _extra_controls(self, box: QtWidgets.QGroupBox) -> None:
        return None

    def _apply_default_port(self):
        self.port = getattr(self, "DEFAULT_PORT", 0)

    def _params(self) -> Dict[str, Any]:
        return {
            "host": (self.host or "").strip(),
            "port": int(self.port or 0),
            "database": (self.database or "").strip(),
            "user": (self.user or "").strip(),
            "password": self._password_mem or "",
        }

    def _build_url(self, params: Dict[str, Any]) -> str:
        raise NotImplementedError

    def _driver_kind(self) -> str:
        return getattr(self, "DB_KIND", "Generic DB")

    # ===== lifecycle =====
    def onDeleteWidget(self):
        self._safe_kill_worker()
        try:
            self.Outputs.Connection.send(None)
        except Exception:
            pass
        super().onDeleteWidget()

    # ===== worker handling =====
    def _toggle_busy(self, busy: bool):
        self.btn_connect.setDisabled(busy)
        self.btn_disconnect.setDisabled(busy or (self._engine is None))

    def _safe_kill_worker(self):
        w = getattr(self, "_worker", None)
        if not w:
            return
        try:
            try: w.finished_ok.disconnect(self._on_connected)
            except Exception: pass
            try: w.failed.disconnect(self._on_failed)
            except Exception: pass
            try: w.finished.disconnect(self._on_worker_finished)
            except Exception: pass

            try: w.setParent(None)
            except Exception: pass
            try: w.deleteLater()
            except Exception: pass
        finally:
            self._worker = None

    # ===== autoconnect =====
    def _maybe_autoconnect_on_start(self):
        if not self.auto_connect_on_start:
            return
        if self._engine is not None:
            return

        p = self._params()
        if not p["host"]:
            return
        if self.require_user_for_autoconnect and not p["user"]:
            return

        self._connect()

    # ===== actions =====
    def _connect(self):
        self._safe_kill_worker()
        self.Error.clear()
        self.Info.clear()
        self.Warning.clear()
        self._toggle_busy(True)

        params = self._params()

        self._worker = ConnectWorker(
            driver_kind=self._driver_kind(),
            params=params,
            build_url=self._build_url,
            parent=self,
        )
        self._worker.finished_ok.connect(self._on_connected)
        self._worker.failed.connect(self._on_failed)
        self._worker.finished.connect(self._on_worker_finished)
        self._worker.start()

    def _disconnect(self):
        self._engine = None
        self.Outputs.Connection.send(None)
        self.Info.disconnected()
        self.Error.clear()
        self.Warning.clear()
        self.btn_disconnect.setDisabled(True)

    def _on_worker_finished(self):
        QTimer.singleShot(0, self._finish_worker_cleanup)

    def _finish_worker_cleanup(self):
        self._toggle_busy(False)
        self._safe_kill_worker()

    def _on_connected_extra(self, engine) -> None:
        return None

    def _on_connected(self, engine):
        self._engine = engine

        sys.stderr.write(f"=== DB CONNECTED === {self.DB_KIND}\n")
        sys.stderr.write(f"ENGINE: {type(engine)} {engine}\n")
        sys.stderr.flush()

        self._on_connected_extra(engine)

        if not self.remember_password:
            self._password_mem = ""

        self.Info.connected()
        self.btn_disconnect.setDisabled(False)

        self.Outputs.Connection.send(engine)
        QTimer.singleShot(0, lambda e=engine: self.Outputs.Connection.send(e))

    def _on_failed(self, err: str):
        self._engine = None
        self.Outputs.Connection.send(None)
        self.Error.connect_error(err)
        self.Info.disconnected()
        self.btn_disconnect.setDisabled(True)
