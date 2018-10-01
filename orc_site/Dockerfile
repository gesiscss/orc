FROM ubuntu:18.04

LABEL maintainer="notebooks@gesis.org"

RUN apt-get update -y && \
    apt-get install -yq \
    python3-pip \
    python3-dev \
    vim \
    htop \
    less && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# upgrade pip
RUN pip3 install --upgrade pip

# We copy just the requirements.txt first to leverage Docker cache
COPY ./requirements.txt /app/requirements.txt

WORKDIR /app

RUN pip3 install --no-cache-dir -r requirements.txt

COPY . /app

# tell the port number the container should expose
EXPOSE 5000

# run the application
CMD ["python3", "app.py"]
