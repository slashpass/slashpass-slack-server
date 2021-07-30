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
    access_token = db.Column(db.String)
    authed_user = db.Column(db.String)
    bot_user_id = db.Column(db.String)
    created = db.Column(db.DateTime)
    enterprise_id = db.Column(db.String, nullable=True)
    enterprise_name = db.Column(db.String, nullable=True)
    is_enterprise_install = db.Column(db.Boolean)
    public_key = db.Column(db.Text, nullable=True)
    scope = db.Column(db.String)
    team_id = db.Column(db.String, unique=True)
    team_name = db.Column(db.String)
    url = db.Column(db.String, nullable=True)

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

    def __init__(
        self,
        access_token,
        authed_user,
        bot_user_id,
        enterprise_id,
        enterprise_name,
        is_enterprise_install,
        scope,
        team_id,
        team_name,
    ):
        self.access_token = access_token
        self.authed_user = authed_user
        self.bot_user_id = bot_user_id
        self.enterprise_id = enterprise_id
        self.enterprise_name = enterprise_name
        self.is_enterprise_install = is_enterprise_install
        self.scope = scope
        self.team_id = team_id
        self.team_name = team_name
        if self.created is None:
            self.created = datetime.utcnow()

    def __repr__(self):
        return "Slack team: {}".format(self.team_name)
