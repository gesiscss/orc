import os
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
    """Check if a user is logged in by checking if cookie exists"""
    # FIXME cant we check if user logged in with JHub API?
    # by default, use the `jupyterhub-session-id` cookie, which is created under `/`
    cookie_name = os.getenv("JUPYTERHUB_COOKIE_NAME", "jupyterhub-session-id")
    return cookie_name in request.cookies


@app.route('/')
# @cache.cached(timeout=None)
def home():
    context = get_default_template_context()

    if user_logged_in():
        app.logger.info(f"User already logged in, redirecting to JupyterHub {context['gesishub_url']}")
        return redirect(context['gesishub_url'])

    binder_examples = [
        # {'headline': '',
        #  'repo_link': '',
        #  'who': '',
        #  'where': '',
        #  'description': '',
        #  'binder_link': '',
        #  'language': ''},
        {'headline': 'Welcome to GESIS Notebooks',
         'repo_link': 'https://github.com/gesiscss/notebooks_getting_started',
         'who': 'Arnim Bleier',
         'where': 'CSS, GESIS',
         'description': 'GESIS Notebooks is an online service for researchers in the Social Sciences to publish and execute data-driven research designs.',
         'binder_link': '/services/binder/v2/gh/gesiscss/notebooks_getting_started/master?urlpath=lab/tree/introduction_python.ipynb',
         'language': 'Python'},
        {'headline': 'Scientometrics Summer School',
         'repo_link': 'https://github.com/gesiscss/wikiwho_demo',
         'who': 'Vincent Traag',
         'where': 'Centre for Science and Technology Studies, Leiden University',
         'description': 'In these Notebooks, you will learn how to perform scientometric network analysis.',
         'binder_link': '/services/binder/v2/gh/CWTSLeiden/CSSS/master?filepath=01-basics.ipynb',
         'language': 'Python'},
        {'headline': 'Analytical Information Systems',
         'repo_link': 'https://github.com/wi3jmu/AIS_2019',
         'who': 'Matthias Griebel',
         'where': 'Julius Maximilian University of Würzburg',
         'description': 'Learn about the use of programming for data analysis, data management, and statistical analysis techniques.',
         'binder_link': '/services/binder/v2/gh/matjesg/AIS_2019/master?urlpath=lab/tree/notebooks/AIS_T01_SS19.ipynb',
         'language': 'R'},
        {'headline': 'Practical Introduction to Text Mining',
         'repo_link': 'https://github.com/gesiscss/ptm',
         'who': 'Arnim Bleier',
         'where': 'CSS, GESIS',
         'description': 'Introduction to Natural Language Processing with a special emphasis on the analysis of Job Advertisements',
         'binder_link': '/services/binder/v2/gh/gesiscss/ptm/master?filepath=index.ipynb',
         'language': 'R'},
        {'headline': 'RStan + Binder',
         'repo_link': 'https://github.com/arnim/RStan-Binder',
         'who': 'Arnim Bleier',
         'where': 'CSS, GESIS',
         'description': 'Files for running RStan on Binder',
         'binder_link': '/services/binder/v2/gh/arnim/RStan-Binder/master?urlpath=lab/tree/README.md',
         'language': 'R'},
        {'headline': 'GESIS DataDay 2020',
         'repo_link': 'https://github.com/gesiscss/gesis_dataday_20',
         'who': 'Arnim Bleier and Johannes Breuer',
         'where': 'CSS & DAS, GESIS',
         'description': 'Materials for GESIS DataDay 2020',
         'binder_link': '/services/binder/v2/gh/gesiscss/gesis_dataday_20/master?urlpath=lab',
         'language': 'R'},
        {'headline': 'compsoc',
         'repo_link': 'https://github.com/gesiscss/compsoc',
         'who': 'Haiko Lietz',
         'where': 'CSS, GESIS',
         'description': 'Notebooks for Computational Sociology',
         'binder_link': '/services/binder/v2/gh/gesiscss/compsoc/master',
         'language': 'Python'},
        # {'headline': 'Wiki-Impact',
        #  'repo_link': 'https://github.com/gesiscss/wikiwho_demo',
        #  'who': '',
        #  'where': '',
        #  'description': 'A demonstration of how to use the <a href="https://www.wikiwho.net">WikiWho service</a> to complement other external tools.',
        #  'binder_link': '/services/binder/v2/gh/gesiscss/wikiwho_demo/master?urlpath=%2Fapps%2F1.%20General%20Metadata%20of%20a%20Wikipedia%20Article.ipynb',
        #  'language': 'Python'},
        # {'headline': 'Python Data Science Handbook',
        #  'repo_link': 'https://github.com/jakevdp/PythonDataScienceHandbook',
        #  'who': '',
        #  'where': '',
        #  'description': '',
        #  'binder_link': '/services/binder/v2/gh/jakevdp/PythonDataScienceHandbook/master?filepath=notebooks%2FIndex.ipynb',
        #  'language': 'Python'},
        # {'headline': 'LIGO Binder',
        #  'repo_link': 'https://github.com/minrk/ligo-binder',
        #  'who': '',
        #  'where': '',
        #  'description': '',
        #  'binder_link': '/services/binder/v2/gh/minrk/ligo-binder/master?filepath=index.ipynb',
        #  'language': 'Python'},
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
