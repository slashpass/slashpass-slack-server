FROM python:3.9-alpine

COPY . /app

RUN apk update
RUN apk add g++
RUN apk add gcc
RUN apk add postgresql-dev

WORKDIR /app
RUN pip install pipenv
RUN pipenv sync --system

EXPOSE 8000

WORKDIR /app
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "wsgi"]
