Add a section named after the CMIS backend (`cmis_backend.<backend name>`)
in the server environment configuration, for example:

``` ini
[cmis_backend.alfresco]
location = https://alfresco.example.com/alfresco/api/-default-/public/cmis/versions/1.1/browser/
username = odoo
password = secret
timeout = 60
initial_directory_write = /odoo
alfresco_api_location = https://alfresco.example.com/alfresco/api/-default-/public/alfresco/versions/1
share_location = https://alfresco.example.com/share
```

The keys defined in the configuration are read-only in Odoo, the others keep
the value of the backend in the database. See the documentation of the
`server_environment` module for the configuration files and the environment
variables (`SERVER_ENV_CONFIG`, `SERVER_ENV_CONFIG_SECRET`).
