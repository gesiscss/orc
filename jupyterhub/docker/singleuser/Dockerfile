# https://hub.docker.com/r/jupyter/datascience-notebook/tags/
# https://github.com/jupyter/docker-stacks/tree/master/datascience-notebook
FROM jupyter/datascience-notebook:92fe05d1e7e5

# conda/pip/apt install additional packages here, if desired.

# pin jupyterhub to match the Hub version
# set via --build-arg in Makefile
ARG JUPYTERHUB_VERSION=0.8.*
RUN pip install --no-cache jupyterhub==$JUPYTERHUB_VERSION

# More R packages

## Building a conda R package: https://www.anaconda.com/blog/developer-blog/conda-data-science/
#conda install --quiet --yes conda-build
#conda skeleton cran openNLPdata
#conda build --quiet r-opennlpdata/
#conda skeleton cran openNLP
#conda build --quiet r-opennlp/
#conda build purge
#conda install -c anaconda binstar
#conda install anaconda-client
#binstar upload /opt/conda/conda-bld/linux-64/r-opennlpdata-1.5.3_4-r3.3.2_0.tar.bz2
#binstar upload /opt/conda/conda-bld/linux-64/r-opennlp-0.2_6-r3.3.2_0.tar.bz2

# https://anaconda.org/brown-data-science/repo
RUN conda install --quiet --yes \
    -c conda-forge \
    'r-tm=0.7*' \
    'lxml=4.2.*' \
    'wordcloud=1.4.*' && \
    conda install --quiet --yes \
    -c brown-data-science \
    'r-lda=1.4*' \
    'r-topicmodels=0.2*' && \
    conda install --quiet --yes \
    -c bitnik \
    'r-opennlpdata=1.5.*' \
    'r-opennlp=0.2*' && \
    conda clean -tipsy && \
    fix-permissions $CONDA_DIR && \
    fix-permissions /home/$NB_USER

# https://zero-to-jupyterhub.readthedocs.io/en/latest/user-environment.html#use-jupyterlab-by-default
# Note: For all methods of installation, if you are using a version of Jupyter Notebook earlier than 5.3,
# then you must also run the following command after installation to enable the JupyterLab server extension:
RUN jupyter serverextension enable --py jupyterlab --sys-prefix

# https://github.com/jupyter/notebook/blob/master/notebook/templates/page.html
RUN mv /opt/conda/lib/python3.6/site-packages/notebook/templates/page.html /opt/conda/lib/python3.6/site-packages/notebook/templates/page_base.html
ADD templates/page.html /opt/conda/lib/python3.6/site-packages/notebook/templates/page.html
# https://github.com/jupyterlab/jupyterlab/blob/master/jupyterlab/staging/templates/template.html
ADD templates/template.html /opt/conda/lib/python3.6/site-packages/jupyterlab/staging/templates/template.html
# redo this to apply replacement of template.html
RUN jupyter labextension install @jupyterlab/hub-extension && \
    npm cache clean && \
    rm -rf $CONDA_DIR/share/jupyter/lab/staging && \
    rm -rf /home/$NB_USER/.cache/yarn && \
    fix-permissions $CONDA_DIR && \
    fix-permissions /home/$NB_USER