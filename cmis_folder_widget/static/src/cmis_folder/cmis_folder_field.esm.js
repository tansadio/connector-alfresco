/* Adapted from the cmis_web module of Alfodoo
 * Copyright 2016-2023 ACSONE SA/NV (<http://acsone.eu>)
 * Copyright 2026 tansadio
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html). */

import {Component, onWillStart, onWillUpdateProps, useState} from "@odoo/owl";
import {CmisBreadcrumbs} from "../cmis_breadcrumbs/cmis_breadcrumbs.esm";
import {CmisFile} from "../cmis_file_model.esm";
import {CmisFileDialog} from "../dialogs/file_dialog.esm";
import {CmisNameDialog} from "../dialogs/name_dialog.esm";
import {CmisTable} from "../cmis_table/cmis_table.esm";
import {ConfirmationDialog} from "@web/core/confirmation_dialog/confirmation_dialog";
import {_t} from "@web/core/l10n/translation";
import {browser} from "@web/core/browser/browser";
import {post} from "@web/core/network/http_service";
import {registry} from "@web/core/registry";
import {rpc} from "@web/core/network/rpc";
import {standardFieldProps} from "@web/views/fields/standard_field_props";
import {useFileViewer} from "@web/core/file_viewer/file_viewer_hook";
import {useService} from "@web/core/utils/hooks";

/**
 * Widget of the cmis_folder fields: browse and manage the CMIS folder of the
 * record. All the requests go to Odoo, which checks the access rights and
 * calls the CMIS server with the account of the backend.
 */
export class CmisFolderField extends Component {
    static template = "cmis_folder_widget.CmisFolderField";
    static components = {CmisBreadcrumbs, CmisTable};
    static props = {...standardFieldProps};

    setup() {
        this.dialog = useService("dialog");
        this.notification = useService("notification");
        this.ui = useService("ui");
        this.fileViewer = useFileViewer();
        this.dragCount = 0;
        this.state = useState({
            loading: false,
            error: false,
            folder: null,
            breadcrumbs: [],
            children: [],
            permissions: {},
            dragging: false,
        });
        onWillStart(() => this.load());
        onWillUpdateProps(async (nextProps) => {
            const value = nextProps.record.data[nextProps.name];
            if (value !== this.loadedValue) {
                await this.load(null, nextProps);
            }
        });
    }

    get fieldDescription() {
        return this.props.record.fields[this.props.name];
    }

    get backendError() {
        const backend = this.fieldDescription.backend || {};
        return backend.backend_error || false;
    }

    get value() {
        return this.props.record.data[this.props.name];
    }

    get canCreateRoot() {
        return (
            !this.value &&
            this.fieldDescription.allow_create &&
            !this.props.readonly &&
            !this.backendError
        );
    }

    routeParams(props = this.props) {
        return {
            model: props.record.resModel,
            res_id: props.record.resId,
            field_name: props.name,
        };
    }

    async load(folderId = null, props = this.props) {
        const value = props.record.data[props.name];
        this.loadedValue = value;
        if (!value || !props.record.resId || this.backendError) {
            Object.assign(this.state, {folder: null, children: [], error: false});
            return;
        }
        this.state.loading = true;
        try {
            const result = await rpc("/cmis_folder_widget/folder", {
                ...this.routeParams(props),
                folder_id: folderId,
            });
            Object.assign(this.state, result, {error: false});
        } catch (error) {
            this.state.error = error.data?.message || error.message || String(error);
        } finally {
            this.state.loading = false;
        }
    }

    reload() {
        return this.load(this.state.folder && this.state.folder.id);
    }

    async withBlockedUI(callback) {
        this.ui.block();
        try {
            return await callback();
        } finally {
            this.ui.unblock();
        }
    }

    // Folder of the record

    async createRootFolder() {
        await this.props.record.save();
        await this.withBlockedUI(() =>
            rpc("/web/cmis/field/create_value", {
                model_name: this.props.record.resModel,
                res_id: this.props.record.resId,
                field_name: this.props.name,
            })
        );
        await this.props.record.load();
    }

    // Navigation

    openFolder(folderId) {
        return this.load(folderId);
    }

    // Documents

    async uploadFiles(files) {
        if (!files.length) {
            return;
        }
        const formData = new FormData();
        for (const [key, value] of Object.entries(this.routeParams())) {
            formData.append(key, value);
        }
        formData.append("folder_id", this.state.folder.id);
        formData.append("csrf_token", odoo.csrf_token);
        for (const file of files) {
            formData.append("ufile", file);
        }
        const result = await this.withBlockedUI(() =>
            post("/cmis_folder_widget/upload", formData)
        );
        if (result.error) {
            this.notification.add(result.error, {type: "danger"});
        }
        await this.reload();
    }

    onClickAddDocument() {
        this.dialog.add(CmisFileDialog, {
            title: _t("Add documents"),
            confirmLabel: _t("Add"),
            multiple: true,
            confirm: (files) => this.uploadFiles(files),
        });
    }

    onClickCreateFolder() {
        this.dialog.add(CmisNameDialog, {
            title: _t("Create a folder"),
            confirmLabel: _t("Create"),
            confirm: async (name) => {
                await this.withBlockedUI(() =>
                    rpc("/cmis_folder_widget/create_folder", {
                        ...this.routeParams(),
                        folder_id: this.state.folder.id,
                        name,
                    })
                );
                await this.reload();
            },
        });
    }

    newCmisFile(obj) {
        return new CmisFile(obj, this.routeParams());
    }

    onPreview(obj) {
        const files = this.state.children
            .filter((child) => !child.is_folder)
            .map((child) => this.newCmisFile(child));
        const file = files.find((f) => f.id === obj.id);
        if (file.isViewable) {
            this.fileViewer.open(file, files);
        } else {
            this.onDownload(obj);
        }
    }

    onDownload(obj) {
        browser.open(this.newCmisFile(obj).downloadUrl, "_blank");
    }

    onRename(obj) {
        this.dialog.add(CmisNameDialog, {
            title: _t("Rename %s", obj.name),
            confirmLabel: _t("Rename"),
            name: obj.name,
            confirm: async (name) => {
                if (name === obj.name) {
                    return;
                }
                await rpc("/cmis_folder_widget/rename", {
                    ...this.routeParams(),
                    object_id: obj.id,
                    name,
                });
                await this.reload();
            },
        });
    }

    onUpdateContent(obj) {
        this.dialog.add(CmisFileDialog, {
            title: _t("Update the content of %s", obj.name),
            confirmLabel: _t("Update"),
            confirm: async (files) => {
                const formData = new FormData();
                for (const [key, value] of Object.entries(this.routeParams())) {
                    formData.append(key, value);
                }
                formData.append("object_id", obj.id);
                formData.append("csrf_token", odoo.csrf_token);
                formData.append("ufile", files[0]);
                const result = await this.withBlockedUI(() =>
                    post("/cmis_folder_widget/update_content", formData)
                );
                if (result.error) {
                    this.notification.add(result.error, {type: "danger"});
                }
                await this.reload();
            },
        });
    }

    onDelete(obj) {
        this.dialog.add(ConfirmationDialog, {
            title: _t("Delete"),
            body: obj.is_folder
                ? _t('Delete the folder "%s" and all its content?', obj.name)
                : _t('Delete "%s"?', obj.name),
            confirmLabel: _t("Delete"),
            confirm: async () => {
                await rpc("/cmis_folder_widget/delete", {
                    ...this.routeParams(),
                    object_id: obj.id,
                });
                await this.reload();
            },
            // Displays the cancel button, which closes the dialog
            cancel: () => true,
        });
    }

    // Drag and drop

    get canDrop() {
        return Boolean(this.state.folder && this.state.permissions.can_create);
    }

    onDragenter() {
        if (this.canDrop && this.dragCount++ === 0) {
            this.state.dragging = true;
        }
    }

    onDragleave() {
        if (this.canDrop && --this.dragCount === 0) {
            this.state.dragging = false;
        }
    }

    onDrop(ev) {
        this.dragCount = 0;
        this.state.dragging = false;
        if (this.canDrop) {
            this.uploadFiles(ev.dataTransfer.files);
        }
    }
}

export const cmisFolderField = {
    component: CmisFolderField,
    displayName: _t("CMIS Folder"),
    supportedTypes: ["cmis_folder"],
};

registry.category("fields").add("cmis_folder", cmisFolderField);
