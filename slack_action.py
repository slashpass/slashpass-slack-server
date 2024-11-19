import json

import validators
from flask import Blueprint, abort, request

from environ import DEMO_SERVER
from server import Team, db
from utils import error, info, success, valid_slack_request

view = Blueprint("slack_action", __name__)


@view.route("", methods=["POST"])
def action_api():
    data = request.values.to_dict()
    payload = json.loads(data["payload"])
    if not valid_slack_request(request):
        return abort(404)

    if "actions" not in payload:
        return "not implemented"

    if payload["callback_id"] == "configure_password_server":
        option = payload["actions"][0]
        action = option["name"]
        if action == "no_configure":
            return success(
                "Sure! for more information on how the pass command "
                "works, check out `/pass help` or our website "
                "at https://slashpass.co"
            )

        elif action == "no_reconfigure":
            return info("Password server unchanged.")

        team = db.session.query(Team).filter_by(team_id=payload["team"]["id"]).first()

        if action == "reconfigure_server":
            if not validators.url(option["value"]):
                return error("Invalid URL format, use: https://<domain>")

            return (
                success("Password server successfully updated!")
                if team.register_server(option["value"])
                else error("Unable to retrieve the _public_key_ " "from the server")
            )
        elif action == "use_demo_server":
            if not team.register_server(DEMO_SERVER):
                return error(
                    "An error occurred registering the server, " "please try later."
                )
            return success(
                "The testing server is already configured! remember that "
                "the data on this server will be deleted without prior "
                "notice, when you are ready to configure your company's server "
                "just run the command `/pass configure` along "
                "with the the private server url."
            )
