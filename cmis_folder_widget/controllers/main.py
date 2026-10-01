# Copyright 2026 tansadio
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging

import werkzeug

from odoo import http
from odoo.exceptions import AccessError, UserError
from odoo.http import content_disposition, request

_logger = logging.getLogger(__name__)

CHUNK_SIZE = 64 * 1024

# contents displayed in the browser; the others are always downloaded since
# a document (html, svg...) could run scripts on the Odoo domain
INLINE_MIMETYPES = {
    "application/pdf",
    "audio/mpeg",
    "image/bmp",
    "image/gif",
    "image/jpeg",
    "image/png",
    "image/tiff",
    "image/webp",
    "text/plain",
    "video/mp4",
    "video/webm",
}


class CmisFolderWidgetController(http.Controller):
    @property
    def _widget(self):
        return request.env["cmis.folder.widget"]

    @http.route("/cmis_folder_widget/folder", type="jsonrpc", auth="user")
    def folder(self, model, res_id, field_name, folder_id=None):
        return self._widget.get_folder(model, res_id, field_name, folder_id)

    @http.route("/cmis_folder_widget/create_folder", type="jsonrpc", auth="user")
    def create_folder(self, model, res_id, field_name, folder_id, name):
        return self._widget.create_folder(model, res_id, field_name, folder_id, name)

    @http.route("/cmis_folder_widget/rename", type="jsonrpc", auth="user")
    def rename(self, model, res_id, field_name, object_id, name):
        return self._widget.rename(model, res_id, field_name, object_id, name)

    @http.route("/cmis_folder_widget/delete", type="jsonrpc", auth="user")
    def delete(self, model, res_id, field_name, object_id):
        return self._widget.delete(model, res_id, field_name, object_id)

    @staticmethod
    def _read_file(file):
        return (file.filename, file.read(), file.mimetype or "application/octet-stream")

    def _json_error(self, error):
        return request.make_json_response({"error": str(error)}, status=400)

    @http.route(
        "/cmis_folder_widget/upload", type="http", auth="user", methods=["POST"]
    )
    def upload(self, model, res_id, field_name, folder_id, **kwargs):
        files = [self._read_file(f) for f in request.httprequest.files.getlist("ufile")]
        try:
            result = self._widget.upload(model, res_id, field_name, folder_id, files)
        except (UserError, AccessError) as error:
            return self._json_error(error)
        return request.make_json_response(result)

    @http.route(
        "/cmis_folder_widget/update_content",
        type="http",
        auth="user",
        methods=["POST"],
    )
    def update_content(self, model, res_id, field_name, object_id, **kwargs):
        file = request.httprequest.files.get("ufile")
        if not file:
            return self._json_error(request.env._("No file provided."))
        try:
            result = self._widget.update_content(
                model, res_id, field_name, object_id, self._read_file(file)
            )
        except (UserError, AccessError) as error:
            return self._json_error(error)
        return request.make_json_response(result)

    @http.route(
        "/cmis_folder_widget/content", type="http", auth="user", methods=["GET"]
    )
    def content(self, model, res_id, field_name, object_id, download=None, **kwargs):
        try:
            document, response = self._widget.get_content(
                model, res_id, field_name, object_id
            )
        except (UserError, AccessError) as error:
            raise werkzeug.exceptions.Forbidden(str(error)) from error
        mimetype = document.mime_type or "application/octet-stream"
        inline = not download and mimetype in INLINE_MIMETYPES
        headers = {
            "Content-Type": mimetype,
            "Content-Disposition": content_disposition(
                document.name, "inline" if inline else "attachment"
            ),
            "X-Content-Type-Options": "nosniff",
            "Cache-Control": "private, no-store",
        }
        length = response.headers.get("Content-Length")
        if length:
            headers["Content-Length"] = length
        return werkzeug.Response(
            response.iter_content(CHUNK_SIZE),
            headers=headers,
            direct_passthrough=True,
        )
