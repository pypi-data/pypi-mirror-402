from __future__ import annotations

from pathlib import Path

from environ_odoo_config.config_section.api import SimpleKey
from environ_odoo_config.environ import Environ
from environ_odoo_config.odoo_config import OdooConfigExtension, OdooEnvConfig


class CleverCloudAutoConfig(OdooConfigExtension):
    _order = 999

    app_id: str = SimpleKey("CC_APP_ID")
    app_name: str = SimpleKey("CC_APP_NAME")
    commit_id: str = SimpleKey("CC_COMMIT_ID")
    deployment_id: str = SimpleKey("CC_DEPLOYMENT_ID")
    instance_type: str = SimpleKey("INSTANCE_TYPE")
    app_home: Path = SimpleKey("APP_HOME")

    def apply_extension(self, environ: Environ, odoo_config: OdooEnvConfig):
        super().apply_extension(environ, odoo_config)
        if not self.app_id:
            return

        odoo_config.misc.config_file = self.app_home / "odoo-config.ini"
        odoo_config.misc.data_dir = self.app_home / "datas"
        odoo_config.misc.pidfile = self.app_home / "odoo.pid"
        odoo_config.http.proxy_mode = True
        if not odoo_config.http.port:
            odoo_config.http.port = 8080  # Default listen http port of clevercloud

        if self.instance_type == "production" and not environ.get("LIST_DB"):
            odoo_config.database.list_db = False
