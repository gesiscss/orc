FROM python:3.7.1-stretch

LABEL maintainer="notebooks@gesis.org"

RUN apt-get update -y && \
    apt-get install -yq \
    vim \
    htop \
    less && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# upgrade pip
RUN pip install --no-cache-dir --upgrade pip

# We copy just the requirements.txt first to leverage Docker cache
COPY ./requirements.txt /app/requirements.txt

WORKDIR /app

RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

# tell the port number the container should expose
EXPOSE 5000

# run the application
CMD ["python", "app.py"]
