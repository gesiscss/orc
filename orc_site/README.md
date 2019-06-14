An app to serve ORC project static files and base pages, such as home and about.

## How to run locally

```bash
git clone git@github.com:gesiscss/orc.git
cd orc/orc_site

# create a virtual enviroment.

pip install -r requirements.txt

export FLASK_APP=app.py
export FLASK_ENV=development

flask run
```

## Shibboleth embedded discovery service (EDS)

Shibboleth EDS documentation: https://wiki.shibboleth.net/confluence/display/EDS10/1.+Overview

This files are downloaded from: https://shibboleth.net/downloads/embedded-discovery-service/latest/