This module provides the widget of the `cmis_folder` fields (see the
`cmis_field` module of [Alfodoo](https://github.com/acsone/alfodoo)): it
displays the content of the CMIS folder linked to a record and allows to
navigate in it, create folders, add documents (also by drag and drop),
preview, download, rename, update and delete them.

Unlike the `cmis_web` module of Alfodoo, the browser never calls the CMIS
server: all the operations are done by Odoo, with the account of the CMIS
backend, once checked that:

- the user has the required access rights on the record: read to browse,
  write to create, rename and update, delete to delete;
- the content is the folder of the record or one of its descendants (the
  paths are compared, a folder `Client A` does not give access to a folder
  `Client AB`);
- the folder of the record itself is not renamed or deleted.

The CMIS server does not need to be reachable from the browsers, and there is
no CORS configuration. The documents are displayed with the file viewer of
Odoo; the contents that could run scripts (html, svg...) are always
downloaded.
