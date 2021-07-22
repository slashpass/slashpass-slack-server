import requests

from flask import Blueprint, abort, request, render_template
from urllib.parse import urlencode

from environ import SLACK_CLIENT_ID, SLACK_CLIENT_SECRET
from server import db, Team, sentry


view = Blueprint('slack_oauth', __name__)


@view.route('', methods=['GET'])
def slack_oauth():
    if 'code' not in request.args:
        abort(400)

    oauth_access_url = '{}{}'.format(
        'https://slack.com/api/oauth.access?', urlencode({
            'client_id': SLACK_CLIENT_ID,
            'client_secret': SLACK_CLIENT_SECRET,
            'code': request.args['code']
        })
    )
    response = requests.get(oauth_access_url).json()
    if 'ok' not in response or not response['ok']:
        sentry.captureMessage(response)
        abort(403)

    slack_id = response['team_id']

    if not db.session.query(Team).filter_by(slack_id=slack_id).first():
        # not storing the `access_token` at this time is not necessary
        new_team = Team(
            slack_id=slack_id,
            name=response['team_name']
            # access_token=response.json()['access_token'],
        )
        db.session.add(new_team)
        db.session.commit()
    message = ('The Slack application was installed successfully, go to your '
               'Slack group and try it!')
    return render_template('success.html', message=message)
