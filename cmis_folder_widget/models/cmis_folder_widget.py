# Copyright 2026 tansadio
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
"""Operations of the CMIS folder widget.

The browser never calls the CMIS server: every operation goes through this
model, with the account of the CMIS backend, once checked that:

- the user has the required access on the record and on the field;
- the CMIS object is the folder of the record or one of its descendants.
"""

from dataclasses import dataclass

from odoo import api, models
from odoo.exceptions import AccessError, UserError

from odoo.addons.cmis.client import CmisObject, CmisRepository
from odoo.addons.cmis_field.fields import CmisFolder

DEFAULT_CHILDREN_LIMIT = 1000


def is_sub_path(path, root_path):
    """Return True if ``path`` is ``root_path`` or one of its descendants"""
    root_path = root_path.rstrip("/")
    return path == root_path or path.startswith(f"{root_path}/")


@dataclass
class FolderContext:
    """The record and CMIS folder an operation of the widget applies to"""

    record: models.BaseModel
    field: CmisFolder
    backend: models.BaseModel
    repository: CmisRepository
    root: CmisObject

    def is_root(self, cmis_object):
        return cmis_object.id == self.root.id

    def get_object(self, object_id=None):
        """Return the object, after checking it is in the folder of the
        record. Without id, return the folder of the record."""
        if not object_id or object_id == self.root.id:
            return self.root
        cmis_object = self.repository.get_object(object_id)
        paths = cmis_object.get_paths()
        if not paths and cmis_object.is_document:
            # an old version of a document is not filed in a folder: use the
            # latest version (the id changes on each new version)
            cmis_object = self._get_latest_version(object_id)
            paths = cmis_object.get_paths()
        if not any(is_sub_path(p, self.root.path) for p in paths):
            raise AccessError(
                self.record.env._("This content is not in the folder of the record.")
            )
        return cmis_object

    def _get_latest_version(self, object_id):
        response = self.repository.client.request(
            "GET",
            self.repository.root_folder_url,
            params={
                "objectId": object_id,
                "cmisselector": "object",
                "succinct": "true",
                "returnVersion": "latest",
            },
        )
        return CmisObject(
            self.repository, response.json().get("succinctProperties", {})
        )

    def get_folder(self, folder_id=None):
        folder = self.get_object(folder_id)
        if not folder.is_folder:
            raise UserError(self.record.env._("%s is not a folder.", folder.name))
        return folder


class CmisFolderWidget(models.AbstractModel):
    _name = "cmis.folder.widget"
    _description = "CMIS folder widget operations"

    @api.model
    def _get_context(self, model, res_id, field_name, operation="read"):
        if model not in self.env:
            raise AccessError(self.env._("Unknown model %s.", model))
        record = self.env[model].browse(int(res_id)).exists()
        if not record:
            raise AccessError(self.env._("The record does not exist."))
        field = record._fields.get(field_name)
        if not isinstance(field, CmisFolder):
            raise AccessError(self.env._("%s is not a CMIS folder field.", field_name))
        record.check_access(operation)
        record._check_field_access(field, "read")
        root_id = record[field_name]
        if not root_id:
            raise UserError(self.env._("No CMIS folder is linked to this record."))
        # the users do not access the credentials of the backend
        backend = field.get_backend(self.env).sudo()
        repository = backend.get_cmis_repository()
        root = repository.get_object(root_id)
        return FolderContext(record, field, backend, repository, root)

    @api.model
    def _get_permissions(self, record):
        can_write = record.has_access("write")
        return {
            "can_create": can_write,
            "can_rename": can_write,
            "can_update_content": can_write,
            "can_delete": record.has_access("unlink"),
        }

    @api.model
    def _serialize(self, context, cmis_object):
        """Return the values of a CMIS object sent to the widget"""
        props = cmis_object.properties
        return {
            "id": cmis_object.id,
            "name": cmis_object.name,
            "is_folder": cmis_object.is_folder,
            "mimetype": cmis_object.mime_type or False,
            "title": props.get("cm:title") or "",
            "description": props.get("cmis:description") or "",
            "creation_date": props.get("cmis:creationDate"),
            "modification_date": props.get("cmis:lastModificationDate"),
            "last_modified_by": props.get("cmis:lastModifiedBy") or "",
            "version_label": cmis_object.version_label or "",
            "size": props.get("cmis:contentStreamLength"),
        }

    @api.model
    def _get_breadcrumbs(self, context, folder):
        """Return the folders from the root of the record to ``folder``"""
        crumbs = [folder]
        current = folder
        while not context.is_root(current) and current.parent_id:
            current = context.repository.get_object(current.parent_id)
            crumbs.insert(0, current)
        return [{"id": f.id, "name": f.name} for f in crumbs]

    @api.model
    def _check_name(self, context, name):
        name = (name or "").strip()
        backend = context.backend
        if backend.enable_sanitize_cmis_name:
            name = backend.sanitize_cmis_name(name)
        else:
            backend.is_valid_cmis_name(name, raise_if_invalid=True)
        if not name:
            raise UserError(self.env._("The name can not be empty."))
        return name

    # Operations

    @api.model
    def get_folder(self, model, res_id, field_name, folder_id=None):
        context = self._get_context(model, res_id, field_name)
        folder = context.get_folder(folder_id)
        children = []
        for child in context.repository.iter_children(folder.id):
            children.append(self._serialize(context, child))
            if len(children) >= DEFAULT_CHILDREN_LIMIT:
                break
        return {
            "folder": self._serialize(context, folder),
            "breadcrumbs": self._get_breadcrumbs(context, folder),
            "children": children,
            "permissions": self._get_permissions(context.record),
        }

    @api.model
    def create_folder(self, model, res_id, field_name, folder_id, name):
        context = self._get_context(model, res_id, field_name, "write")
        parent = context.get_folder(folder_id)
        folder = parent.create_folder(self._check_name(context, name))
        return self._serialize(context, folder)

    @api.model
    def upload(self, model, res_id, field_name, folder_id, files):
        """Create documents in a folder.

        :param files: list of (filename, content as bytes, mimetype)
        """
        context = self._get_context(model, res_id, field_name, "write")
        parent = context.get_folder(folder_id)
        documents = []
        for filename, content, mimetype in files:
            document = parent.create_document(
                self._check_name(context, filename), content, mimetype
            )
            documents.append(self._serialize(context, document))
        return documents

    @api.model
    def rename(self, model, res_id, field_name, object_id, name):
        context = self._get_context(model, res_id, field_name, "write")
        cmis_object = context.get_object(object_id)
        if context.is_root(cmis_object):
            raise UserError(self.env._("The folder of the record can not be renamed."))
        cmis_object.update_properties({"cmis:name": self._check_name(context, name)})
        return self._serialize(context, cmis_object)

    @api.model
    def update_content(self, model, res_id, field_name, object_id, file):
        """Replace the content of a document.

        :param file: (filename, content as bytes, mimetype)
        """
        context = self._get_context(model, res_id, field_name, "write")
        document = context.get_object(object_id)
        if not document.is_document:
            raise UserError(self.env._("%s is not a document.", document.name))
        filename, content, mimetype = file
        document = context.repository.set_content(
            document.id, content, mimetype, filename=filename
        )
        return self._serialize(context, document)

    @api.model
    def delete(self, model, res_id, field_name, object_id):
        context = self._get_context(model, res_id, field_name, "unlink")
        cmis_object = context.get_object(object_id)
        if context.is_root(cmis_object):
            raise UserError(self.env._("The folder of the record can not be deleted."))
        if cmis_object.is_folder:
            cmis_object.delete_tree()
        else:
            cmis_object.delete()
        return True

    @api.model
    def get_content(self, model, res_id, field_name, object_id):
        """Return the document and a streamed response of its content"""
        context = self._get_context(model, res_id, field_name)
        document = context.get_object(object_id)
        if not document.is_document:
            raise UserError(self.env._("%s is not a document.", document.name))
        response = context.repository.client.request(
            "GET",
            context.repository.root_folder_url,
            params={"objectId": document.id, "cmisselector": "content"},
            stream=True,
        )
        return document, response
