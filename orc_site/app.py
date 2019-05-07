import os
from flask_caching import Cache
from flask import Flask, render_template

cache = Cache(config={'CACHE_TYPE': 'simple'})
app = Flask(__name__)
app.config['SERVER_NAME'] = os.getenv("FLASK_SERVER_NAME", "127.0.0.1:5000")
cache.init_app(app)


def get_default_template_context():
    staging = app.debug
    production = not app.debug
    site_url = 'https://notebooks{}.gesis.org'.format('-test' if staging else '')
    context = {
        'staging': staging,
        'production': production,
        'site_url': site_url,
        'version': 'beta',
        # 'shibboleth_entityID': f'{site_url}/shibboleth',

        'home_url': '/',
        'jhub_url': '/jupyter/',
        'gesis_login_url': f'{site_url}/Shibboleth.sso/Login?SAMLDS=1&'
                           f'target={site_url}/hub/login&'
                           f'entityID=https%3A%2F%2Fidp.gesis.org%2Fidp%2Fshibboleth',
        'bhub_url': '/binder/',
        'about_url': '/about/',
        'tou_url': '/terms_of_use/',
        'imprint_url': 'https://www.gesis.org/en/institute/imprint/',
        'data_protection_url': 'https://www.gesis.org/en/institute/data-protection/',
        'gesis_url': 'https://www.gesis.org/en/home/',
        'gallery_url': '/gallery/'
        # 'help_url': 'https://www.gesis.org/en/help/',
    }

    return context


@app.errorhandler(404)
def not_found(error):
    context = get_default_template_context()
    context.update({'status_code': error.code,
                    'status_message': error.name,
                    'message': error.description,
                    'active': None})
    return render_template('error.html', **context), 404


@app.route('/')
@cache.cached(timeout=None)
def home():
    context = get_default_template_context()
    site_url = context["site_url"]
    binder_examples = [
        {'headline': 'Wiki-Impact',
         'content': '',
         'binder_link': f'{site_url}/binder/v2/gh/gesiscss/wikiwho_demo/master?urlpath=%2Fapps%2F1.%20General%20Metadata%20of%20a%20Wikipedia%20Article.ipynb',
         'repo_link': 'https://github.com/gesiscss/wikiwho_demo'},
        {'headline': 'Python Data Science Handbook',
         'content': '',
         'binder_link': f'{site_url}/binder/v2/gh/jakevdp/PythonDataScienceHandbook/master?filepath=notebooks%2FIndex.ipynb',
         'repo_link': 'https://github.com/jakevdp/PythonDataScienceHandbook'},
        {'headline': 'LIGO Binder',
         'content': '',
         'binder_link': f'{site_url}/binder/v2/gh/minrk/ligo-binder/master?filepath=index.ipynb',
         'repo_link': 'https://github.com/minrk/ligo-binder'},
    ]
    context.update({'active': 'home', 'binder_examples': binder_examples})
    return render_template('home.html', **context)


@app.route('/login/')
def login():
    context = get_default_template_context()
    context.update({'active': 'jupyterhub'})
    return render_template('shibboleth_login.html', **context)


@app.route('/about/')
@cache.cached(timeout=None)
def about():
    context = get_default_template_context()
    context.update({'active': 'about'})
    return render_template('about.html', **context)


@app.route('/terms_of_use/')
@cache.cached(timeout=None)
def terms_of_use():
    context = get_default_template_context()
    context.update({'active': 'terms_of_use'})
    return render_template('terms_of_use.html', **context)
