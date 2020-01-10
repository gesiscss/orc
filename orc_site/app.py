import os
import requests
from flask_caching import Cache
from flask import Flask, render_template, request, redirect

cache = Cache(config={'CACHE_TYPE': 'simple'})

static_folder = "../load_balancer/static" if os.getenv("FLASK_ENV") == "development" else "static"
app = Flask(__name__, static_folder=static_folder)
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
    context = {
        'version': 'beta',
        'home_url': '/',
        'gesishub_url': '/hub/',
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
    if os.getenv("GESISHUB_UNDER_MAINTENANCE", "false") == "true" and \
        (request.path.startswith('/hub') or
         request.path.startswith('/user') or
         request.path.startswith('/services')):
        status_code = None
        status_message = "Under maintenance"
        message = "This service will be back soon."
        active = "hub"
        response_code = 503
        context.update({'user': None})
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


def user_logged_in():
    """Check if a user is logged in"""
    cookie_name = os.getenv("JUPYTERHUB_COOKIE_NAME", "jupyterhub-session-id")
    cookie_value = request.cookies.get(cookie_name)
    app.logger.info(f"#######1 {request.host}")
    if cookie_value:
        app.logger.info(f"#######2 {request.host}")
        api_url = f"https://{request.host}/hub/api/authorizations/cookie/{cookie_name}/{cookie_value}"
        token = os.getenv("JUPYTERHUB_API_TOKEN")
        headers = {'Authorization': 'token %s' % token}
        try:
            r = requests.get(api_url, headers=headers, timeout=1)
        except requests.exceptions.Timeout:
            return False
        else:
            if r.status_code == 200:
                return True
    return False


@app.route('/')
# @cache.cached(timeout=None)
def home():
    context = get_default_template_context()

    if user_logged_in():
        app.logger.info(f"User already logged in, redirecting to JupyterHub {context['gesishub_url']}")
        return redirect(context['gesishub_url'])

    binder_examples = [
        {'headline': 'Wiki-Impact',
         'content': '',
         'binder_link': '/binder/v2/gh/gesiscss/wikiwho_demo/master?urlpath=%2Fapps%2F1.%20General%20Metadata%20of%20a%20Wikipedia%20Article.ipynb',
         'repo_link': 'https://github.com/gesiscss/wikiwho_demo'},
        {'headline': 'Python Data Science Handbook',
         'content': '',
         'binder_link': '/binder/v2/gh/jakevdp/PythonDataScienceHandbook/master?filepath=notebooks%2FIndex.ipynb',
         'repo_link': 'https://github.com/jakevdp/PythonDataScienceHandbook'},
        {'headline': 'LIGO Binder',
         'content': '',
         'binder_link': '/binder/v2/gh/minrk/ligo-binder/master?filepath=index.ipynb',
         'repo_link': 'https://github.com/minrk/ligo-binder'},
    ]
    context.update({'active': 'home',
                    'binder_examples': binder_examples,
                    })
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
