import os
from flask import Flask, render_template, abort
from .popular_repos import get_launch_data, process_launch_data, get_popular_repos
from .utilities import get_created_by_gesis
from copy import deepcopy
# app = Flask(__name__, template_folder='../templates/orc_site')
app = Flask(__name__)

staging = os.environ.get('DEPLOYMENT_ENV') == 'staging'
production = os.environ.get('DEPLOYMENT_ENV') == 'production'
site_url = 'https://notebooks{}.gesis.org'.format('-test' if staging else '')

context = {
    'staging': staging,
    'production': production,
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


@app.errorhandler(404)
def not_found(error):
    context.update({'status_code': error.code,
                    'status_message': error.name,
                    'message': error.description,
                    'active': None})
    return render_template('error.html', **context), 404


@app.route('/')
def home():
    binder_examples = [
        {'headline': 'Girls Day Hackathon',
         'content': '',
         'binder_link': f'{site_url}/binder/v2/gh/gesiscss/workshop_girls_day/master',
         'repo_link': 'https://github.com/gesiscss/workshop_girls_day'},
        {'headline': 'Python Data Science Handbook',
         'content': '',
         'binder_link': f'{site_url}/binder/v2/gh/gesiscss/PythonDataScienceHandbook/master',
         'repo_link': 'https://github.com/gesiscss/PythonDataScienceHandbook'},
        {'headline': 'LIGO Binder',
         'content': '',
         'binder_link': f'{site_url}/binder/v2/gh/minrk/ligo-binder/master',
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
    # get all launch count data (in last 90 days)
    launch_data = get_launch_data()
    launch_data = process_launch_data(launch_data)

    popular_repos_all = [
        (1, 'Last 24 hours', get_popular_repos(deepcopy(launch_data), '24h'), '24h', ),
        (2, 'Last week', get_popular_repos(deepcopy(launch_data), '7d'), '7d', ),
        (3, 'Last 30 days', get_popular_repos(deepcopy(launch_data), '30d'), '30d', ),
        (4, 'Last 60 days', get_popular_repos(deepcopy(launch_data), '60d'), '60d', ),
    ]

    created_by_gesis = get_created_by_gesis()

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
    # get all launch count data (in last 90 days)
    launch_data = get_launch_data()
    launch_data = process_launch_data(launch_data)
    context.update({'active': 'gallery',
                    'title': titles[time_range],
                    'popular_repos': get_popular_repos(launch_data, time_range)})
    return render_template('gallery/popular_repos.html', **context)


def run_app():
    app.run(debug=False, host='0.0.0.0')


main = run_app

if __name__ == '__main__':
    main()

