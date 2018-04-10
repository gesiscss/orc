# https://github.com/gesiscss/orc/tree/master/orc_site
FROM ubuntu:16.04

LABEL maintainer="kenan.erdogan@gesis.org"

RUN apt-get update -y && \
    apt-get install -yq \
    python3-pip \
    python3-dev \
    vim \
    htop \
    sshpass \
    less && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# upgrade pip
RUN pip3 install --upgrade pip

# We copy just the requirements.txt first to leverage Docker cache
COPY ./requirements.txt /job/requirements.txt

WORKDIR /job

RUN pip3 install --no-cache-dir -r requirements.txt

COPY . /job

# tell the port number the container should expose
#EXPOSE 5001

# run the application
#CMD ["python3", "backup.py"]
