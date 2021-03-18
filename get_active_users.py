import requests
import pandas as pd


def get_active_users(api_url, token, days=14):
    """
    Get active users is the last 'X' days using the JupyterHub API.
    """
    response = requests.get(
        api_url + "/users", headers={"Authorization": "token %s" % token}
    )
    if response.status_code == 404:
        raise ValueError(
            "Not able to connect to the JupyterHub API, check the API_URL."
        )
    elif response.status_code == 403:
        raise ValueError("Make sure you have provided the token of an admin user.")

    users = pd.DataFrame.from_records(response.json())
    last_active = pd.Timestamp.today() - pd.Timedelta(days=days)
    users.last_activity = pd.to_datetime(users.last_activity)
    return users[users.last_activity.dt.date > last_active.date()].name.to_list()


api_url = "http://notebooks.gesis.org/hub/api"
# get the token from https://notebooks.gesis.org/hub/token
# make sure it's from an admin user.
token = ""

print(get_active_users(api_url, token))
print(len(get_active_users(api_url, token)))
