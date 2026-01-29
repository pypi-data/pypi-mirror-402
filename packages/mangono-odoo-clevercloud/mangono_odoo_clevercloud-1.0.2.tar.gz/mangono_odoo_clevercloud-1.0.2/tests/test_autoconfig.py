import unittest
from pathlib import Path

from environ_odoo_config.odoo_config import OdooEnvConfig

from mangono_odoo_clevercloud.extensions.cc_auto_config import CleverCloudAutoConfig
from mangono_odoo_clevercloud.mappers.cc_postgresql import clevercloud_postgresql
from environ_odoo_config.environ import Environ
from dotenv import dotenv_values

DEFAULT_CC_ENV = {
            "CC_APP_ID": "addon_c32a24fa-624d-484d-b423-e439a4d65f96",
            "CC_APP_NAME": "test-app",
            "CC_COMMIT_ID": "12bd575",
            "CC_DEPLOYMENT_ID": "deployment_0000",
            "INSTANCE_TYPE": "production",
            "APP_HOME": "/home",
        }
class TestAutoConfigCleverCloud(unittest.TestCase):

    def test_instance_type_production(self):
        values = DEFAULT_CC_ENV
        odoo_config = OdooEnvConfig(environ=values, use_os_environ=False)
        self.assertEqual(True, odoo_config.database.list_db)
        self.assertEqual(False, odoo_config.http.proxy_mode)
        self.assertEqual(0, odoo_config.http.port)
        odoo_config.apply_extension(CleverCloudAutoConfig)
        self.assertEqual(False, odoo_config.database.list_db)
        self.assertEqual(True, odoo_config.http.proxy_mode)
        self.assertEqual(8080, odoo_config.http.port)

    def test_instance_type_preview(self):
        values = dict(DEFAULT_CC_ENV, INSTANCE_TYPE="preview")
        odoo_config = OdooEnvConfig(environ=values, use_os_environ=False)
        self.assertEqual(True, odoo_config.database.list_db)
        self.assertEqual(False, odoo_config.http.proxy_mode)
        self.assertEqual(0, odoo_config.http.port)
        odoo_config.apply_extension(CleverCloudAutoConfig)
        self.assertEqual(True, odoo_config.database.list_db)
        self.assertEqual(True, odoo_config.http.proxy_mode)
        self.assertEqual(8080, odoo_config.http.port)

    def test_preview_force_list_db(self):
        values = dict(DEFAULT_CC_ENV, INSTANCE_TYPE="preview", LIST_DB="False")
        odoo_config = OdooEnvConfig(environ=values, use_os_environ=False)
        self.assertEqual(False, odoo_config.database.list_db)
        self.assertEqual(False, odoo_config.http.proxy_mode)
        self.assertEqual(0, odoo_config.http.port)
        odoo_config.apply_extension(CleverCloudAutoConfig)
        self.assertEqual(False, odoo_config.database.list_db)
        self.assertEqual(True, odoo_config.http.proxy_mode)
        self.assertEqual(8080, odoo_config.http.port)

    def test_production_force_list_db(self):
        values = dict(DEFAULT_CC_ENV, LIST_DB="True")
        odoo_config = OdooEnvConfig(environ=values, use_os_environ=False)
        self.assertEqual(True, odoo_config.database.list_db)
        self.assertEqual(False, odoo_config.http.proxy_mode)
        self.assertEqual(0, odoo_config.http.port)
        odoo_config.apply_extension(CleverCloudAutoConfig)
        self.assertEqual(True, odoo_config.database.list_db)
        self.assertEqual(True, odoo_config.http.proxy_mode)
        self.assertEqual(8080, odoo_config.http.port)

    def test_datadir(self):
        odoo_config = OdooEnvConfig(environ=dict(DEFAULT_CC_ENV), use_os_environ=False)
        self.assertEqual(None, odoo_config.misc.data_dir)
        self.assertEqual(None, odoo_config.misc.config_file)
        self.assertEqual(None , odoo_config.misc.pidfile)
        odoo_config.apply_extension(CleverCloudAutoConfig)
        self.assertEqual(Path(DEFAULT_CC_ENV["APP_HOME"]) / "datas", odoo_config.misc.data_dir)
        self.assertEqual(Path(DEFAULT_CC_ENV["APP_HOME"]) / "odoo-config.ini", odoo_config.misc.config_file)
        self.assertEqual(Path(DEFAULT_CC_ENV["APP_HOME"]) / "odoo.pid", odoo_config.misc.pidfile)
