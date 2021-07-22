from flask import Blueprint
from server import public_key

view = Blueprint('public_key', __name__)


@view.route('', methods=['GET'])
def get_public_key():
    return public_key
