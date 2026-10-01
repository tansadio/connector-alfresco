# Copyright 2026 tansadio
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import itertools
from types import MappingProxyType
from unittest import mock

from odoo_test_helper import FakeModelLoader

from odoo.tests import common, tagged

from odoo.addons.cmis.client import CmisObject, CmisPage
from odoo.addons.cmis.exceptions import CMISObjectNotFoundError


class FakeRepository:
    """In memory CMIS repository, with a tree of folders and documents"""

    root_folder_url = "http://cmis/browser/root"

    def __init__(self):
        self.ids = itertools.count(1)
        self.objects = {}
        self.parents = {}
        self.contents = {}
        self.client = mock.MagicMock()
        self.root = self._add("/", "Company Home", None, "cmis:folder")

    def _add(self, path, name, parent, base_type, mimetype=None):
        object_id = f"id{next(self.ids)}"
        if base_type == "cmis:document":
            object_id += ";1.0"
        props = {
            "cmis:objectId": object_id,
            "cmis:name": name,
            "cmis:baseTypeId": base_type,
            "cmis:objectTypeId": base_type,
            "cmis:contentStreamMimeType": mimetype,
            "cmis:lastModificationDate": 1767225600000,
        }
        if base_type == "cmis:folder":
            props["cmis:path"] = path
            props["cmis:parentId"] = parent and parent.id
        obj = CmisObject(self, props)
        self.objects[object_id] = obj
        self.parents[object_id] = parent
        return obj

    def _children(self, folder_id):
        return [
            o
            for i, o in self.objects.items()
            if self.parents[i] and self.parents[i].id == folder_id
        ]

    def add_folder(self, parent, name):
        if any(c.name == name for c in self._children(parent.id)):
            raise AssertionError(f"{name} already exists")
        return self._add(
            f"{parent.path.rstrip('/')}/{name}", name, parent, "cmis:folder"
        )

    def add_document(self, parent, name, content=b"", mimetype="text/plain"):
        document = self._add(None, name, parent, "cmis:document", mimetype)
        self.contents[document.id] = content
        return document

    # CmisRepository API used by the widget

    def get_object(self, object_id):
        if object_id not in self.objects:
            raise CMISObjectNotFoundError("Object not found", "objectNotFound", 404)
        return self.objects[object_id]

    def get_object_by_path(self, path):
        for obj in self.objects.values():
            if obj.path == path:
                return obj
        raise CMISObjectNotFoundError("Object not found", "objectNotFound", 404)

    def get_parents(self, object_id):
        parent = self.parents[object_id]
        return [parent] if parent else []

    def iter_children(self, folder_id, page_size=100):
        return iter(self._children(folder_id))

    def get_children(self, folder_id, max_items=100, skip_count=0):
        children = self._children(folder_id)
        return CmisPage(children, False, len(children))

    def query(self, statement, max_items=100, skip_count=0):
        return CmisPage([], False, 0)

    def create_folder(self, parent_id, name, properties=None):
        return self.add_folder(self.get_object(parent_id), name)

    def create_document(self, parent_id, name, content=b"", mime_type=None, **kw):
        return self.add_document(self.get_object(parent_id), name, content, mime_type)

    def update_properties(self, object_id, properties):
        obj = self.get_object(object_id)
        obj.properties.update(properties)
        return obj

    def set_content(self, object_id, content, mime_type, filename="content"):
        self.contents[object_id] = content
        obj = self.get_object(object_id)
        obj.properties["cmis:contentStreamMimeType"] = mime_type
        return obj

    def delete(self, object_id, all_versions=True):
        del self.objects[object_id]

    def delete_tree(self, folder_id, all_versions=True, continue_on_failure=False):
        for child in self._children(folder_id):
            if child.is_folder:
                self.delete_tree(child.id)
            else:
                self.delete(child.id)
        self.delete(folder_id)


class CmisFolderWidgetMixin:
    """Fake model with a cmis_folder field, linked to a folder of a fake
    repository::

        /odoo/Client A          <- folder of the record
        /odoo/Client A/doc.txt
        /odoo/Client A/Sub
        /odoo/Client AB         <- folder of another record
        /odoo/Client AB/secret.txt
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.loader = FakeModelLoader(cls.env, cls.__module__)
        cls.loader.backup_registry()
        from .models import CmisFolderWidgetTestModel

        cls.loader.update_registry((CmisFolderWidgetTestModel,))
        # compute the fields of the ir.model.fields created for the fake
        # models now: they no longer exist once the test class rolled back
        cls.env.flush_all()
        cls.addClassCleanup(cls._restore_registry)

        cls.backend = cls.env["cmis.backend"].create(
            {
                "name": "cmis_folder_widget_test",
                "location": "http://cmis/browser/",
                "username": "admin",
                "password": "secret",
            }
        )
        cls._build_repository(cls)
        cls.record = cls.env["cmis.folder.widget.test.model"].create(
            {"name": "Client A", "cmis_folder": cls.folder.id}
        )
        cls.widget = cls.env["cmis.folder.widget"]

    @classmethod
    def _restore_registry(cls):
        original = cls.loader._original_registry
        cls.loader.restore_registry()
        # With Odoo 19, model._fields is a read-only view of model._fields__
        # and the fields are attributes of the model classes: restore_registry
        # only replaces model._fields by a copy and removes the attributes, so
        # the ORM would use other field objects. Restore them consistently.
        for name, model in cls.env.registry.models.items():
            fields_ = dict(original[name]["_fields"])
            model._fields__.clear()
            model._fields__.update(fields_)
            model._fields = MappingProxyType(model._fields__)
            for field_name, field in fields_.items():
                if vars(model).get(field_name) is not field:
                    setattr(model, field_name, field)

    @staticmethod
    def _build_repository(target):
        """Build the tree (the ids are the same at each build)"""
        target.repo = FakeRepository()
        odoo_folder = target.repo.add_folder(target.repo.root, "odoo")
        target.folder = target.repo.add_folder(odoo_folder, "Client A")
        target.document = target.repo.add_document(target.folder, "doc.txt", b"hello")
        target.sub_folder = target.repo.add_folder(target.folder, "Sub")
        target.other_folder = target.repo.add_folder(odoo_folder, "Client AB")
        target.other_document = target.repo.add_document(
            target.other_folder, "secret.txt"
        )

    def setUp(self):
        super().setUp()
        # a new repository for each test, the tests change it
        self._build_repository(self)
        patcher = mock.patch(
            "odoo.addons.cmis.models.cmis_backend.CmisBackend.get_cmis_repository",
            return_value=self.repo,
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def params(self, record=None):
        record = record or self.record
        return (record._name, record.id, "cmis_folder")


@tagged("post_install", "-at_install")
class CmisFolderWidgetCase(CmisFolderWidgetMixin, common.TransactionCase):
    pass


@tagged("post_install", "-at_install")
class CmisFolderWidgetHttpCase(CmisFolderWidgetMixin, common.HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # the requests are done by a user, who needs an access to the model
        cls.env["ir.model.access"].create(
            {
                "name": "cmis.folder.widget.test.model user",
                "model_id": cls.env["ir.model"]._get_id(cls.record._name),
                "group_id": cls.env.ref("base.group_user").id,
                "perm_read": True,
                "perm_write": True,
                "perm_create": True,
                "perm_unlink": True,
            }
        )
