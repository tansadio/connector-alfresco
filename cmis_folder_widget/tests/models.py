# Copyright 2026 tansadio
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

# DON'T IMPORT THIS MODULE IN INIT TO AVOID THE CREATION OF THE MODELS
# DEFINED FOR TESTS INTO YOUR ODOO INSTANCE

from odoo import fields, models

from odoo.addons.cmis_field.fields import CmisFolder


class CmisFolderWidgetTestModel(models.Model):
    _name = "cmis.folder.widget.test.model"
    _description = "cmis.folder.widget.test.model Fake Model"

    name = fields.Char(required=True)
    cmis_folder = CmisFolder(backend_name="cmis_folder_widget_test")
