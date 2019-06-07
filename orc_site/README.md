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
