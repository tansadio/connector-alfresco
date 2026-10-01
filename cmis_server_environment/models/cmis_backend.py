# Copyright 2026 tansadio
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import fields, models

# fields of the backend read from the server environment, the ones of other
# modules (cmis_alf) only when they are installed
SERVER_ENV_FIELDS = (
    "location",
    "username",
    "password",
    "timeout",
    "initial_directory_write",
    "alfresco_api_location",
    "share_location",
)


class CmisBackend(models.Model):
    """The CMIS backends are configured in a section named after the backend:

    .. code-block:: ini

        [cmis_backend.alfresco]
        location = https://alfresco.example.com/alfresco/api/-default-/public/cmis/versions/1.1/browser/
        username = odoo
        password = secret
    """

    _name = "cmis.backend"
    _inherit = ["cmis.backend", "server.env.mixin"]

    # the default values (password included) are stored in this field: the
    # users can read the backends, not their credentials
    server_env_defaults = fields.Serialized(groups="base.group_system")

    @property
    def _server_env_fields(self):
        env_fields = super()._server_env_fields
        env_fields.update(
            {name: {} for name in SERVER_ENV_FIELDS if name in self._fields}
        )
        return env_fields
