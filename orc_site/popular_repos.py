import requests
from datetime import datetime, timedelta

REPOS_TO_FILTER = [
    # 'gesiscss/binder-stats'
]

PROVIDER_PREFIXES = {
    'Git': 'git',
    'GitHub': 'gh',
    'GitLab': 'gl',
    # 'gist.github.com': 'gist',
}


def binder_url(provider, org, repo):
    provider_prefix = PROVIDER_PREFIXES.get(provider, '')
    if provider_prefix:
        return f'https://notebooks.gesis.org/binder/v2/{provider_prefix}/{org}/{repo}/master'
    return ''


def ts_to_dt(ts):
    return datetime.utcfromtimestamp(ts)


def get_launch_data(time_range='90d', filter_="{status='success'}"):
    # NOTE: increase() doesn't return first +1 (0->1)
    # query = f"increase(binderhub_launch_count_total{filter_}[{time_range}])"
    query = f"binderhub_launch_count_total{filter_}[{time_range}]"
    # print(query)
    resp = requests.get('https://notebooks.gesis.org/prometheus/api/v1/query',
                        params={'query': query})
    data = resp.json()['data']['result']
    return data


def process_launch_data(data):
    d = {}  # {repo: [repo, org, provider, [launches], repo_url, binder_url]}
    for container in data:
        # first get meta data
        repo_url = container['metric']['repo']
        provider = container['metric']['provider']
        provider_org_repo = repo_url.replace('https://', '').rstrip('.git').rsplit('/', 2)
        if len(provider_org_repo) == 2:
            # some repo urls (e.g. gist) don't contain org/user info
            provider, repo = provider_org_repo
            org = ''
        else:
            provider_, org, repo = provider_org_repo
        if f'{org}/{repo}' in REPOS_TO_FILTER:
            continue
        # detect changes of launch count
        # get ts of each increase of launch count
        launch_count_increases = []
        launch_count_prev = 0
        for ts, launch_count in container['values']:
            launch_count = int(launch_count)
            if launch_count != launch_count_prev:
                # assert launch_count > launch_count_prev
                launch_count_increases.append((ts, launch_count))
            launch_count_prev = launch_count

        if repo not in d:
            d[repo] = [repo, org, provider, [launch_count_increases], repo_url, binder_url(provider, org, repo)]
        else:
            # same repo can be launched on different instances (after a new deployment/update)
            d[repo][3].append(launch_count_increases)

    # sort and flatten launch_count_increases
    for repo, data in d.items():
        launch_count_increases_ = []
        count_prev = 0
        launch_count_increases = data[3]
        # sort with timestamp (of first element of each sub-list)
        launch_count_increases.sort(key=lambda x: x[0][0])
        for increase in launch_count_increases:
            for i in increase:
                launch_count_increases_.append((ts_to_dt(i[0]), i[1] + count_prev))
            count_prev = launch_count_increases_[-1][1]
        data[3] = launch_count_increases_

    #     print('Since', ts_to_dt(min(value_times)), 'in UTC')
    d = list(d.values())
    return d


def get_popular_repos(launch_data, time_range):
    if time_range.endswith('h'):
        p = {'hours': int(time_range.split('h')[0])}
    elif time_range.endswith('d'):
        p = {'days': int(time_range.split('d')[0])}
    else:
        raise ValueError('Time range must be in hours or days.')
    popular_repos = []
    time_delta = timedelta(**p)
    start_dt = datetime.utcnow() - time_delta
    for data in launch_data:
        # get the launch count just before time_range
        first_value = 0
        for dt, launch_count in data[3]:
            if dt < start_dt:
                first_value = launch_count
        # increase in launch count during time_range
        data[3] = launch_count - first_value
        if data[3] != 0:
            popular_repos.append(data)
    # sort according to launch count
    popular_repos.sort(key=lambda x: x[3], reverse=True)
    # print("Total number of launches: " + str(sum([i[3] for i in popular_repos])) + " in " + str(time_range))
    return popular_repos
