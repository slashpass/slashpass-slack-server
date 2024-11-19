import pickle

from flask import Blueprint, abort, render_template

from environ import HOMEPAGE
from server import Team, cache, db

root_view = Blueprint("root", __name__)
insert_view = Blueprint("insert_view", __name__)


@root_view.route("", methods=["GET"])
def root():
    return render_template("redirect.html", redirect_url=HOMEPAGE)


@insert_view.route("/<token>", methods=["GET"])
def insert(token):
    token = str(token)
    if token not in cache:
        abort(404)
    obj = pickle.loads(cache[token])
    team_id = obj["team_id"]
    team = db.session.query(Team).filter_by(id=team_id).first()
    return render_template("redirect.html", redirect_url=f"{team.url}/insert/{token}")
