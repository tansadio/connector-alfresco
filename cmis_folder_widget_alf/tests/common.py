# Copyright 2026 tansadio
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from unittest import mock

ODT = "application/vnd.oasis.opendocument.text"


class AlfrescoMixin:
    """Add an office document to the fake repository and mock the client of
    the Alfresco REST API"""

    def setUp(self):
        super().setUp()
        self.report = self.repo.add_document(self.folder, "report.odt", b"odt", ODT)
        self.alfresco = mock.MagicMock()
        self.alfresco.url = "http://alfresco/api"
        self.alfresco.timeout = 30
        rendition = mock.MagicMock(headers={"Content-Length": "4"})
        rendition.iter_content.return_value = [b"%PDF"]
        self.alfresco.session.request.return_value = rendition
        patcher = mock.patch(
            "odoo.addons.cmis_alf.models.cmis_backend.CmisBackend.get_alfresco_client",
            return_value=self.alfresco,
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        # no wait between the checks of the rendition status (patching
        # time.sleep would patch it for the whole process)
        interval = mock.patch(
            "odoo.addons.cmis_folder_widget_alf.models.cmis_folder_widget.POLL_INTERVAL",
            0,
        )
        interval.start()
        self.addCleanup(interval.stop)

    def rendition_status(self, *statuses):
        """The GET of the rendition returns the given statuses"""

        def request(method, path, **kwargs):
            if method == "GET":
                return {"id": "pdf", "status": next(status_iter)}
            return {}

        status_iter = iter(statuses)
        self.alfresco.request.side_effect = request
