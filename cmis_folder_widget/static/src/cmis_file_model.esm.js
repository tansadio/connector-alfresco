/* Copyright 2026 tansadio
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html). */

import {FileModelMixin} from "@web/core/file_viewer/file_model";

/**
 * A document of a CMIS folder, displayed by the Odoo file viewer. Its
 * content is served by Odoo (the browser never calls the CMIS server).
 */
export class CmisFile extends FileModelMixin(Object) {
    /**
     * @param {Object} data document as returned by /cmis_folder_widget/folder
     * @param {Object} routeParams model, res_id and field_name of the record
     */
    constructor(data, routeParams) {
        super();
        this.id = data.id;
        this.name = data.name;
        this.mimetype = data.mimetype || "application/octet-stream";
        this.type = "binary";
        this.routeParams = routeParams;
    }

    get urlRoute() {
        return "/cmis_folder_widget/content";
    }

    get urlQueryParams() {
        return {...this.routeParams, object_id: this.id};
    }

    get isText() {
        // Html could run scripts: only plain text is displayed
        return this.mimetype === "text/plain";
    }
}
