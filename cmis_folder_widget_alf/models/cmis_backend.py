# Copyright 2026 tansadio
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import fields, models


class CmisBackend(models.Model):
    _inherit = "cmis.backend"

    alfresco_share_links = fields.Boolean(
        "Links to Alfresco Share",
        help="Display in the CMIS folder widget a link to open the contents in "
        "Alfresco Share. The users need an Alfresco account to open them.",
    )
    alfresco_rendition_timeout = fields.Integer(
        "Preview generation timeout",
        default=15,
        help="Maximum time, in seconds, to wait for Alfresco to generate the PDF "
        "preview of a document",
    )
