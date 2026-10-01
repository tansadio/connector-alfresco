# Copyright 2026 tansadio
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
"""Tests against a real CMIS server, run only when ``CMIS_TEST_LOCATION``
(browser binding URL) is set, with ``CMIS_TEST_USERNAME`` and
``CMIS_TEST_PASSWORD`` (default admin / admin)."""

import os
import unittest
import uuid

from odoo.exceptions import AccessError
from odoo.tests import common, tagged

from .common import CmisFolderWidgetMixin

LOCATION = os.environ.get("CMIS_TEST_LOCATION")


@tagged("post_install", "-at_install")
@unittest.skipUnless(LOCATION, "CMIS_TEST_LOCATION is not set")
class TestCmisFolderWidgetLive(CmisFolderWidgetMixin, common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.backend.write(
            {
                "location": LOCATION,
                "username": os.environ.get("CMIS_TEST_USERNAME", "admin"),
                "password": os.environ.get("CMIS_TEST_PASSWORD", "admin"),
            }
        )
        repo = cls.backend.get_cmis_repository()
        cls.test_root = repo.get_root_folder().create_folder(
            f"odoo-cmis-widget-test-{uuid.uuid4().hex}"
        )
        cls.addClassCleanup(cls.test_root.delete_tree)
        cls.live_folder = cls.test_root.create_folder("Client A")
        cls.live_other = cls.test_root.create_folder("Client AB")
        cls.live_secret = cls.live_other.create_document(
            "secret.txt", b"secret", "text/plain"
        )
        cls.record.cmis_folder = cls.live_folder.id

    def setUp(self):
        # no fake repository: use the CMIS server
        super(CmisFolderWidgetMixin, self).setUp()

    def test_widget_operations(self):
        params = self.params()
        folder_id = self.live_folder.id
        sub = self.widget.create_folder(*params, folder_id, "Contrats")
        [document] = self.widget.upload(
            *params, sub["id"], [("contrat v1.txt", b"v1", "text/plain")]
        )
        result = self.widget.get_folder(*params, sub["id"])
        self.assertEqual([c["name"] for c in result["children"]], ["contrat v1.txt"])
        self.assertEqual(
            [c["name"] for c in result["breadcrumbs"]], ["Client A", "Contrats"]
        )
        self.widget.update_content(
            *params, document["id"], ("contrat.txt", b"v2", "text/plain")
        )
        renamed = self.widget.rename(*params, document["id"], "contrat.txt")
        self.assertEqual(renamed["name"], "contrat.txt")
        found, response = self.widget.get_content(*params, document["id"])
        self.assertEqual(b"".join(response.iter_content(1024)), b"v2")
        self.widget.delete(*params, sub["id"])
        result = self.widget.get_folder(*params)
        self.assertEqual(result["children"], [])

    def test_folder_of_another_record(self):
        params = self.params()
        with self.assertRaises(AccessError):
            self.widget.get_folder(*params, self.live_other.id)
        with self.assertRaises(AccessError):
            self.widget.get_content(*params, self.live_secret.id)
        with self.assertRaises(AccessError):
            self.widget.delete(*params, self.live_secret.id)
