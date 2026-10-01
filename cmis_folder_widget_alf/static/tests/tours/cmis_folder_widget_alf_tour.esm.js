/* Copyright 2026 tansadio
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html). */

import {registry} from "@web/core/registry";

const row = (name) => `.o_cmis_row:contains(${name})`;

registry.category("web_tour.tours").add("cmis_folder_widget_alf_tour", {
    steps: () => [
        {
            content: "Open the actions of the office document",
            trigger: `${row("report.odt")} .o_cmis_more`,
            run: "click",
        },
        {
            content: "A link opens the document in Alfresco Share",
            trigger: ".o_cmis_share_link[href*='document-details']",
        },
        {
            content: "Preview the office document",
            trigger: `${row("report.odt")} .o_cmis_preview`,
            run: "click",
        },
        {
            content: "The PDF rendition is displayed by the file viewer",
            trigger: ".o-FileViewer iframe[src*='cmis_folder_widget_alf%2Frendition']",
        },
    ],
});
