`bot.py` is based on 
[henchbot script](https://github.com/henchbot/mybinder.org-upgrades/blob/master/src/mybinder-upgrades/henchbot.py). 
It fetches BinderHub and repo2docker updates of 
[mybinder.org-deploy](https://github.com/jupyterhub/mybinder.org-deploy) 
makes related PRs for GESIS Binder. 
It is implemented to be ran in a
[CronJob](https://kubernetes.io/docs/tasks/job/automated-tasks-with-cron-jobs/) 
(see `cron_job.yaml` file).
