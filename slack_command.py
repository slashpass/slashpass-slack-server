import re

import validators
from flask import Blueprint, abort, jsonify, request

from core import SlashpassError
from environ import CONFIGURATION_GUIDE_URL, SLACK_SERVER
from server import Team, cmd, db
from utils import error, success, valid_slack_request, warning

view = Blueprint("slack_command", __name__)


@view.route("", methods=["POST"])
def api():
    data = request.values.to_dict()
    try:
        command = re.split("\s+", data["text"])
        slack_id = data["team_id"]
        team_domain = data["team_domain"]
        channel = data["channel_id"]
    except KeyError:
        abort(400)

    # ensuring that the request comes from slack
    if not valid_slack_request(request):
        return abort(404)

    team = db.session.query(Team).filter_by(slack_id=slack_id).first()
    if not team:
        return error(
            "You are not registered in our proxy server, try removig the app "
            "and adding it to slack again."
        )

    if command[0] == "help":
        fields = [
            {
                "title": "`/pass` _or_ `/pass list`",
                "value": "To list the available passwords in this channel.",
                "short": True,
            },
            {
                "title": "`/pass <secret>` or `/pass show <secret>`",
                "value": (
                    "To retrieve a one time use link with the secret content, "
                    "this link expires in 15 minutes."
                ),
                "short": True,
            },
            {
                "title": "`/pass insert <secret>`",
                "value": (
                    "To retrieve the link with the editor to create the "
                    "secret, this link expires in 15 minutes."
                ),
                "short": True,
            },
            {
                "title": "`/pass remove <secret>`",
                "value": ("To remove the secret from the group."),
                "short": True,
            },
            {
                "title": "`/pass configure` or `/pass configure <server_url>`",
                "value": (
                    "To setup the password storage, it is only necessary "
                    "to execute it once."
                ),
                "short": True,
            },
        ]
        return jsonify(
            {
                "attachments": [
                    {
                        "fallback": (
                            "_Usage:_ https://github.com/talpor/password-scale"
                        ),
                        "text": "*_Usage:_*",
                        "fields": fields,
                    }
                ]
            }
        )

    if command[0] == "configure" and len(command) == 2:
        url = command[1]
        if not validators.url(url):
            return error("Invalid URL format, use: https://<domain>")

        if team.url:
            msg = (
                "This team is already configured, you want to replace "
                "the password server?"
            )
            return jsonify(
                {
                    "attachments": [
                        {
                            "fallback": "This team already configured",
                            "text": msg,
                            "callback_id": "configure_password_server",
                            "color": "warning",
                            "actions": [
                                {
                                    "name": "reconfigure_server",
                                    "text": "Yes",
                                    "type": "button",
                                    "value": url,
                                },
                                {
                                    "name": "no_reconfigure",
                                    "text": "No",
                                    "style": "danger",
                                    "type": "button",
                                    "value": "no",
                                },
                            ],
                        }
                    ]
                }
            )

        if not team.register_server(url):
            return error(
                "Unable to retrieve the _public_key_ "
                "from the server".format(team_domain)
            )

        return success("{} team successfully configured!".format(team_domain))

    if command[0] == "configure" and len(command) == 1 or not team.url:
        color = "warning"
        if team.url:
            msg = (
                "*{}* team already have a server configured, if you want to "
                "swap select some of the options below".format(team.name)
            )
        elif command[0] == "configure":
            color = "good"
            msg = "What type of server do you want to use?"
        else:
            msg = (
                "*{}* team does not have a password server configured, select "
                "one of the options below to start.".format(team_domain)
            )

        warning_msg = (
            "This is a test server, any information stored on this server "
            "can be deleted at any moment without prior notice!"
        )
        return jsonify(
            {
                "attachments": [
                    {
                        "fallback": msg,
                        "text": msg,
                        "color": color,
                        "callback_id": "configure_password_server",
                        "actions": [
                            {
                                "name": "use_demo_server",
                                "text": "Use Test Server",
                                "type": "button",
                                "value": "no",
                                "confirm": {
                                    "title": "Confirm",
                                    "text": warning_msg,
                                    "ok_text": "I understand",
                                    "dismiss_text": "No",
                                },
                            },
                            {
                                "text": "Request Private Server",
                                "type": "button",
                                "url": CONFIGURATION_GUIDE_URL,
                            },
                            {
                                "name": "no_configure",
                                "text": "Later",
                                "type": "button",
                                "value": "no",
                            },
                        ],
                    }
                ]
            }
        )
    if command[0] in ["", "list"]:
        try:
            dir_ls = cmd.list(team, channel)
        except SlashpassError as e:
            return error("_{}_".format(e.message))

        if not dir_ls:
            return warning(
                "You have not passwords created for this channel, use "
                "`/pass insert <secret>` to create the first one!"
            )

        return jsonify(
            {
                "attachments": [
                    {
                        "fallback": dir_ls,
                        "text": "Password Store\n{}".format(dir_ls),
                        "footer": (
                            "Use the command `/pass <key_name>` to retrieve "
                            "some of the keys"
                        ),
                    }
                ]
            }
        )

    if command[0] == "insert" and len(command) == 2:
        app = command[1]
        token = cmd.generate_insert_token(team, channel, app)

        msg = "Adding password for *{}* in this channel".format(app)
        return jsonify(
            {
                "attachments": [
                    {
                        "fallback": msg,
                        "text": msg,
                        "footer": "This editor will be valid for 15 minutes",
                        "color": "good",
                        "actions": [
                            {
                                "text": "Open editor",
                                "style": "primary",
                                "type": "button",
                                "url": "{}/insert/{}".format(SLACK_SERVER, token),
                            }
                        ],
                    }
                ]
            }
        )

    if command[0] == "remove" and len(command) == 2:
        app = command[1]
        if cmd.remove(team, channel, app):
            return success("The secret *{}* was removed successfully.".format(app))
        return warning(
            "Looks like the secret *{}* is not in your repository "
            ":thinking_face: use the command `/pass list` "
            "to verify your storage.".format(app)
        )

    if command[0] == "show" and len(command) == 2:
        app = command[1]
    else:
        app = command[0]

    onetime_link = cmd.show(team, channel, app)
    if onetime_link:
        return jsonify(
            {
                "attachments": [
                    {
                        "fallback": "Password: {}".format(onetime_link),
                        "text": "Password for *{}*".format(app),
                        "footer": "This secret will be valid for 15 minutes",
                        "color": "good",
                        "actions": [
                            {
                                "text": "Open secret",
                                "style": "primary",
                                "type": "button",
                                "url": onetime_link,
                            }
                        ],
                    }
                ]
            }
        )
    else:
        return warning("*{}* is not in the password store.".format(app))
