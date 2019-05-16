FROM python:3.7.3-stretch

LABEL maintainer="notebooks@gesis.org"

RUN apt-get update -y && \
    apt-get install -yq \
    vim \
    htop \
    sshpass \
    less && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# upgrade pip
RUN pip install --no-cache-dir --upgrade pip

COPY . /job
WORKDIR /job

RUN pip install --no-cache-dir -r requirements.txt

# run backup process
CMD ["python", "backup.py"]
