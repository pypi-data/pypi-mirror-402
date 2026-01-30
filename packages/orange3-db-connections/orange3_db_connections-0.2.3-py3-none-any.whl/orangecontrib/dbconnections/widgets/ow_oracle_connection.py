# orangecontrib/dbconnections/widgets/ow_oracle_connection.py

from typing import Dict, Any
from ._base_connection import BaseDBConnectionWidget


class OWOracleConnection(BaseDBConnectionWidget):
    name = "Oracle"
    id = "dbconnections-oracle-connection"
    description = "Koneksi ke Oracle Database. Output: SQLAlchemy Engine."
    icon = "icons/oracle.png"

    DB_KIND = "Oracle"
    DEFAULT_PORT = 1521

    def _build_url(self, params: Dict[str, Any]) -> str:
        """
        SQLAlchemy URL untuk Oracle menggunakan python-oracledb (default Thin mode).

        Field "Database/Schema/Path" diisi SERVICE_NAME
        contoh: ORCLPDB1
        """
        user = (params.get("user") or "").strip()
        pwd = params.get("password") or ""
        host = (params.get("host") or "localhost").strip()
        port = int(params.get("port") or self.DEFAULT_PORT)
        service = (params.get("database") or "").strip()

        auth = ""
        if user:
            auth = f"{user}:{pwd}@" if pwd else f"{user}@"

        # SQLAlchemy standard format
        if service:
            dsn = f"{host}:{port}/?service_name={service}"
        else:
            dsn = f"{host}:{port}"

        return f"oracle+oracledb://{auth}{dsn}"
