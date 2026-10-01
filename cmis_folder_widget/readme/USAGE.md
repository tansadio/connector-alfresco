Add a `cmis_folder` field to a model and display it in a form view:

``` python
from odoo import models

from odoo.addons.cmis_field.fields import CmisFolder


class ResPartner(models.Model):
    _inherit = "res.partner"

    cmis_folder = CmisFolder()
```

``` xml
<field name="cmis_folder" nolabel="1" colspan="2" />
```

The *Create folder in DMS* button creates the folder of the record, then its
content is managed in the form.
