# Copyright 2026 tansadio
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo.exceptions import AccessError, UserError

from odoo.addons.cmis.exceptions import CMISContentAlreadyExistsError
from odoo.addons.cmis_folder_widget.tests.common import (
    CmisFolderWidgetCase,
    CmisFolderWidgetHttpCase,
)

from .common import AlfrescoMixin


class TestCmisFolderWidgetAlf(AlfrescoMixin, CmisFolderWidgetCase):
    def _child(self, result, name):
        return next(c for c in result["children"] if c["name"] == name)

    def test_serialize_preview_rendition(self):
        result = self.widget.get_folder(*self.params())
        self.assertEqual(self._child(result, "report.odt")["preview_rendition"], "pdf")
        self.assertNotIn("preview_rendition", self._child(result, "doc.txt"))
        self.assertNotIn("preview_rendition", self._child(result, "Sub"))

    def test_share_links(self):
        result = self.widget.get_folder(*self.params())
        self.assertNotIn("share_url", self._child(result, "report.odt"))
        self.backend.write(
            {"alfresco_share_links": True, "share_location": "http://share/share/"}
        )
        result = self.widget.get_folder(*self.params())
        node_id = self.report.id.split(";")[0]
        self.assertEqual(
            self._child(result, "report.odt")["share_url"],
            "http://share/share/page/document-details?nodeRef="
            f"workspace%3A%2F%2FSpacesStore%2F{node_id}",
        )
        self.assertIn("/page/folder-details?", self._child(result, "Sub")["share_url"])

    def test_rendition_created(self):
        self.rendition_status("CREATED")
        document, response = self.widget.get_rendition(*self.params(), self.report.id)
        self.assertEqual(document, self.report)
        node_id = self.report.id.split(";")[0]
        method, url = self.alfresco.session.request.call_args[0]
        self.assertEqual(
            (method, url),
            ("GET", f"http://alfresco/api/nodes/{node_id}/renditions/pdf/content"),
        )
        # no generation requested
        self.assertNotIn(
            "POST", [c[0][0] for c in self.alfresco.request.call_args_list]
        )

    def test_rendition_generated(self):
        self.rendition_status("NOT_CREATED", "NOT_CREATED", "CREATED")
        self.widget.get_rendition(*self.params(), self.report.id)
        post = [c for c in self.alfresco.request.call_args_list if c[0][0] == "POST"]
        self.assertEqual(len(post), 1)
        self.assertEqual(post[0][1]["json"], {"id": "pdf"})
        self.assertTrue(self.alfresco.session.request.called)

    def test_rendition_already_requested(self):
        statuses = iter(["NOT_CREATED", "CREATED"])

        def request(method, path, **kwargs):
            if method == "POST":
                raise CMISContentAlreadyExistsError("exists", status_code=409)
            return {"status": next(statuses)}

        self.alfresco.request.side_effect = request
        self.widget.get_rendition(*self.params(), self.report.id)
        self.assertTrue(self.alfresco.session.request.called)

    def test_rendition_timeout(self):
        self.backend.alfresco_rendition_timeout = 0
        self.rendition_status("NOT_CREATED")
        with self.assertRaises(UserError):
            self.widget.get_rendition(*self.params(), self.report.id)
        self.assertFalse(self.alfresco.session.request.called)

    def test_rendition_not_available(self):
        with self.assertRaises(UserError):
            self.widget.get_rendition(*self.params(), self.document.id)
        other = self.repo.add_document(
            self.other_folder,
            "other.odt",
            b"",
            "application/vnd.oasis.opendocument.text",
        )
        with self.assertRaises(AccessError):
            self.widget.get_rendition(*self.params(), other.id)


class TestControllersAlf(AlfrescoMixin, CmisFolderWidgetHttpCase):
    def test_rendition_route(self):
        self.authenticate("admin", "admin")
        self.rendition_status("CREATED")
        response = self.url_open(
            "/cmis_folder_widget_alf/rendition?"
            f"model={self.record._name}&res_id={self.record.id}"
            f"&field_name=cmis_folder&object_id={self.report.id}"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"%PDF")
        self.assertEqual(response.headers["Content-Type"], "application/pdf")
        disposition = response.headers["Content-Disposition"]
        self.assertTrue(disposition.startswith("inline"))
        self.assertIn("report.pdf", disposition)

    def test_tour(self):
        self.backend.alfresco_share_links = True
        self.rendition_status(*["CREATED"] * 5)
        view = self.env["ir.ui.view"].create(
            {
                "name": "cmis.folder.widget.test.model.form",
                "model": self.record._name,
                "arch": '<form><field name="name" />'
                '<field name="cmis_folder" /></form>',
            }
        )
        action = self.env["ir.actions.act_window"].create(
            {
                "name": "CMIS folder widget test",
                "res_model": self.record._name,
                "view_mode": "form",
                "view_id": view.id,
            }
        )
        self.start_tour(
            f"/odoo/action-{action.id}/{self.record.id}",
            "cmis_folder_widget_alf_tour",
            login="admin",
        )
