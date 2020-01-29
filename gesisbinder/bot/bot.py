"""
Derived from henchbot.py script: https://github.com/henchbot/mybinder.org-upgrades/blob/master/henchbot.py
"""

from yaml import safe_load as load
import requests
import subprocess
import os
import shutil
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

GL_BOT_NAME = os.environ['GL_BOT_NAME'].strip()
GL_BOT_EMAIL = os.environ['GL_BOT_EMAIL'].strip()
GL_BOT_TOKEN = os.environ['GL_BOT_TOKEN'].strip()

# https://docs.gitlab.com/ee/api/#personal-access-tokens
GL_API_AUTHORIZATION_HEADER = {"Private-Token": GL_BOT_TOKEN}
GL_API_URL = f"https://git.gesis.org/api/v4/"
GL_ORG_NAME = os.environ.get("GL_ORG_NAME", "ilcm")
GL_REPO_NAME = os.environ.get("GL_REPO_NAME", "orc")
GL_REPO_URL = f"https://oauth2:{GL_BOT_TOKEN}@git.gesis.org/{GL_ORG_NAME}/{GL_REPO_NAME}"

GH_ORG_NAME = os.environ.get("GH_ORG_NAME", "gesiscss")
GH_REPO_NAME = os.environ.get("GH_REPO_NAME", "orc")
GH_REPO_RAW_URL = f"https://raw.githubusercontent.com/{GH_ORG_NAME}/{GH_REPO_NAME}/master/"

BHUB_RAW_URL = "https://raw.githubusercontent.com/jupyterhub/binderhub/"

MYBINDER_REPO_URL = f"https://github.com/jupyterhub/mybinder.org-deploy/"
MYBINDER_REPO_RAW_URL = f"https://raw.githubusercontent.com/jupyterhub/mybinder.org-deploy/"


class Bot:
    """
    Class for a bot that determines whether an upgrade is necessary
    for GESIS Binder depending on if repo2docker and BinderHub is updated on mybinder.org.
    If an upgrade is needed, it will checkout into <repo>_bump branch,
    edit files and create a PR.
    """
    def __init__(self):
        """
        Start by getting the latest commits of repo2docker, BinderHub and Jupyterhub in mybinder.org
        and the live ones in GESIS Binder.
        """
        self.commit_info = {'binderhub': {}, 'repo2docker': {}, 'jupyterhub': {}}
        self.get_new_commits()
        self.gitlab_project_id = None
        self.branch_name = None

    def set_gitlab_project_id(self, repo_name):
        projects = requests.get(f'{GL_API_URL}projects?search={repo_name}',
                                headers=GL_API_AUTHORIZATION_HEADER).json()
        for project in projects:
            if project['name'] == repo_name:
                self.gitlab_project_id = project['id']
                break

    def check_existing_prs(self, repo):
        """
        Check if there are open PRs created by bot
        """
        # https://docs.gitlab.com/ee/api/merge_requests.html#list-merge-requests
        prs = requests.get(GL_API_URL + 'merge_requests?state=opened',
                           headers=GL_API_AUTHORIZATION_HEADER).json()
        for pr in prs:
            if repo in pr['title'].lower():
                pr_latest = pr['title'].split('...')[-1].strip()
                if pr_latest == self.commit_info[repo]['latest']:
                    # same update, pr is not merged yet
                    return None
                return {'iid': pr['iid']}  # iid is unique only in scope of a single project
        return False

    def check_branch_exists(self):
        # https://docs.gitlab.com/ee/api/branches.html#list-repository-branches
        branches = requests.get(f'{GL_API_URL}/projects/{self.gitlab_project_id}/repository/branches',
                                headers=GL_API_AUTHORIZATION_HEADER).json()
        return self.branch_name in [b['name'] for b in branches]

    def delete_old_branch_if_exists(self):
        if self.check_branch_exists():
            # https://docs.gitlab.com/ee/api/branches.html#delete-repository-branch
            res = requests.delete(f'{GL_API_URL}/projects/{self.gitlab_project_id}/repository/branches/{self.branch_name}',
                                  headers=GL_API_AUTHORIZATION_HEADER)
            assert res.status_code == 204

    def edit_repo2docker_files(self, repo):
        """
        Update the SHA to latest for r2d
        """
        fnames = ['gesisbinder/gesisbinder/values.yaml',
                  'gesishub/gesishub/values.yaml']
        for fname in fnames:
            with open(fname, 'r', encoding='utf8') as f:
                values_yaml = f.read()

            updated_yaml = values_yaml.replace(
                "jupyter/repo2docker:{}".format(self.commit_info[repo]['live']),
                "jupyter/repo2docker:{}".format(self.commit_info[repo]['latest'])
            )

            with open(fname, 'w', encoding='utf8') as f:
                f.write(updated_yaml)
        return fnames

    def edit_binderhub_files(self, repo):
        """
        Update the SHA to latest for bhub
        """
        fname = 'gesisbinder/gesisbinder/requirements.yaml'
        with open(fname, 'r', encoding='utf8') as f:
            requirements_yaml = f.read()

        updated_yaml = requirements_yaml.replace(
            "version: {}".format(self.commit_info[repo]['live']),
            "version: {}".format(self.commit_info[repo]['latest']),
            1
        )

        with open(fname, 'w', encoding='utf8') as f:
            f.write(updated_yaml)

        return [fname]

    def edit_files(self, repo):
        """
        Controlling method to update file for the repo
        """
        if repo == 'repo2docker':
            return self.edit_repo2docker_files(repo)
        elif repo == 'binderhub':
            return self.edit_binderhub_files(repo)

    def add_commit_push(self, files_changed, repo):
        """
        After making change, add, commit and push to fork
        """
        for f in files_changed:
            subprocess.check_call(['git', 'add', f])

        if repo == 'repo2docker':
            commit_message = 'repo2docker: https://github.com/jupyter/repo2docker/compare/{}...{}'.format(
                self.commit_info['repo2docker']['live'].split('.dirty')[0].split('.')[-1][1:],
                self.commit_info['repo2docker']['latest'].split('.dirty')[0].split('.')[-1][1:])
        elif repo == 'binderhub':
            commit_message = 'binderhub: https://github.com/jupyterhub/binderhub/compare/{}...{}'.format(
                self.bhub_live,
                self.bhub_latest)

        subprocess.check_call(['git', 'config', 'user.name', GL_BOT_NAME])
        subprocess.check_call(['git', 'config', 'user.email', GL_BOT_EMAIL])
        subprocess.check_call(['git', 'commit', '-m', commit_message])
        if self.check_branch_exists():
            # there is an open PR for this repo, so update it
            subprocess.check_call(['git', 'push', '-f', GL_REPO_URL, self.branch_name])
        else:
            subprocess.check_call(['git', 'push', GL_REPO_URL, self.branch_name])

    def get_associated_prs(self, compare_url):
        """
        Gets all PRs from dependency repo associated with the upgrade
        """
        repo_api = compare_url.replace('github.com', 'api.github.com/repos')
        res = requests.get(repo_api).json()
        if 'commits' not in res or not res['commits']:
            logging.error("Compare url returns no commits but there must be commits. "
                          "Something must be wrong with compare url.")
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
                                self.commit_info['repo2docker']['live'].split('.dirty')[0].split('.')[-1][1:],
                                self.commit_info['repo2docker']['latest'].split('.dirty')[0].split('.')[-1][1:])
        elif repo == 'binderhub':
            compare_url = 'https://github.com/jupyterhub/binderhub/compare/{}...{}'.format(
                                self.bhub_live,
                                self.bhub_latest)
        logging.info('compare url: {}'.format(compare_url))
        associated_prs = self.get_associated_prs(compare_url)
        body = '\n'.join(
            [f'This is a {repo} version bump. See the link below for a diff of new changes:\n',
             compare_url + ' \n'] + associated_prs
        )
        return body

    def create_update_pr(self, repo, existing_pr):
        """
        Makes the PR from all components
        """
        body = self.make_pr_body(repo)
        title = f"{repo}: {self.commit_info[repo]['live']}...{self.commit_info[repo]['latest']}"
        params = {'source_branch': self.branch_name, 'target_branch': 'master',
                  'title': title, 'description': f'{body}'}
        if existing_pr:
            # update title and description of existing PR
            # https://docs.gitlab.com/ee/api/merge_requests.html#update-mr
            res = requests.put(f"{GL_API_URL}projects/{self.gitlab_project_id}/merge_requests/{existing_pr['iid']}",
                               params=params, headers=GL_API_AUTHORIZATION_HEADER)
        else:
            # https://docs.gitlab.com/ee/api/merge_requests.html#create-mr
            res = requests.post(f"{GL_API_URL}projects/{self.gitlab_project_id}/merge_requests",
                                params=params, headers=GL_API_AUTHORIZATION_HEADER)
        logging.info(f"PR done: {title}")

    def update_repos(self, repos):
        """
        Main method to check/create upgrades
        """
        for repo in repos:
            self.branch_name = repo + '_bump'
            if self.commit_info[repo]['live'] != self.commit_info[repo]['latest']:
                logging.info(f"{repo}:{self.commit_info[repo]['live']}-->{self.commit_info[repo]['latest']}")
                self.set_gitlab_project_id(GL_REPO_NAME)
                existing_pr = self.check_existing_prs(repo)
                if existing_pr is None:
                    # there is a PR with same update, it is not merged yet
                    continue
                elif existing_pr is False:
                    # no PR exists for this repo
                    self.delete_old_branch_if_exists()

                subprocess.check_call(['git', 'clone', f'{GL_REPO_URL}.git'])
                os.chdir(GL_REPO_NAME)
                subprocess.check_call(['git', 'checkout', '-b', self.branch_name])

                files_changed = self.edit_files(repo)
                self.add_commit_push(files_changed, repo)

                os.chdir('..')
                shutil.rmtree(GL_REPO_NAME)

                self.create_update_pr(repo, existing_pr)
            else:
                logging.info(f"{repo}: already up-to-date")

    def get_repo2docker_live(self):
        """
        Get the live r2d SHA from GESIS Notebooks
        """
        # Load master repo2docker
        url_helm_chart = f"{GH_REPO_RAW_URL}gesisbinder/gesisbinder/values.yaml"
        helm_chart = requests.get(url_helm_chart)
        helm_chart = load(helm_chart.text)
        r2d_live = helm_chart['binderhub']['config']['BinderHub']['build_image'].split(':')[-1]
        self.commit_info['repo2docker']['live'] = r2d_live

    def get_binderhub_live(self):
        """
        Get the latest BinderHub SHA from GESIS Notebooks
        """
        # Load master requirements
        url_requirements = f"{GH_REPO_RAW_URL}gesisbinder/gesisbinder/requirements.yaml"
        requirements = load(requests.get(url_requirements).text)
        binderhub_dep = [ii for ii in requirements['dependencies'] if ii['name'] == 'binderhub'][0]
        bhub_live = binderhub_dep['version'].strip()
        self.commit_info['binderhub']['live'] = bhub_live

    def get_jupyterhub_live(self):
        """
        Get the live JupyterHub SHA from BinderHub repo
        """
        url_binderhub_requirements = f"{BHUB_RAW_URL}{self.bhub_live}/helm-chart/binderhub/requirements.yaml"
        requirements = load(requests.get(url_binderhub_requirements).text)
        jupyterhub_dep = [ii for ii in requirements['dependencies'] if ii['name'] == 'jupyterhub'][0]
        jhub_live = jupyterhub_dep['version'].strip()
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
        bhub_latest = binderhub_dep['version'].strip()
        self.commit_info['binderhub']['latest'] = bhub_latest

    def get_jupyterhub_latest(self):
        """
        Get the live JupyterHub SHA from BinderHub repo
        """
        url_binderhub_requirements = f"{BHUB_RAW_URL}{self.bhub_latest}/helm-chart/binderhub/requirements.yaml"
        requirements = load(requests.get(url_binderhub_requirements).text)
        jupyterhub_dep = [ii for ii in requirements['dependencies'] if ii['name'] == 'jupyterhub'][0]
        jhub_latest = jupyterhub_dep['version'].strip()
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

    def parse_chart_version(self, chart_version):
        """
        All cases: https://github.com/jupyterhub/chartpress#examples-chart-versions-and-image-tags
        - 0.8.0
        - 0.8.0-n004.hasdf123
        - 0.9.0-beta.1
        - 0.2.0-072.544c0b1
        - 0.9.0-beta.1.n001.hdfgh345
        """
        parts = chart_version.split('-')
        if len(parts) == 1:
            # stable version: 0.8.0
            return chart_version
        else:
            parts = chart_version.split('-')[-1].split('.')
            if len(parts) == 2 and not parts[0].startswith('n') and not parts.isdigit():
                # beta version: 0.9.0-beta.1
                return chart_version
            else:
                # dev: 0.8.0-n004.hasdf123 or 0.9.0-beta.1.n001.hdfgh345
                chart_version = parts[-1]
                if chart_version.startswith('h'):
                    chart_version = chart_version[1:]
                return chart_version

    @property
    def bhub_live(self):
        return self.parse_chart_version(self.commit_info['binderhub']['live'])

    @property
    def bhub_latest(self):
        return self.parse_chart_version(self.commit_info['binderhub']['latest'])


if __name__ == '__main__':
    b = Bot()
    b.update_repos(['repo2docker', 'binderhub'])
