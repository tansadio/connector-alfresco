# Copyright 2026 tansadio
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import werkzeug

from odoo import http
from odoo.exceptions import AccessError, UserError
from odoo.http import request

from odoo.addons.cmis_folder_widget.controllers.main import (
    CmisFolderWidgetController,
)


class CmisFolderWidgetAlfController(CmisFolderWidgetController):
    @http.route(
        "/cmis_folder_widget_alf/rendition",
        type="http",
        auth="user",
        methods=["GET"],
    )
    def rendition(self, model, res_id, field_name, object_id, **kwargs):
        try:
            document, response = request.env["cmis.folder.widget"].get_rendition(
                model, res_id, field_name, object_id
            )
        except (UserError, AccessError) as error:
            raise werkzeug.exceptions.Forbidden(str(error)) from error
        filename = document.name.rsplit(".", 1)[0] + ".pdf"
        return self._stream(filename, "application/pdf", response)
