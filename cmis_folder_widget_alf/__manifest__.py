# Copyright 2026 tansadio
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "CMIS Folder Widget for Alfresco",
    "summary": "Preview office documents as PDF and open the contents in Share",
    "version": "19.0.1.0.0",
    "category": "Document Management",
    "website": "https://github.com/tansadio/connector-alfresco",
    "author": "tansadio",
    "maintainers": ["tansadio"],
    "license": "AGPL-3",
    "development_status": "Alpha",
    "depends": ["cmis_folder_widget", "cmis_alf"],
    "data": ["views/cmis_backend.xml"],
    "assets": {
        "web.assets_backend": [
            "cmis_folder_widget_alf/static/src/**/*",
        ],
        "web.assets_tests": [
            "cmis_folder_widget_alf/static/tests/tours/*",
        ],
    },
    "auto_install": True,
    "installable": True,
}
