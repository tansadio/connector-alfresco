/* Copyright 2026 tansadio
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html). */

import {registry} from "@web/core/registry";

const row = (name) => `.o_cmis_row:contains(${name})`;

registry.category("web_tour.tours").add("cmis_folder_widget_tour", {
    steps: () => [
        {
            content: "The content of the folder is displayed",
            trigger: `.o_cmis_folder ${row("doc.txt")}`,
        },
        {
            content: "Open the sub folder",
            trigger: row("Sub"),
            run: "click",
        },
        {
            content: "The breadcrumbs show the sub folder",
            trigger: ".o_cmis_folder .breadcrumb-item.active:contains(Sub)",
        },
        {
            content: "Go back to the folder of the record",
            trigger: ".o_cmis_folder .breadcrumb-item a:contains(Client A)",
            run: "click",
        },
        {
            content: "Create a folder",
            trigger: `.o_cmis_folder:has(${row("doc.txt")}) .o_cmis_create_folder`,
            run: "click",
        },
        {
            content: "Name the folder",
            trigger: ".modal input[type=text]",
            run: "edit Tour folder",
        },
        {
            trigger: ".modal .btn-primary:contains(Create)",
            run: "click",
        },
        {
            content: "The new folder is displayed",
            trigger: row("Tour folder"),
        },
        {
            content: "Open the actions of the document",
            trigger: `${row("doc.txt")} .o_cmis_more`,
            run: "click",
        },
        {
            trigger: ".o_cmis_rename",
            run: "click",
        },
        {
            trigger: ".modal input[type=text]",
            run: "edit renamed.txt",
        },
        {
            trigger: ".modal .btn-primary:contains(Rename)",
            run: "click",
        },
        {
            content: "The document is renamed",
            trigger: row("renamed.txt"),
        },
        {
            content: "Preview the document",
            trigger: `${row("renamed.txt")} .o_cmis_preview`,
            run: "click",
        },
        {
            content: "The file viewer displays the document",
            trigger: ".o-FileViewer",
        },
        {
            trigger: ".o-FileViewer-headerButton[aria-label='Close']",
            run: "click",
        },
        {
            content: "Delete the folder",
            trigger: `${row("Tour folder")} .o_cmis_more`,
            run: "click",
        },
        {
            trigger: ".o_cmis_delete",
            run: "click",
        },
        {
            trigger: ".modal .btn-primary:contains(Delete)",
            run: "click",
        },
        {
            content: "The folder is deleted",
            trigger: `.o_cmis_folder:has(${row("renamed.txt")}):not(:has(${row(
                "Tour folder"
            )}))`,
        },
    ],
});
