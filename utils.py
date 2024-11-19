import hmac
import hashlib
import time
import urllib

from flask import jsonify

from environ import SIGNING_SECRET


def _slack_msg(msg, color):
    return jsonify({"attachments": [{"fallback": msg, "text": msg, "color": color}]})


def warning(msg):
    return _slack_msg(msg, "warning")


def success(msg):
    return _slack_msg(msg, "good")


def error(msg):
    return _slack_msg(msg, "danger")


def info(msg):
    return jsonify({"attachments": [{"fallback": msg, "text": msg}]})


def valid_slack_request(request):
    slack_signing_secret = SIGNING_SECRET
    timestamp = request.headers["X-Slack-Request-Timestamp"]

    request_body = urllib.parse.urlencode(dict(request.form))

    sig_basestring = f"v0:{timestamp}:{request_body}"

    if abs(time.time() - float(timestamp)) > 60:
        # The request timestamp is more than one minutes from local time.
        # It could be a replay attack, so let's ignore it.
        return False

    signature = (
        "v0="
        + hmac.new(
            bytes(slack_signing_secret, "UTF-8"),
            bytes(sig_basestring, "UTF-8"),
            hashlib.sha256,
        ).hexdigest()
    )

    slack_signature = request.headers["X-Slack-Signature"]
    return signature == slack_signature
