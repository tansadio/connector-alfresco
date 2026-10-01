/* Adapted from the cmis_web module of Alfodoo
 * Copyright 2016-2023 ACSONE SA/NV (<http://acsone.eu>)
 * Copyright 2026 tansadio
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html). */

import {Component, useState} from "@odoo/owl";
import {CheckBox} from "@web/core/checkbox/checkbox";
import {CmisActions} from "../cmis_actions/cmis_actions.esm";
import {Dropdown} from "@web/core/dropdown/dropdown";
import {DropdownItem} from "@web/core/dropdown/dropdown_item";
import {_t} from "@web/core/l10n/translation";
import {formatDateTime} from "@web/core/l10n/dates";

const {DateTime} = luxon;

const MIMETYPE_ICONS = {
    "application/pdf": "fa-file-pdf-o",
    "text/plain": "fa-file-text-o",
    "text/html": "fa-file-code-o",
    "application/json": "fa-file-code-o",
    "application/gzip": "fa-file-archive-o",
    "application/zip": "fa-file-archive-o",
};
const MIMETYPE_GROUP_ICONS = {
    image: "fa-file-image-o",
    audio: "fa-file-audio-o",
    video: "fa-file-video-o",
};

/** The contents of a CMIS folder */
export class CmisTable extends Component {
    static template = "cmis_folder_widget.CmisTable";
    static components = {CheckBox, CmisActions, Dropdown, DropdownItem};
    static props = {
        children: Array,
        permissions: Object,
        openFolder: Function,
        onPreview: Function,
        onDownload: Function,
        onRename: Function,
        onUpdateContent: Function,
        onDelete: Function,
    };

    setup() {
        this.state = useState({
            columns: [
                {name: "name", label: _t("Name"), active: true},
                {name: "title", label: _t("Title"), active: false},
                {name: "description", label: _t("Description"), active: true},
                {name: "modification_date", label: _t("Modified"), active: true},
                {name: "creation_date", label: _t("Created"), active: false},
                {name: "last_modified_by", label: _t("Modifier"), active: true},
            ],
            orderBy: "name",
            asc: true,
        });
    }

    get activeColumns() {
        return this.state.columns.filter((column) => column.active);
    }

    get sortedChildren() {
        const {orderBy, asc} = this.state;
        const value = (obj) => {
            const val = obj[orderBy];
            return typeof val === "string" ? val.toLowerCase() : val || 0;
        };
        // Folders first, then by the selected column
        return [...this.props.children].sort((a, b) => {
            if (a.is_folder !== b.is_folder) {
                return a.is_folder ? -1 : 1;
            }
            const [va, vb] = [value(a), value(b)];
            if (va === vb) {
                return 0;
            }
            return (va < vb ? -1 : 1) * (asc ? 1 : -1);
        });
    }

    sortBy(column) {
        if (this.state.orderBy === column.name) {
            this.state.asc = !this.state.asc;
        } else {
            this.state.orderBy = column.name;
            this.state.asc = true;
        }
    }

    sortIcon(column) {
        if (this.state.orderBy !== column.name) {
            return "fa fa-angle-down opacity-0 opacity-75-hover";
        }
        return this.state.asc ? "fa fa-angle-up" : "fa fa-angle-down";
    }

    toggleColumn(column) {
        column.active = !column.active;
    }

    iconClass(obj) {
        if (obj.is_folder) {
            return "fa fa-folder text-warning";
        }
        const mimetype = obj.mimetype || "";
        const icon =
            MIMETYPE_ICONS[mimetype] ||
            MIMETYPE_GROUP_ICONS[mimetype.split("/")[0]] ||
            "fa-file-o";
        return `fa ${icon}`;
    }

    formatValue(column, obj) {
        const value = obj[column.name];
        if (column.name.endsWith("_date")) {
            return value ? formatDateTime(DateTime.fromMillis(value)) : "";
        }
        return value || "";
    }

    onClickRow(obj) {
        if (obj.is_folder) {
            this.props.openFolder(obj.id);
        } else {
            this.props.onPreview(obj);
        }
    }
}
