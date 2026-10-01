# Copyright 2026 tansadio
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from .common import CmisFolderWidgetHttpCase


class TestTour(CmisFolderWidgetHttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        view = cls.env["ir.ui.view"].create(
            {
                "name": "cmis.folder.widget.test.model.form",
                "model": cls.record._name,
                "arch": """
                    <form>
                        <sheet>
                            <field name="name" />
                            <field name="cmis_folder" nolabel="1" />
                        </sheet>
                    </form>
                """,
            }
        )
        cls.action = cls.env["ir.actions.act_window"].create(
            {
                "name": "CMIS folder widget test",
                "res_model": cls.record._name,
                "view_mode": "form",
                "view_id": view.id,
            }
        )

    def test_tour(self):
        self.start_tour(
            f"/odoo/action-{self.action.id}/{self.record.id}",
            "cmis_folder_widget_tour",
            login="admin",
        )
        self.assertEqual(self.document.name, "renamed.txt")
        self.assertNotIn(
            "Tour folder", [c.name for c in self.repo._children(self.folder.id)]
        )
