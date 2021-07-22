from flask import render_template

import api
import public_key
import slack_action
import slack_command
import slack_oauth
import web
from server import server

server.register_blueprint(api.get_token_data, url_prefix="/t")
server.register_blueprint(public_key.view, url_prefix="/public_key")
server.register_blueprint(slack_action.view, url_prefix="/slack/action")
server.register_blueprint(slack_command.view, url_prefix="/slack/command")
server.register_blueprint(slack_oauth.view, url_prefix="/slack/oauth")
server.register_blueprint(web.insert_view, url_prefix="/insert")
server.register_blueprint(web.root_view, url_prefix="/")


@server.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404
