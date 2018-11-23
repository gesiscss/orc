import os
from flask import Flask, render_template, abort
from .popular_repos import get_popular_repos
# app = Flask(__name__, template_folder='../templates/orc_site')
app = Flask(__name__)






context = {
    'version': 'beta',
    'test_version': 'test-beta',
    'home_url': '/',
    'jhub_url': '/jupyter/',
    'gesis_login_url': 'https://notebooks{}.gesis.org/Shibboleth.sso/Login?SAMLDS=1&'
                       'target=https://notebooks{}.gesis.org/jupyter/hub/login&'
                       'entityID=https%3A%2F%2Fidp.gesis.org%2Fidp%2Fshibboleth'.
                       format(*['-test', '-test'] if os.environ.get('DEPLOYMENT_ENV') == 'staging' else ['', '']),
    'bhub_url': '/binder/',
    'about_url': '/about/',
    'tou_url': '/terms_of_use/',
    'imprint_url': 'https://www.gesis.org/en/institute/imprint/',
    'data_protection_url': 'https://www.gesis.org/en/institute/data-protection/',
    'contact_url': 'mailto:notebooks@gesis.org',
    'gesis_url': 'https://www.gesis.org/en/home/',
    'help_url': 'https://www.gesis.org/en/help/',
    'shibboleth_entityID': 'https://notebooks.gesis.org/shibboleth',
    'test_shibboleth_entityID': 'https://notebooks-test.gesis.org/shibboleth',
    'is_staging': os.environ.get('DEPLOYMENT_ENV') == 'staging',
    'is_production': os.environ.get('DEPLOYMENT_ENV') == 'production',
    'gallery_url': '/gallery/'
}


@app.errorhandler(404)
def not_found(error):
    context.update({'status_code': error.code,
                    'status_message': error.name,
                    'message': error.description,
                    'active': None})
    return render_template('error.html', **context), 404


@app.route('/')
def home():
    domain = 'https://notebooks{}.gesis.org'.format('-test' if os.environ.get('DEPLOYMENT_ENV') == 'staging' else '')
    binder_examples = [
        {'headline': 'Girls Day Hackathon',
         'content': '',
         'binder_link': '{}/binder/v2/gh/gesiscss/workshop_girls_day/master'.format(domain),
         'repo_link': 'https://github.com/gesiscss/workshop_girls_day'},
        {'headline': 'Python Data Science Handbook',
         'content': '',
         'binder_link': '{}/binder/v2/gh/gesiscss/PythonDataScienceHandbook/master'.format(domain),
         'repo_link': 'https://github.com/gesiscss/PythonDataScienceHandbook'},
        {'headline': 'LIGO Binder',
         'content': '',
         'binder_link': '{}/binder/v2/gh/minrk/ligo-binder/master'.format(domain),
         'repo_link': 'https://github.com/minrk/ligo-binder'},
    ]
    context.update({'active': 'home', 'binder_examples': binder_examples})
    return render_template('home.html', **context)


@app.route('/login/')
def login():
    context.update({'active': 'login'})
    return render_template('shibboleth_login.html', **context)


@app.route('/about/')
def about():
    context.update({'active': 'about'})
    return render_template('about.html', **context)


@app.route('/terms_of_use/')
def terms_of_use():
    context.update({'active': 'terms_of_use'})
    return render_template('terms_of_use.html', **context)


@app.route('/gallery/')
def gallery():
    popular_repos_all = [
        (1, 'Last 24 hours', get_popular_repos('24h'), '24h', ),
        (2, 'Last week', get_popular_repos('7d'), '7d', ),
        (3, 'Last 30 days', get_popular_repos('30d'), '30d', ),
        (4, 'Last 60 days', get_popular_repos('60d'), '60d', ),
    ]

    created_by_gesis = [
        ('ptm', 'https://github.com/gesiscss/ptm', 'gesiscss', 'GitHub',
         'https://notebooks.gesis.org/binder/v2/gh/gesiscss/ptm/master?filepath=index.ipynb',
         'Introduction to Natural Language Processing with a special emphasis on the analysis of Job Advertisements', ),
        ('workshop_girls_day', 'https://github.com/gesiscss/workshop_girls_day', 'gesiscss', 'GitHub',
         'https://notebooks.gesis.org/binder/v2/gh/gesiscss/workshop_girls_day/master',
         '', ),
        ('gesis-meta-analysis-2018', 'https://github.com/berndweiss/gesis-meta-analysis-2018', 'berndweiss', 'GitHub',
         'https://notebooks.gesis.org/binder/v2/gh/berndweiss/gesis-meta-analysis-2018/master',
         'GESIS Summer School in Survey Methodology 2018: Meta-Analysis in Social Research and Survey Methodology', ),
        ('wikiwho_tutorial', 'https://github.com/gesiscss/wikiwho_tutorial', 'gesiscss', 'GitHub',
         'https://notebooks.gesis.org/binder/v2/gh/gesiscss/wikiwho_tutorial/master',
         'A simple tutorial for WikiWho that uses the wikiwho_wrapper', ),
        ('flow', 'https://github.com/gesiscss/flow', 'gesiscss', 'GitHub',
         'https://notebooks.gesis.org/binder/v2/gh/gesiscss/flow/master',
         'High-resolution audience research on local passenger traffic in Saxony, Germany', ),
    ]

    context.update({'active': 'gallery',
                    'popular_repos_all': popular_repos_all,
                    'created_by_gesis': created_by_gesis,
                    })
    return render_template('gallery/gallery.html', **context)


@app.route('/gallery/popular_repos/<string:time_range>')
def popular_repos(time_range):
    titles = {'24h': 'Popular repositories in last 24 hours',
              '7d': 'Popular repositories in last week',
              '30d': 'Popular repositories in last 30 days',
              '60d': 'Popular repositories in last 60 days'}
    if time_range not in titles:
        abort(404)
    context.update({'active': 'gallery',
                    'title': titles[time_range],
                    'popular_repos': get_popular_repos(time_range)})
    return render_template('gallery/popular_repos.html', **context)


def run_app():
    app.run(debug=False, host='0.0.0.0')


main = run_app

if __name__ == '__main__':
    main()
