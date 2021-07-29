from urllib.parse import urlencode

import requests
from flask import Blueprint, abort, render_template, request

from environ import SLACK_CLIENT_ID, SLACK_CLIENT_SECRET, SUCCESS_PAGE
from server import Team, db, sentry

view = Blueprint("slack_oauth", __name__)


@view.route("", methods=["GET"])
def slack_oauth():
    if "code" not in request.args:
        abort(400)

    oauth_access_url = "{}{}".format(
        "https://slack.com/api/oauth.v2.access?",
        urlencode(
            {
                "client_id": SLACK_CLIENT_ID,
                "client_secret": SLACK_CLIENT_SECRET,
                "code": request.args["code"],
            }
        ),
    )
    response = requests.get(oauth_access_url).json()

    if not response.get("ok", False):
        sentry.captureMessage(response)
        abort(403)

    enterprise = response.get("enterprise", None)

    access_token = response["access_token"]
    authed_user = response["authed_user"]["id"]
    bot_user_id = response["bot_user_id"]
    enterprise_id = enterprise["id"] if enterprise else None
    enterprise_name = enterprise["name"] if enterprise else None
    is_enterprise_install = response["is_enterprise_install"]
    scope = response["scope"]
    team_id = response["team"]["id"]
    team_name = response["team"]["name"]

    if not db.session.query(Team).filter_by(team_id=team_id).first():
        new_team = Team(
            access_token=access_token,
            authed_user=authed_user,
            bot_user_id=bot_user_id,
            enterprise_id=enterprise_id,
            enterprise_name=enterprise_name,
            is_enterprise_install=is_enterprise_install,
            scope=scope,
            team_id=team_id,
            team_name=team_name,
        )
        db.session.add(new_team)
        db.session.commit()
    return render_template("redirect.html", redirect_url=SUCCESS_PAGE)
