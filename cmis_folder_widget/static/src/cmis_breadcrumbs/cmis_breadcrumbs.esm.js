/* Adapted from the cmis_web module of Alfodoo
 * Copyright 2016-2023 ACSONE SA/NV (<http://acsone.eu>)
 * Copyright 2026 tansadio
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html). */

import {Component} from "@odoo/owl";

export class CmisBreadcrumbs extends Component {
    static template = "cmis_folder_widget.CmisBreadcrumbs";
    static props = {
        breadcrumbs: {
            type: Array,
            element: {type: Object, shape: {id: String, name: String}},
        },
        openFolder: Function,
    };
}
