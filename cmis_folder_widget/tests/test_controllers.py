# Copyright 2026 tansadio
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import json
from unittest import mock

from odoo import http
from odoo.tools import mute_logger

from .common import CmisFolderWidgetHttpCase


class TestControllers(CmisFolderWidgetHttpCase):
    def setUp(self):
        super().setUp()
        self.authenticate("admin", "admin")
        content = mock.MagicMock(headers={"Content-Length": "5"})
        content.iter_content.return_value = [b"hel", b"lo"]
        self.repo.client.request.return_value = content

    def content_url(self, document, **params):
        params = {
            "model": self.record._name,
            "res_id": self.record.id,
            "field_name": "cmis_folder",
            "object_id": document.id,
            **params,
        }
        query = "&".join(f"{k}={v}" for k, v in params.items())
        return f"/cmis_folder_widget/content?{query}"

    def test_content_inline(self):
        response = self.url_open(self.content_url(self.document))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"hello")
        self.assertTrue(response.headers["Content-Disposition"].startswith("inline"))
        self.assertEqual(response.headers["X-Content-Type-Options"], "nosniff")
        self.assertEqual(response.headers["Content-Length"], "5")

    def test_content_download(self):
        response = self.url_open(self.content_url(self.document, download="true"))
        self.assertTrue(
            response.headers["Content-Disposition"].startswith("attachment")
        )

    def test_content_html_is_downloaded(self):
        page = self.repo.add_document(
            self.folder, "page.html", b"<script/>", "text/html"
        )
        response = self.url_open(self.content_url(page))
        self.assertTrue(
            response.headers["Content-Disposition"].startswith("attachment")
        )

    def test_content_forbidden(self):
        response = self.url_open(self.content_url(self.other_document))
        self.assertEqual(response.status_code, 403)

    def _upload_data(self, **values):
        return {
            "model": self.record._name,
            "res_id": self.record.id,
            "field_name": "cmis_folder",
            "folder_id": self.folder.id,
            **values,
        }

    def test_upload(self):
        response = self.url_open(
            "/cmis_folder_widget/upload",
            data=self._upload_data(csrf_token=http.Request.csrf_token(self)),
            files=[("ufile", ("new.txt", b"new", "text/plain"))],
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual([d["name"] for d in response.json()], ["new.txt"])
        new = self.repo.get_object_by_path("/odoo/Client A")
        self.assertIn("new.txt", [c.name for c in self.repo._children(new.id)])

    @mute_logger("odoo.http")
    def test_upload_without_csrf_token(self):
        response = self.url_open(
            "/cmis_folder_widget/upload",
            data=self._upload_data(),
            files=[("ufile", ("new.txt", b"new", "text/plain"))],
        )
        self.assertEqual(response.status_code, 400)
        self.assertNotIn(
            "new.txt", [c.name for c in self.repo._children(self.folder.id)]
        )

    def test_upload_forbidden_folder(self):
        response = self.url_open(
            "/cmis_folder_widget/upload",
            data=self._upload_data(
                folder_id=self.other_folder.id,
                csrf_token=http.Request.csrf_token(self),
            ),
            files=[("ufile", ("new.txt", b"new", "text/plain"))],
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json())

    def test_jsonrpc_folder(self):
        response = self.url_open(
            "/cmis_folder_widget/folder",
            data=json.dumps(
                {
                    "params": {
                        "model": self.record._name,
                        "res_id": self.record.id,
                        "field_name": "cmis_folder",
                    }
                }
            ),
            headers={"Content-Type": "application/json"},
        )
        self.assertNotIn("error", response.json(), response.text)
        result = response.json()["result"]
        self.assertEqual(result["folder"]["id"], self.folder.id)


class TestAssets(CmisFolderWidgetHttpCase):
    def test_backend_bundle(self):
        """The javascript of the module is valid and in the backend bundle"""
        bundle = self.env["ir.qweb"]._get_asset_bundle("web.assets_backend")
        js = bundle.js().raw.decode()
        self.assertIn("/cmis_folder_widget/static/src/cmis_folder/", js)
        self.assertIn("/cmis_folder_widget/upload", js)
        self.assertIn('t-name="cmis_folder_widget.CmisFolderField"', js)
        # each module is transpiled and defined (not the case on a syntax error)
        for module in (
            "cmis_file_model",
            "cmis_folder/cmis_folder_field",
            "cmis_table/cmis_table",
            "cmis_actions/cmis_actions",
            "cmis_breadcrumbs/cmis_breadcrumbs",
            "dialogs/name_dialog",
            "dialogs/file_dialog",
        ):
            self.assertIn(f"odoo.define('@cmis_folder_widget/{module}.esm'", js)
