import os
from datetime import datetime
from urllib.parse import urlparse, urlunparse

import redis
import requests
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from raven.contrib.flask import Sentry
from rsa import generate_key

from core import SlashpassCMD
from environ import BIP39, DATABASE_URL, REDIS_HOST, SENTRY_DSN

secret_key = generate_key(BIP39)
private_key = secret_key.exportKey("PEM")
public_key = secret_key.publickey().exportKey("PEM")

server = Flask(__name__)
server.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
server.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

cache = redis.StrictRedis(host=REDIS_HOST, port=6379)
sentry = Sentry(server, dsn=SENTRY_DSN)

cmd = SlashpassCMD(cache, private_key)
db = SQLAlchemy(server)


class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    slack_id = db.Column(db.String, unique=True)
    name = db.Column(db.String, unique=True)
    url = db.Column(db.String, nullable=True)
    public_key = db.Column(db.Text, nullable=True)
    created = db.Column(db.DateTime)

    def register_server(self, url):
        self.url = url
        try:
            response = requests.get(self.api("public_key"))
        except requests.exceptions.ConnectionError:
            return False

        if response.status_code != requests.codes.ok:
            return False

        self.public_key = response.text
        db.session.commit()
        return True

    def api(self, path):
        url_parts = list(urlparse(self.url))
        url_parts[2] = os.path.join(url_parts[2], path)
        return urlunparse(url_parts)

    def __init__(self, slack_id, name):
        self.slack_id = slack_id
        self.name = name
        if self.created is None:
            self.created = datetime.utcnow()

    def __repr__(self):
        return "Slack team: {}".format(self.name)
