FROM python:3.11-rc-slim-buster

WORKDIR /workspace
COPY ./requirements.txt /workspace/requirements.txt

RUN apt update

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r /workspace/requirements.txt

COPY ./cache /workspace/cache
COPY ./client /workspace/client
COPY ./db /workspace/db
COPY ./utils /workspace/utils

ENV PYTHONPATH=/workspace/app:$PYTHONPATH
