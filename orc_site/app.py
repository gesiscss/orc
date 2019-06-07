import os
from flask_caching import Cache
from flask import Flask, render_template, request

cache = Cache(config={'CACHE_TYPE': 'simple'})
app = Flask(__name__)
if not app.debug:
    # configure flask.app logger
    import logging
    # sh = logging.StreamHandler()
    # formatter = logging.Formatter('[%(asctime)s] %(levelname)s in %(module)s: %(message)s')
    # sh.setFormatter(formatter)
    # app.logger.handlers = [sh]
    app.logger.setLevel(logging.INFO)
    # reverse proxy fix
    from werkzeug.middleware.proxy_fix import ProxyFix
    app.wsgi_app = ProxyFix(app.wsgi_app)
app.config['SERVER_NAME'] = os.getenv("FLASK_SERVER_NAME",
                                      "127.0.0.1:5000" if app.debug else "0.0.0.0:5000")
cache.init_app(app)


def get_default_template_context():
    production = bool(os.getenv("PRODUCTION_SERVER", False))
    staging = not production
    site_url = 'https://notebooks{}.gesis.org'.format('-test' if staging else '')
    context = {
        'staging': staging,
        'production': production,
        'site_url': site_url,
        'version': 'beta',
        'home_url': '/',
        'gesishub_url': '/jupyter/',
        'gesisbinder_url': '/binder/',
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
    if os.getenv("JHUB_UNDER_MAINTENANCE", "false") == "true" and \
       request.path in ['/jupyter/', '/jupyter']:
        status_code = None
        status_message = "Under maintenance"
        message = "This service will be back soon."
        active = "jupyterhub"
        response_code = 503
    else:
        status_code = error.code
        status_message = error.name
        message = error.description
        active = None
        response_code = 404
    context.update({'status_code': status_code,
                    'status_message': status_message,
                    'message': message,
                    'active': active})
    return render_template('error.html', **context), response_code


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
