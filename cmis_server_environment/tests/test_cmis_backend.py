# Copyright 2026 tansadio
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo.exceptions import AccessError
from odoo.tests import new_test_user

from odoo.addons.server_environment.tests.common import ServerEnvironmentCase

CONFIG = """
[cmis_backend.cmis_env_test]
location = http://alfresco.prod/alfresco/api/-default-/public/cmis/versions/1.1/browser/
username = odoo
password = prod-secret
timeout = 60
"""


class TestCmisBackendServerEnv(ServerEnvironmentCase):
    def _create_backend(self):
        backend = self.env["cmis.backend"].create(
            {
                "name": "cmis_env_test",
                "location": "http://localhost:8080/browser/",
                "username": "admin",
                "password": "dev-secret",
            }
        )
        # read the values as computed from the environment, not the created ones
        backend.invalidate_recordset()
        return backend

    def test_values_from_environment(self):
        with self.load_config(public=CONFIG):
            backend = self._create_backend()
            self.assertEqual(
                backend.location,
                "http://alfresco.prod/alfresco/api/-default-/public/cmis/versions/1.1/browser/",
            )
            self.assertEqual(backend.username, "odoo")
            self.assertEqual(backend.password, "prod-secret")
            self.assertEqual(backend.timeout, 60)
            # not in the configuration: the default value
            self.assertEqual(backend.initial_directory_write, "/")
            client = backend.get_cmis_client()
            self.assertEqual(client.url, backend.location)
            self.assertEqual(client.session.auth, ("odoo", "prod-secret"))
            self.assertEqual(client.timeout, 60)
            # the values of the configuration are not editable
            self.assertFalse(backend.x_location_env_is_editable)
            self.assertTrue(backend.x_initial_directory_write_env_is_editable)

    def test_default_values(self):
        with self.load_config(public="[cmis_backend.other]\nusername = x\n"):
            backend = self._create_backend()
            self.assertEqual(backend.location, "http://localhost:8080/browser/")
            self.assertEqual(backend.username, "admin")
            self.assertEqual(backend.password, "dev-secret")
            self.assertTrue(backend.x_password_env_is_editable)
            backend.username = "other"
            self.assertEqual(backend.username, "other")

    def test_credentials_access(self):
        with self.load_config(public="[cmis_backend.other]\nusername = x\n"):
            backend = self._create_backend()
            user = new_test_user(
                self.env, login="cmis_env_user", groups="base.group_user"
            )
            user_backend = backend.with_user(user)
            self.assertEqual(user_backend.read(["name"])[0]["name"], "cmis_env_test")
            for field_name in (
                "password",
                "x_password_env_default",
                "server_env_defaults",
            ):
                with self.assertRaises(AccessError):
                    user_backend.read([field_name])
            # the users can use the backend
            self.assertEqual(
                user_backend.get_cmis_client().session.auth, ("admin", "dev-secret")
            )

    def test_alfresco_values_from_environment(self):
        backend_model = self.env["cmis.backend"]
        if "alfresco_api_location" not in backend_model._fields:
            self.skipTest("cmis_alf is not installed")
        config = CONFIG + (
            "alfresco_api_location = "
            "http://alfresco.prod/alfresco/api/-default-/public/alfresco/versions/1\n"
            "share_location = http://alfresco.prod/share\n"
        )
        with self.load_config(public=config):
            backend = self._create_backend()
            self.assertEqual(backend.share_location, "http://alfresco.prod/share")
            client = backend.get_alfresco_client()
            self.assertEqual(
                client.url,
                "http://alfresco.prod/alfresco/api/-default-/public/alfresco/versions/1",
            )
            self.assertEqual(client.session.auth, ("odoo", "prod-secret"))
