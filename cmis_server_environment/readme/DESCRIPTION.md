This module allows to configure the CMIS backends (module `cmis`) in the
server environment files of the `server_environment` module, instead of in
the database: the URL, the account and the timeout can differ between the
environments (development, staging, production) and the password is not
stored in the database.

The URLs of the Alfresco REST API and of Alfresco Share (module `cmis_alf`)
are also read from the environment when the module is installed.
