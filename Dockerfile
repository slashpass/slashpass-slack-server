FROM python:3.12-alpine

COPY . /app

RUN apk update
RUN apk add g++
RUN apk add gcc
RUN apk add postgresql-dev

WORKDIR /app
RUN poetry install
EXPOSE 8000

WORKDIR /app
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "wsgi"]
