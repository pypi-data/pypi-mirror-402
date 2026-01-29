import unittest
from pathlib import Path

from environ_odoo_config.odoo_config import OdooEnvConfig

from mangono_odoo_clevercloud.mappers.cc_postgresql import clevercloud_postgresql
from environ_odoo_config.environ import Environ
from dotenv import dotenv_values


class TestCleverCloudMapperPostgres(unittest.TestCase):

    def load_file(self, filename):
        return dotenv_values(Path(__file__).absolute().parent / filename)

    def test_db_profile_clever(self):
        values = self.load_file("test_db_clever.env")
        odoo_config = OdooEnvConfig(environ=values, use_os_environ=False)
        self.assertEqual("my_db_name", odoo_config.database.name)
        self.assertEqual("my_db_host", odoo_config.database.host)
        self.assertEqual(1234, odoo_config.database.port)
        self.assertEqual("my_db_user", odoo_config.database.user)
        self.assertEqual("my_db_password", odoo_config.database.password)

    def test_db_profile_clever_with_direct(self):
        values = {
            **self.load_file("test_db_clever.env"),
            **self.load_file("test_db_clever_direct.env")
        }
        odoo_config = OdooEnvConfig(environ=values, use_os_environ=False)
        self.assertEqual("my_db_name", odoo_config.database.name)
        self.assertEqual("my_db_host_direct", odoo_config.database.host)
        self.assertEqual(4567, odoo_config.database.port)
        self.assertEqual("my_db_user", odoo_config.database.user)
        self.assertEqual("my_db_password", odoo_config.database.password)
