/* Adapted from the cmis_web module of Alfodoo
 * Copyright 2016-2023 ACSONE SA/NV (<http://acsone.eu>)
 * Copyright 2026 tansadio
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html). */

import {Component} from "@odoo/owl";
import {Dropdown} from "@web/core/dropdown/dropdown";
import {DropdownItem} from "@web/core/dropdown/dropdown_item";

/** Actions available on a content of the folder */
export class CmisActions extends Component {
    static template = "cmis_folder_widget.CmisActions";
    static components = {Dropdown, DropdownItem};
    static props = {
        cmisObject: Object,
        permissions: Object,
        onPreview: Function,
        onDownload: Function,
        onRename: Function,
        onUpdateContent: Function,
        onDelete: Function,
    };

    get hasMoreActions() {
        const {permissions, cmisObject} = this.props;
        return (
            permissions.can_rename ||
            (permissions.can_update_content && !cmisObject.is_folder) ||
            permissions.can_delete
        );
    }
}
