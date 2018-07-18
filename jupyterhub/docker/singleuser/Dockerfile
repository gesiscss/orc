# https://hub.docker.com/r/jupyter/datascience-notebook/tags/
# https://github.com/jupyter/docker-stacks/tree/master/datascience-notebook
FROM jupyter/datascience-notebook:702d2f6a3eaa

RUN pip install --no-cache jupyterhub==0.9.1

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

# FIXME r packages are actually not installed
# https://anaconda.org/brown-data-science/repo
RUN conda install --quiet --yes \
    -c conda-forge \
#    'r-tm=0.7*' \
    'lxml=4.2.*' \
    'wordcloud=1.4.*' && \
#    conda install --quiet --yes \
#    -c brown-data-science \
#    'r-lda=1.4*' \
#    'r-topicmodels=0.2*' && \
#    conda install --quiet --yes \
#    -c bitnik \
#    'r-opennlpdata=1.5.*' \
#    'r-opennlp=0.2*' && \
    conda clean -tipsy && \
    fix-permissions $CONDA_DIR && \
    fix-permissions /home/$NB_USER

# https://github.com/jupyter/notebook/blob/master/notebook/templates/page.html
RUN mv /opt/conda/lib/python3.6/site-packages/notebook/templates/page.html /opt/conda/lib/python3.6/site-packages/notebook/templates/page_base.html
ADD templates/page.html /opt/conda/lib/python3.6/site-packages/notebook/templates/page.html
# FIXME extra_template_paths didnt work
#RUN mkdir -p /etc/jupyter/custom_notebook_templates
#COPY templates/page.html /etc/jupyter/custom_notebook_templates
#USER root
#RUN chown -R $NB_UID:users /etc/jupyter/custom_notebook_templates
#USER $NB_UID
COPY extra_notebook_config.py  /etc/jupyter/extra_notebook_config.py
RUN cat /etc/jupyter/extra_notebook_config.py >> /etc/jupyter/jupyter_notebook_config.py
RUN rm -f /etc/jupyter/extra_notebook_config.py

# FIXME doesnt work for jlab
# https://github.com/jupyterlab/jupyterlab/blob/master/jupyterlab/staging/templates/template.html
ADD templates/template.html /opt/conda/lib/python3.6/site-packages/jupyterlab/staging/templates/template.html
