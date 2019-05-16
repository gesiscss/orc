from subprocess import run, PIPE
from os.path import basename, join, isfile, dirname, realpath
from syslog import syslog, LOG_ERR


def quota():
    """
    This script is called every time nfs-provisioner projects file is changed.

    According to the change in the projects file, adds into /deletes from xfs quota.
    """
    xfs_dir = '/xfs'
    nfs_dir = f'{xfs_dir}/nfs'
    # projects file from xfs-nfs-provisioner
    nfs_projects_path = f'{nfs_dir}/projects'
    syslog(f'quota: {nfs_projects_path} is changed')

    # projects file of quota.py
    projects_path = join(dirname(realpath(__file__)), 'projects')
    if not isfile(projects_path):
        # create it, if already doesn't exist
        f = open(projects_path, 'w')
        f.close()

    with open(nfs_projects_path, 'r') as f1, \
         open(projects_path, 'r+') as f2:
        nfs_projects = {l for l in f1.read().splitlines() if l.strip()}
        projects = {l for l in f2.read().splitlines() if l.strip()}

        deleted = projects.difference(nfs_projects)
        for d in deleted:
            syslog(f'quota: deleted project: {d}')
            project_id = d.split(':')[0]
            # remove project from xfs quota by setting hard limit to 0
            cp = run(f"xfs_quota -x -c 'limit -p bhard=0 {project_id}' {xfs_dir}",
                     shell=True, stdout=PIPE, stderr=PIPE)
            syslog(f"quota: command: {cp.args} -> {cp.returncode} - stdout: {cp.stdout}")
            if cp.stderr:
                syslog(LOG_ERR, f"quota: error for command {cp.args}: {cp.stderr}")
            projects.remove(d)

        added = nfs_projects.difference(projects)
        for a in added:
            syslog(f'quota: added project: {a}')
            project_id, project_path, hard_limit = a.split(':')
            project_folder = basename(project_path)
            project_path = join(nfs_dir, project_folder)
            # add new project to xfs quota
            cp = run(f"xfs_quota -x -c 'project -s -p {project_path} {project_id}' {xfs_dir}",
                     shell=True, stdout=PIPE, stderr=PIPE)
            syslog(f"quota: command: {cp.args} -> {cp.returncode} - stdout: {cp.stdout}")
            if cp.stderr:
                syslog(LOG_ERR, f"quota: error for command {cp.args}: {cp.stderr}")
            # set hard limit for this project
            cp = run(f"xfs_quota -x -c 'limit -p bhard={hard_limit} {project_id}' {xfs_dir}",
                     shell=True, stdout=PIPE, stderr=PIPE)
            syslog(f"quota: command: {cp.args} -> {cp.returncode} - stdout: {cp.stdout}")
            if cp.stderr:
                syslog(LOG_ERR, f"quota: error for command {cp.args}: {cp.stderr}")
            projects.add(a)

        # re-write all projects into projects file of quota.py
        f2.seek(0)
        f2.write('\n'.join(projects) + '\n')
        f2.truncate()


if __name__ == '__main__':
    quota()
