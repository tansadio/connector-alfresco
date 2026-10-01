/* Copyright 2026 tansadio
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html). */

import {Component, useRef, useState} from "@odoo/owl";
import {Dialog} from "@web/core/dialog/dialog";

/** Select files, to add documents or update the content of a document */
export class CmisFileDialog extends Component {
    static template = "cmis_folder_widget.CmisFileDialog";
    static components = {Dialog};
    static props = {
        title: String,
        confirmLabel: String,
        multiple: {type: Boolean, optional: true},
        confirm: Function,
        close: Function,
    };

    setup() {
        this.inputRef = useRef("input");
        this.state = useState({count: 0});
    }

    onChange() {
        this.state.count = this.inputRef.el.files.length;
    }

    async onConfirm() {
        const files = this.inputRef.el.files;
        if (!files.length) {
            return;
        }
        await this.props.confirm(files);
        this.props.close();
    }
}
