import pickle

from flask import Blueprint, abort

from server import cache

get_token_data = Blueprint("get_token_data", __name__)


@get_token_data.route("/<token>", methods=["GET"])
def get_token(token):
    token = str(token)
    if token not in cache:
        abort(404)

    obj = pickle.loads(cache[token])
    return obj["path"]
