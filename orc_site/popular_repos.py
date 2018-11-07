import requests


def binder_url(org, repo):
    """

    :param org:
    :param repo:
    :return:
    """
    return f'https://notebooks.gesis.org/binder/v2/gh/{org}/{repo}/master'


def query(time_range, filter="{status='success'}"):
    """

    :param time_range:
    :param filter:
    :return:
    """
    query = f"binderhub_launch_count_total{filter}[{time_range}]"
    # print(query)
    resp = requests.get('https://notebooks.gesis.org/prometheus/api/v1/query', params={'query': query})
    data = resp.json()['data']['result']
    return data


def process_data(data):
    d = {}  # {repo: [repo, org, provider, launches, repo_url, binder_url]}
    for container in data:
        repo_url = container['metric']['repo']
        provider = container['metric']['provider']
        provider_, org, repo = repo_url.replace('https://', '').rsplit('/', 2)

        # calculate number of launches for each repo = max value in time
        launches = max([int(i[1]) for i in container['values']])
        if repo not in d:
            d[repo] = [repo, org, provider, launches, repo_url, binder_url(org, repo)]
        else:
            # same repo can be launched on different instances (after a new deployment/update)
            d[repo][3] += launches
    return d


def get_popular_repos(time_range):
    data = query(f'{time_range}')
    data = process_data(data)
    data = sorted(data.values(), key=lambda x: x[3], reverse=True)
    return data

