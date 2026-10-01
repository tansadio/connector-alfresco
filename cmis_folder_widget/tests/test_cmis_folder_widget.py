# Copyright 2026 tansadio
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo.exceptions import AccessError, UserError
from odoo.tests import new_test_user

from ..models.cmis_folder_widget import is_sub_path
from .common import CmisFolderWidgetCase


class TestCmisFolderWidget(CmisFolderWidgetCase):
    def test_is_sub_path(self):
        self.assertTrue(is_sub_path("/odoo/Client A", "/odoo/Client A"))
        self.assertTrue(is_sub_path("/odoo/Client A/doc", "/odoo/Client A/"))
        self.assertFalse(is_sub_path("/odoo/Client AB", "/odoo/Client A"))
        self.assertFalse(is_sub_path("/odoo/Client AB/doc", "/odoo/Client A"))
        self.assertFalse(is_sub_path("/odoo", "/odoo/Client A"))

    def test_get_folder(self):
        result = self.widget.get_folder(*self.params())
        self.assertEqual(result["folder"]["id"], self.folder.id)
        self.assertEqual(
            sorted(c["name"] for c in result["children"]), ["Sub", "doc.txt"]
        )
        document = next(c for c in result["children"] if c["name"] == "doc.txt")
        self.assertFalse(document["is_folder"])
        self.assertEqual(document["mimetype"], "text/plain")
        self.assertEqual(
            result["breadcrumbs"], [{"id": self.folder.id, "name": "Client A"}]
        )
        self.assertEqual(
            result["permissions"],
            {
                "can_create": True,
                "can_rename": True,
                "can_update_content": True,
                "can_delete": True,
            },
        )

    def test_get_sub_folder(self):
        result = self.widget.get_folder(*self.params(), self.sub_folder.id)
        self.assertEqual(result["folder"]["name"], "Sub")
        # the breadcrumbs start at the folder of the record
        self.assertEqual(
            [c["name"] for c in result["breadcrumbs"]], ["Client A", "Sub"]
        )

    def test_folder_of_another_record(self):
        # same prefix in the path, but not a descendant
        with self.assertRaises(AccessError):
            self.widget.get_folder(*self.params(), self.other_folder.id)
        with self.assertRaises(AccessError):
            self.widget.get_content(*self.params(), self.other_document.id)
        with self.assertRaises(AccessError):
            self.widget.delete(*self.params(), self.other_document.id)
        with self.assertRaises(AccessError):
            self.widget.rename(*self.params(), self.other_folder.id, "x")
        with self.assertRaises(AccessError):
            self.widget.create_folder(*self.params(), self.other_folder.id, "x")

    def test_not_a_cmis_folder_field(self):
        with self.assertRaises(AccessError):
            self.widget.get_folder(self.record._name, self.record.id, "name")
        with self.assertRaises(AccessError):
            self.widget.get_folder("unknown.model", 1, "cmis_folder")
        with self.assertRaises(AccessError):
            self.widget.get_folder(self.record._name, 0, "cmis_folder")

    def test_no_folder(self):
        record = self.record.create({"name": "No folder"})
        with self.assertRaises(UserError):
            self.widget.get_folder(*self.params(record))

    def test_create_folder(self):
        folder = self.widget.create_folder(*self.params(), self.folder.id, "New/One")
        # the name is sanitized as configured on the backend
        self.assertEqual(folder["name"], "New_One")
        self.assertTrue(folder["is_folder"])
        self.assertEqual(
            self.repo.get_object_by_path("/odoo/Client A/New_One").id, folder["id"]
        )

    def test_create_folder_in_document(self):
        with self.assertRaises(UserError):
            self.widget.create_folder(*self.params(), self.document.id, "x")

    def test_upload(self):
        documents = self.widget.upload(
            *self.params(),
            self.sub_folder.id,
            [("a.pdf", b"%PDF", "application/pdf"), ("b.txt", b"b", "text/plain")],
        )
        self.assertEqual([d["name"] for d in documents], ["a.pdf", "b.txt"])
        self.assertEqual(self.repo.contents[documents[0]["id"]], b"%PDF")

    def test_rename(self):
        self.widget.rename(*self.params(), self.document.id, "renamed.txt")
        self.assertEqual(self.document.name, "renamed.txt")
        with self.assertRaises(UserError):
            self.widget.rename(*self.params(), self.folder.id, "x")

    def test_update_content(self):
        self.widget.update_content(
            *self.params(), self.document.id, ("doc.txt", b"v2", "text/plain")
        )
        self.assertEqual(self.repo.contents[self.document.id], b"v2")
        with self.assertRaises(UserError):
            self.widget.update_content(
                *self.params(), self.sub_folder.id, ("x", b"", "text/plain")
            )

    def test_delete(self):
        self.widget.delete(*self.params(), self.document.id)
        self.assertNotIn(self.document.id, self.repo.objects)
        self.widget.delete(*self.params(), self.sub_folder.id)
        self.assertNotIn(self.sub_folder.id, self.repo.objects)
        with self.assertRaises(UserError):
            self.widget.delete(*self.params(), self.folder.id)

    def test_get_content(self):
        document, response = self.widget.get_content(*self.params(), self.document.id)
        self.assertEqual(document, self.document)
        method, url = self.repo.client.request.call_args[0]
        params = self.repo.client.request.call_args[1]["params"]
        self.assertEqual((method, url), ("GET", self.repo.root_folder_url))
        self.assertEqual(
            params, {"objectId": self.document.id, "cmisselector": "content"}
        )
        with self.assertRaises(UserError):
            self.widget.get_content(*self.params(), self.sub_folder.id)

    def test_access_rights(self):
        # a user who can read but not write the record
        user = new_test_user(self.env, login="cmis_reader", groups="base.group_user")
        self.env["ir.model.access"].create(
            {
                "name": "read only",
                "model_id": self.env["ir.model"]._get_id(self.record._name),
                "group_id": self.env.ref("base.group_user").id,
                "perm_read": True,
            }
        )
        widget = self.widget.with_user(user)
        result = widget.get_folder(*self.params())
        self.assertFalse(result["permissions"]["can_create"])
        self.assertFalse(result["permissions"]["can_delete"])
        with self.assertRaises(AccessError):
            widget.create_folder(*self.params(), self.folder.id, "x")
        with self.assertRaises(AccessError):
            widget.upload(*self.params(), self.folder.id, [("a", b"", "text/plain")])
        with self.assertRaises(AccessError):
            widget.rename(*self.params(), self.document.id, "x")
        with self.assertRaises(AccessError):
            widget.delete(*self.params(), self.document.id)
        # the credentials of the backend are not readable by the user, but
        # the operations use them
        self.assertTrue(widget.get_content(*self.params(), self.document.id))

    def test_no_read_access(self):
        user = new_test_user(self.env, login="cmis_nobody", groups="base.group_user")
        with self.assertRaises(AccessError):
            self.widget.with_user(user).get_folder(*self.params())
