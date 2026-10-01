/* Copyright 2026 tansadio
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html). */

import {Component, useRef, useState} from "@odoo/owl";
import {Dialog} from "@web/core/dialog/dialog";
import {useAutofocus} from "@web/core/utils/hooks";

/** Ask a name, to create a folder or rename a content */
export class CmisNameDialog extends Component {
    static template = "cmis_folder_widget.CmisNameDialog";
    static components = {Dialog};
    static props = {
        title: String,
        confirmLabel: String,
        name: {type: String, optional: true},
        confirm: Function,
        close: Function,
    };

    setup() {
        this.state = useState({name: this.props.name || ""});
        this.inputRef = useRef("input");
        useAutofocus({refName: "input"});
    }

    async onConfirm() {
        const name = this.state.name.trim();
        if (!name) {
            return;
        }
        await this.props.confirm(name);
        this.props.close();
    }

    onKeydown(ev) {
        if (ev.key === "Enter") {
            this.onConfirm();
        }
    }
}
