# Copyright 2026 tansadio
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "CMIS Folder Widget",
    "summary": "Browse and manage the CMIS folder of a record, through Odoo only",
    "version": "19.0.1.0.0",
    "category": "Document Management",
    "website": "https://github.com/tansadio/connector-alfresco",
    "author": "tansadio, ACSONE SA/NV",
    "maintainers": ["tansadio"],
    "license": "AGPL-3",
    "development_status": "Alpha",
    "depends": ["web", "cmis_field"],
    # both modules provide the widget of the cmis_folder fields
    "excludes": ["cmis_web"],
    "assets": {
        "web.assets_backend": [
            "cmis_folder_widget/static/src/**/*",
        ],
        "web.assets_tests": [
            "cmis_folder_widget/static/tests/tours/*",
        ],
    },
    "installable": True,
}
