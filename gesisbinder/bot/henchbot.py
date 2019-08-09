"""
Original henchbot script: https://github.com/henchbot/mybinder.org-upgrades/blob/master/henchbot.py
"""

from yaml import safe_load as load
import requests
import subprocess
import os
import shutil
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

TOKEN = os.environ['HENCHBOT_TOKEN']
BOT_GH_NAME = os.environ['BOT_GH_NAME']
BOT_EMAIL = os.environ['BOT_EMAIL']

ORG_NAME = os.environ.get("ORG_NAME", "gesiscss")
REPO_NAME = os.environ.get("REPO_NAME", "orc")
REPO_API = f"https://api.github.com/repos/{ORG_NAME}/{REPO_NAME}/"
REPO_URL = f"https://github.com/{ORG_NAME}/{REPO_NAME}.git"
REPO_RAW_URL = f"https://raw.githubusercontent.com/{ORG_NAME}/{REPO_NAME}/master/"

BHUB_RAW_URL = "https://raw.githubusercontent.com/jupyterhub/binderhub/"

MYBINDER_REPO_NAME = os.environ.get("MYBINDER_REPO_NAME", "mybinder.org-deploy")
MYBINDER_REPO_URL = f"https://github.com/jupyterhub/{MYBINDER_REPO_NAME}/"
MYBINDER_REPO_RAW_URL = f"https://raw.githubusercontent.com/jupyterhub/{MYBINDER_REPO_NAME}/"


class henchBotMyBinder:
    """
    Class for a bot that determines whether an upgrade is necessary
    for mybinder.org dependencies on repo2docker and BinderHub.
    If an upgrade is needed, it will fork the main mybinder.org repo,
    update the SHA and create a PR.
    """
    def __init__(self):
        """
        Start by getting the latest commits of repo2docker, BinderHub and Jupyterhub
        and the live SHAs in GESIS Binder
        """
        self.commit_info = {'binderhub': {}, 'repo2docker': {}, 'jupyterhub': {}}
        self.get_new_commits()

    def update_repos(self, repos):
        """
        Main method to check/create upgrades
        """
        my_binder_prs = requests.get(REPO_API + 'pulls?state=open')
        henchbot_prs = [x for x in my_binder_prs.json() if x['user']['login'] == BOT_GH_NAME]
        self.check_fork_exists()

        if len(henchbot_prs) == 0 and self.fork_exists:
            self.remove_fork()

        for repo in repos:
            if self.commit_info[repo]['live'] != self.commit_info[repo]['latest']:
                logging.info(f"{repo}:{self.commit_info[repo]['live']}-->{self.commit_info[repo]['latest']}")
                existing_pr = self.check_existing_prs(henchbot_prs, repo)

                if existing_pr is None:
                    # same update, pr is not merged yet
                    continue

                self.upgrade_repo_commit(existing_pr, repo)
            else:
                logging.info(f"{repo}: already up-to-date}")

    def check_existing_prs(self, henchbot_prs, repo):
        """
        Check GESIS Notebooks for existing henchbot PRs
        """
        for pr in henchbot_prs:
            if repo in pr['title'].lower():
                pr_latest = pr['title'].split('...')[-1].strip()
                if pr_latest == self.commit_info[repo]['latest']:
                    # same update, pr is not merged yet
                    return None
                return {'number': pr['number'], 'prev_latest': pr_latest}
        return False

    def check_fork_exists(self):
        """
        Check if a fork exists for henchbot already
        """
        res = requests.get(f'https://api.github.com/users/{BOT_GH_NAME}/repos')
        self.fork_exists = bool([x for x in res.json() if x['name'] == REPO_NAME])

    def remove_fork(self):
        """
        Remove the henchbot fork
        """
        res = requests.delete(f'https://api.github.com/repos/{BOT_GH_NAME}/{REPO_NAME}',
                              headers={'Authorization': f'token {TOKEN}'})
        self.fork_exists = False
        time.sleep(5)

    def make_fork(self):
        """
        Make a fork of the orc repo to henchbot
        """
        res = requests.post(REPO_API + 'forks', headers={'Authorization': f'token {TOKEN}'})

    def clone_fork(self):
        """
        Clone henchbot's mybinder.org fork
        """
        subprocess.check_call(['git', 'clone', f'https://github.com/{BOT_GH_NAME}/{REPO_NAME}'])

    def delete_old_branch(self, repo):
        """
        Delete an old branch in the henchbot fork (if it was merged)
        """
        res = requests.get(f'https://api.github.com/repos/{BOT_GH_NAME}/{REPO_NAME}/branches')
        if repo+'_bump' in [x['name'] for x in res.json()]:
            subprocess.check_call(['git', 'push', '--delete', 'origin', repo+'_bump'])
            # subprocess.call(['git', 'branch', '-d', repo+'_bump'])

    def checkout_branch(self, existing_pr, repo):
        """
        Checkout branch for the bump
        """
        if not existing_pr:
            if self.fork_exists:  # fork exists for other repo and old branch for this repo
                self.delete_old_branch(repo)
                subprocess.check_call(['git', 'pull', REPO_URL, 'master'])
            # subprocess.check_call(['git', 'checkout', '-b', repo+'_bump'])
        # else:
        #     subprocess.check_call(['git', 'checkout', repo+'_bump'])
        subprocess.check_call(['git', 'checkout', '-b', repo+'_bump'])

    def edit_repo2docker_files(self, repo, existing_pr):
        """
        Update the SHA to latest for r2d
        """
        fname = 'gesisbinder/gesisbinder/values.yaml'
        with open(fname, 'r', encoding='utf8') as f:
            values_yaml = f.read()

        # if not existing_pr:
        updated_yaml = values_yaml.replace(
            "jupyter/repo2docker:{}".format(self.commit_info[repo]['live']),
            "jupyter/repo2docker:{}".format(self.commit_info[repo]['latest'])
        )
        # else:
        #     updated_yaml = values_yaml.replace(
        #         "jupyter/repo2docker:{}".format(
        #             existing_pr['prev_latest']),
        #         "jupyter/repo2docker:{}".format(
        #             self.commit_info[repo]['latest']))

        with open(fname, 'w', encoding='utf8') as f:
            f.write(updated_yaml)

        return [fname]

    def edit_binderhub_files(self, repo, existing_pr):
        """
        Update the SHA to latest for bhub
        """
        fname = 'gesisbinder/gesisbinder/requirements.yaml'
        with open(fname, 'r', encoding='utf8') as f:
            requirements_yaml = f.read()

        # if not existing_pr:
        updated_yaml = requirements_yaml.replace(
            "version: 0.2.0-{}".format(self.commit_info[repo]['live']),
            "version: 0.2.0-{}".format(self.commit_info[repo]['latest'])
        )
        # else:
        #     updated_yaml = requirements_yaml.replace(
        #         "version: 0.2.0-{}".format(existing_pr['prev_latest']),
        #         "version: 0.2.0-{}".format(self.commit_info[repo]['latest']))

        with open(fname, 'w', encoding='utf8') as f:
            f.write(updated_yaml)

        return [fname]

    def edit_files(self, repo, existing_pr):
        """
        Controlling method to update file for the repo
        """
        if repo == 'repo2docker':
            return self.edit_repo2docker_files(repo, existing_pr)
        elif repo == 'binderhub':
            return self.edit_binderhub_files(repo, existing_pr)

    def add_commit_push(self, files_changed, repo):
        """
        After making change, add, commit and push to fork
        """
        for f in files_changed:
            subprocess.check_call(['git', 'add', f])

        if repo == 'repo2docker':
            commit_message = 'repo2docker: https://github.com/jupyter/repo2docker/compare/{}...{}'.format(
                self.commit_info['repo2docker']['live'], self.commit_info['repo2docker']['latest'])
        elif repo == 'binderhub':
            commit_message = 'binderhub: https://github.com/jupyterhub/binderhub/compare/{}...{}'.format(
                self.commit_info['binderhub']['live'], self.commit_info['binderhub']['latest'])

        subprocess.check_call(['git', 'config', 'user.name', BOT_GH_NAME])
        subprocess.check_call(['git', 'config', 'user.email', BOT_EMAIL])
        subprocess.check_call(['git', 'commit', '-m', commit_message])
        subprocess.check_call(['git', 'push',
                               f'https://{BOT_GH_NAME}:{TOKEN}@github.com/{BOT_GH_NAME}/{REPO_NAME}',
                               repo+'_bump'])

    def upgrade_repo_commit(self, existing_pr, repo):
        """
        Main controlling method for the update
        """
        if not self.fork_exists:
            self.make_fork()
        self.clone_fork()

        os.chdir(REPO_NAME)
        self.checkout_branch(existing_pr, repo)
        files_changed = self.edit_files(repo, existing_pr)
        self.add_commit_push(files_changed, repo)
        os.chdir('..')
        shutil.rmtree(REPO_NAME)

        self.create_update_pr(repo, existing_pr)

    def get_mybinder_compare_url(self, repo):
        api_url = MYBINDER_REPO_URL.replace('github.com', 'api.github.com/repos')
        api_url = api_url + "pulls?state=closed"
        prs = requests.get(api_url).json()
        live_commit = self.commit_info[repo]['live']
        latest_commit = self.commit_info[repo]['latest']
        compare = '...'
        for pr in prs:
            if f'...{latest_commit}' in pr['title']:
                compare = compare + pr['merge_commit_sha']
            elif f'...{live_commit}' in pr['title']:
                compare = pr['merge_commit_sha'] + compare
                break
        compare_url = MYBINDER_REPO_URL + "compare/" + compare
        return compare_url

    def get_associated_prs(self, compare_url):
        """
        Gets all PRs from dependency repo associated with the upgrade
        """
        repo_api = compare_url.replace('github.com', 'api.github.com/repos')
        res = requests.get(repo_api).json()
        commit_shas = [x['sha'] for x in res['commits']]

        pr_api = repo_api.split('/compare/')[0] + '/pulls/'
        associated_prs = ['Associated PRs:']
        for sha in commit_shas[::-1]:
            res = requests.get('https://api.github.com/search/issues?q=sha:{}'.format(sha)).json()
            if 'items' in res:
                for i in res['items']:
                    formatted = '- {} [#{}]({})'.format(i['title'], i['number'], i['html_url'])
                    repo_owner = i['repository_url'].split('/')[-2]
                    try:
                        merged_at = requests.get(pr_api + str(i['number'])).json()['merged_at']
                    except KeyError:
                        continue
                    if formatted not in associated_prs and repo_owner.startswith('jupyter') and merged_at:
                        associated_prs.append(formatted)
            time.sleep(3)

        return associated_prs

    def make_pr_body(self, repo):
        """
        Formats a text body for the PR
        """
        if repo == 'repo2docker':
            compare_url = 'https://github.com/jupyter/repo2docker/compare/{}...{}'.format(
                                self.commit_info['repo2docker']['live'],
                                self.commit_info['repo2docker']['latest'])
        elif repo == 'binderhub':
            compare_url = 'https://github.com/jupyterhub/binderhub/compare/{}...{}'.format(
                                self.commit_info['binderhub']['live'],
                                self.commit_info['binderhub']['latest'])
        associated_prs = self.get_associated_prs(compare_url)
        mybinder_compare_url = self.get_mybinder_compare_url(repo)
        body = '\n'.join(
            [f'This is a {repo} version bump. See the link below for a diff of new changes:\n',
             compare_url + ' \n'] + associated_prs + [' \n', mybinder_compare_url]
        )
        return body

    def create_update_pr(self, repo, existing_pr):
        """
        Makes the PR from all components
        """
        body = self.make_pr_body(repo)

        title = f"{repo}: {self.commit_info[repo]['live']}...{self.commit_info[repo]['latest']}"
        pr = {
            'title': title,
            'body': body,
            'base': 'master',
            'head': f'{BOT_GH_NAME}:{repo}_bump'}

        if existing_pr:
            res = requests.patch(REPO_API + 'pulls/{}'.format(existing_pr['number']),
                                 headers={'Authorization': f'token {TOKEN}'}, json=pr)
        else:
            res = requests.post(REPO_API + 'pulls',
                                headers={'Authorization': f'token {TOKEN}'}, json=pr)

        logging.info(f"PR done: {title}")

    def get_repo2docker_live(self):
        """
        Get the live r2d SHA from GESIS Notebooks
        """
        # Load master repo2docker
        url_helm_chart = f"{REPO_RAW_URL}gesisbinder/gesisbinder/values.yaml"
        helm_chart = requests.get(url_helm_chart)
        helm_chart = load(helm_chart.text)
        r2d_live = helm_chart['binderhub']['config']['BinderHub']['build_image'].split(':')[-1]
        self.commit_info['repo2docker']['live'] = r2d_live

    def get_binderhub_live(self):
        """
        Get the latest BinderHub SHA from GESIS Notebooks
        """
        # Load master requirements
        url_requirements = f"{REPO_RAW_URL}gesisbinder/gesisbinder/requirements.yaml"
        requirements = load(requests.get(url_requirements).text)
        binderhub_dep = [ii for ii in requirements['dependencies'] if ii['name'] == 'binderhub'][0]
        bhub_live = binderhub_dep['version'].split('-')[-1]
        self.commit_info['binderhub']['live'] = bhub_live

    def get_jupyterhub_live(self):
        """
        Get the live JupyterHub SHA from BinderHub repo
        """
        url_binderhub_requirements = f"{BHUB_RAW_URL}{self.commit_info['binderhub']['live']}" \
                                     f"/helm-chart/binderhub/requirements.yaml"
        requirements = load(requests.get(url_binderhub_requirements).text)
        jupyterhub_dep = [ii for ii in requirements['dependencies'] if ii['name'] == 'jupyterhub'][0]
        jhub_live = jupyterhub_dep['version'].split('-')[-1]
        self.commit_info['jupyterhub']['live'] = jhub_live

    def get_repo2docker_latest(self):
        """
        Get the latest r2d SHA from mybinder.org
        """
        # Load master repo2docker
        url_helm_chart = f"{MYBINDER_REPO_RAW_URL}master/mybinder/values.yaml"
        helm_chart = requests.get(url_helm_chart)
        helm_chart = load(helm_chart.text)
        r2d_latest = helm_chart['binderhub']['config']['BinderHub']['build_image'].split(':')[-1]
        self.commit_info['repo2docker']['latest'] = r2d_latest

    def get_binderhub_latest(self):
        """
        Get the latest BinderHub SHA from mybinder.org
        """
        # Load master requirements
        url_requirements = f"{MYBINDER_REPO_RAW_URL}master/mybinder/requirements.yaml"
        requirements = load(requests.get(url_requirements).text)
        binderhub_dep = [ii for ii in requirements['dependencies'] if ii['name'] == 'binderhub'][0]
        bhub_latest = binderhub_dep['version'].split('-')[-1]
        self.commit_info['binderhub']['latest'] = bhub_latest

    def get_jupyterhub_latest(self):
        """
        Get the live JupyterHub SHA from BinderHub repo
        """
        url_binderhub_requirements = f"{BHUB_RAW_URL}{self.commit_info['binderhub']['latest']}/helm-chart/binderhub/requirements.yaml"
        requirements = load(requests.get(url_binderhub_requirements).text)
        jupyterhub_dep = [ii for ii in requirements['dependencies'] if ii['name'] == 'jupyterhub'][0]
        jhub_latest = jupyterhub_dep['version'].split('-')[-1]
        self.commit_info['jupyterhub']['latest'] = jhub_latest

    def get_new_commits(self):
        """
        Main controlling method to get commit SHAs
        """
        # logging.info('Fetching latest commit SHAs for repo2docker, BinderHub and JupyterHub that deployed on GESIS Binder')
        self.get_repo2docker_live()
        self.get_binderhub_live()
        self.get_jupyterhub_live()

        # logging.info('Fetching latest commit SHAs for repo2docker, BinderHub and JupyterHub that deployed on mybinder.org')
        self.get_repo2docker_latest()
        self.get_binderhub_latest()
        self.get_jupyterhub_latest()

        logging.info(self.commit_info)



if __name__ == '__main__':
    hb = henchBotMyBinder()
    hb.update_repos(['repo2docker', 'binderhub'])
