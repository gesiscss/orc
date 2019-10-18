FROM python:3.7.4-stretch

LABEL maintainer="notebooks@gesis.org"

# upgrade pip
RUN pip install --no-cache-dir --upgrade pip

# We copy just the requirements.txt first to leverage Docker cache
COPY requirements.txt /requirements.txt

RUN pip install --no-cache-dir -r /requirements.txt

COPY . /image_cleaner

WORKDIR /image_cleaner

ENV PYTHONUNBUFFERED=1

CMD ["python", "image_cleaner.py"]
