/* Copyright 2026 tansadio
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html). */

import {CmisActions} from "@cmis_folder_widget/cmis_actions/cmis_actions.esm";
import {CmisFile} from "@cmis_folder_widget/cmis_file_model.esm";
import {patch} from "@web/core/utils/patch";

const RENDITION_ROUTE = "/cmis_folder_widget_alf/rendition";

patch(CmisFile.prototype, {
    /** Office documents are previewed from the PDF rendition of Alfresco */
    get hasRendition() {
        return this.data.preview_rendition === "pdf";
    },

    get isPdf() {
        return this.hasRendition || super.isPdf;
    },

    get urlRoute() {
        return this.hasRendition ? RENDITION_ROUTE : super.urlRoute;
    },
});

patch(CmisActions.prototype, {
    get hasMoreActions() {
        return Boolean(this.props.cmisObject.share_url) || super.hasMoreActions;
    },
});
