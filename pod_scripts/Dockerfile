# https://hub.docker.com/r/jupyter/datascience-notebook/tags/
# https://github.com/jupyter/docker-stacks/blob/master/scipy-notebook/Dockerfile
FROM jupyter/scipy-notebook:92fe05d1e7e5

# We copy just the requirements.txt first to leverage Docker cache
COPY ./scripts/requirements.txt /home/$NB_USER/work/requirements.txt

WORKDIR /home/$NB_USER/work

RUN pip install --no-cache-dir -r requirements.txt

COPY ./scripts /home/$NB_USER/work

USER root
RUN fix-permissions /home/$NB_USER/work
USER $NB_UID

EXPOSE 5000
CMD ["jupyter", "notebook", "--config=./jupyter_notebook_config.py"]
