# Copyright 2026 tansadio
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
"""Tests against a real Alfresco, run only when ``CMIS_TEST_LOCATION`` (CMIS
browser binding URL) and ``ALFRESCO_TEST_API`` (REST API v1 URL) are set,
with ``CMIS_TEST_USERNAME`` and ``CMIS_TEST_PASSWORD`` (default admin / admin)."""

import io
import os
import unittest
import uuid
import zipfile

from odoo.tests import common, tagged

from odoo.addons.cmis_folder_widget.tests.common import CmisFolderWidgetMixin

from .common import ODT

LOCATION = os.environ.get("CMIS_TEST_LOCATION")
API = os.environ.get("ALFRESCO_TEST_API")


def odt_document(text):
    """Return a minimal OpenDocument text"""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as odt:
        odt.writestr(zipfile.ZipInfo("mimetype"), ODT)
        odt.writestr(
            "META-INF/manifest.xml",
            '<?xml version="1.0"?><manifest:manifest xmlns:manifest="urn:oasis:'
            'names:tc:opendocument:xmlns:manifest:1.0" manifest:version="1.2">'
            f'<manifest:file-entry manifest:full-path="/" manifest:media-type="{ODT}"/>'
            '<manifest:file-entry manifest:full-path="content.xml" '
            'manifest:media-type="text/xml"/></manifest:manifest>',
        )
        odt.writestr(
            "content.xml",
            '<?xml version="1.0"?><office:document-content xmlns:office="urn:oasis:'
            'names:tc:opendocument:xmlns:office:1.0" xmlns:text="urn:oasis:names:tc:'
            'opendocument:xmlns:text:1.0" office:version="1.2"><office:body>'
            f"<office:text><text:p>{text}</text:p></office:text></office:body>"
            "</office:document-content>",
        )
    return buffer.getvalue()


@tagged("post_install", "-at_install")
@unittest.skipUnless(LOCATION and API, "CMIS_TEST_LOCATION or ALFRESCO_TEST_API unset")
class TestCmisFolderWidgetAlfLive(CmisFolderWidgetMixin, common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.backend.write(
            {
                "location": LOCATION,
                "alfresco_api_location": API,
                "username": os.environ.get("CMIS_TEST_USERNAME", "admin"),
                "password": os.environ.get("CMIS_TEST_PASSWORD", "admin"),
                "alfresco_rendition_timeout": 60,
            }
        )
        repo = cls.backend.get_cmis_repository()
        test_root = repo.get_root_folder().create_folder(
            f"odoo-cmis-widget-alf-test-{uuid.uuid4().hex}"
        )
        cls.addClassCleanup(test_root.delete_tree)
        cls.live_folder = test_root.create_folder("Client A")
        cls.record.cmis_folder = cls.live_folder.id

    def setUp(self):
        # no fake repository: use Alfresco
        super(CmisFolderWidgetMixin, self).setUp()

    def test_rendition(self):
        [document] = self.widget.upload(
            *self.params(),
            self.live_folder.id,
            [("rapport.odt", odt_document("Bonjour Odoo"), ODT)],
        )
        self.assertEqual(document["preview_rendition"], "pdf")
        found, response = self.widget.get_rendition(*self.params(), document["id"])
        self.assertEqual(b"".join(response.iter_content(1024))[:5], b"%PDF-")
