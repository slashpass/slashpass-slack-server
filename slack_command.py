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
        team_id = data["team_id"]
        team_domain = data["team_domain"]
        channel = data["channel_id"]
    except KeyError:
        abort(400)

    # ensuring that the request comes from slack
    if not valid_slack_request(request):
        return abort(403)

    team = db.session.query(Team).filter_by(team_id=team_id).first()
    if not team:
        return error(
            "You are not registered in our proxy server, try removig the app "
            "and adding it to slack again."
        )

    if command[0] == "help":
        fields = [
            {
                "title": "`/pass` _or_ `/pass list`",
                "value": "List the available passwords in the channel.",
                "short": True,
            },
            {
                "title": "`/pass <secret>` _or_ `/pass show <secret>`",
                "value": (
                    "Show the one time use link with the secret content, "
                    "this link expires in 15 minutes."
                ),
                "short": True,
            },
            {
                "title": "`/pass insert <secret>`",
                "value": (
                    "Show the link with the editor to create the new secret, "
                    "this link expires in 15 minutes."
                ),
                "short": True,
            },
            {
                "title": "`/pass remove <secret>`",
                "value": ("Delete the secret from the channel."),
                "short": True,
            },
            {
                "title": "`/pass configure <private_server_url>` _or_ `/pass configure`",
                "value": (
                    "Configure the password server, "
                    "it is only necessary to execute it once."
                ),
                "short": True,
            },
            {
                "title": "`/pass help`",
                "value": "Show this dialog :robot_face:",
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
                "You already have a password server configured, "
                "do you want to replace the current server?"
            )
            return jsonify(
                {
                    "attachments": [
                        {
                            "fallback": "You already have a password server configured",
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
            return error("Unable to retrieve the _public_key_ from the server")

        return success(f"{team_domain} team successfully configured!")

    if command[0] == "configure" and len(command) == 1 or not team.url:
        color = "warning"
        if team.url:
            msg = (
                f"*{team.team_name}* team already have a server configured, if you want to "
                f"swap select some of the options below"
            )
        elif command[0] == "configure":
            color = "good"
            msg = "What type of server do you want to use?"
        else:
            msg = (
                f"*{team_domain}* team does not have a slashpass server configured, select "
                f"one of the options below to start."
            )

        warning_msg = (
            "You are choosing a TEST server, any information stored on this server "
            "will be deleted at any moment without prior notice!"
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
            return error(f"_{e.message}_")

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
                        "text": f"Password Store\n{dir_ls}",
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

        msg = f"Adding password for *{app}* in this channel"
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
                                "url": f"{SLACK_SERVER}/insert/{token}",
                            }
                        ],
                    }
                ]
            }
        )

    if command[0] == "remove" and len(command) == 2:
        app = command[1]
        if cmd.remove(team, channel, app):
            return success(f"The secret *{app}* was removed successfully.")
        return warning(
            f"Looks like the secret *{app}* is not in your repository "
            f":thinking_face: use the command `/pass list` "
            f"to verify your storage."
        )

    app = command[1] if command[0] == "show" and len(command) == 2 else command[0]
    if onetime_link := cmd.show(team, channel, app):
        return jsonify(
            {
                "attachments": [
                    {
                        "fallback": "Password: {onetime_link}",
                        "text": "Password for *{app}*",
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
        return warning(f"*{app}* is not in the password store.")
