import pandas as pd
import requests
from datetime import datetime


def binder_url(org, repo):
    """

    :param org:
    :param repo:
    :return:
    """
    return f'https://notebooks.gesis.org/binder/v2/gh/{org}/{repo}/master'


def ts_to_dt(ts):
    """

    :param ts:
    :return:
    """
    return datetime.utcfromtimestamp(ts)


def query(time_range):
    """

    :param time_range:
    :return:
    """
    query = 'binderhub_launch_time_seconds_count{}[{}]'
    query_selectors = "{status='success'}"
    query = query.format(query_selectors, time_range)
    print(query)
    resp = requests.get('https://notebooks.gesis.org/prometheus/api/v1/query', params={'query': query})
    data = resp.json()['data']['result']
    return data


def process_data(data, time_range_beginning):
    """

    :param data:
    :param time_range_beginning:
    :return:
    """
    d = {'name': [], 'org': [], 'provider': [], 'launches': [], 'repo_url': [], 'binder_url': []}
    for container in data:
        repo_url = container['metric']['repo']
        provider, org, repo = repo_url.replace('https://', '').rsplit('/', 2)
        
        # calculate number of launches for each repo and each binder container/deployment
        values = [int(ii[1]) for ii in container['values']]
        first_value_ts = container['values'][0][0]
        first_value_dt = datetime.utcfromtimestamp(first_value_ts)
        # prometheus scrapes data each minute, so ignore seconds while comparision
        if first_value_dt.replace(second=0, microsecond=0) > time_range_beginning.replace(second=0, microsecond=0):
            # this container is created after beginning of time range
            # NOTE first value in container can be > 1 if there are simultaneous launches
            # first_value = values[0]
            # assert first_value == 1, f'{org}/{repo}---{first_value}---{first_value_dt}---{time_range_beginning}'
            # print(repo, first_value_dt, time_range_beginning, first_value)
            launches = max(values)
        else:
            # this container is created before beginning of time range
            launches = max(values) - min(values)
                
        # print(repo_url, launches, container['metric']['status'], container['metric']['retries'])
        if repo in d['name']:
            # same repo can have status success with different retries values
            i = d['name'].index(repo)
            d['launches'][i] += launches
        else:
            d['launches'].append(launches)
            
            d['name'].append(repo)
            d['org'].append(org)
            d['provider'].append(provider)
            d['repo_url'].append(repo_url)
            d['binder_url'].append(binder_url(org, repo))
    return d


def get_popular_repos(time_range, time_delta):
    data = query(f'{time_range}')
    time_range_beginning = datetime.utcnow() - time_delta
    data = process_data(data, time_range_beginning)
    return data


def makedf(time_range, time_delta):
    """

    :param time_range:
    :param time_delta:
    :return:
    """
    data = get_popular_repos(time_range, time_delta)
    df = pd.DataFrame(data)
    # df = df.drop_duplicates(['name'])
    df = df.groupby(['name', 'org', 'provider','repo_url', 'binder_url']).sum().reset_index().sort_values('launches', ascending=False)
    # df['log_launches'] = df['launches'].apply(np.log)
    df = df.style.format({'repo_url':lambda x: f'<a target="_blank" href="{x}">repo url</a>',
                 'binder_url': lambda x: f'<a target="_blank" href="{x}">binder url</a>'})
    return df
