import pickle
import random
import string

import requests
from rsa import decrypt

ERRMSG = "Communication problem with the remote server"


class SlashpassError(Exception):
    def __init__(self, message):
        self.message = message


class SlashpassCMD(object):
    def list(self, team, channel):
        try:
            response = requests.post(team.api(f"list/{channel}"))
        except requests.exceptions.ConnectionError as e:
            raise SlashpassError(f"Timeout: {ERRMSG}") from e
        size = 344  # assuming 2048 bits key

        msg = b"".join(
            decrypt(response.text[i : i + size], self.private_key)
            for i in range(0, len(response.text), size)
        )

        if msg == b"":
            return ""
        elif msg is None:
            raise SlashpassError("Decryption error")

        item_list = msg.decode("utf-8")
        n = item_list.count(channel)
        # formatting response
        return item_list.replace(f"{channel}/", "├─ ", n - 1).replace(
            f"{channel}/", "└─ "
        )

    def generate_insert_token(self, team, channel, app):
        token = "".join(
            random.SystemRandom().choice(string.ascii_uppercase + string.digits)
            for _ in range(6)
        )

        self.cache.set(
            token,
            pickle.dumps(
                {
                    "path": f"{channel}/{app}",
                    "team_id": team.id,
                    "url": team.api("insert"),
                }
            ),
            900,
        )  # expires in 15 minutes

        return token

    def insert(self, token, secret):
        obj = pickle.loads(self.cache[token])
        path = obj["path"]
        url = obj["url"]
        response = requests.post(url, data={"path": path, "secret": secret})

        if response.status_code != requests.codes.ok:
            raise SlashpassError(f"Error {response.status_code}: {ERRMSG}")

        self.cache.delete(token)

    def remove(self, team, channel, app):
        response = requests.post(
            team.api("remove"), data={"channel": channel, "app": app}
        )
        return response.status_code == requests.codes.ok

    def show(self, team, channel, app):
        response = requests.post(
            team.api("onetime_link"), data={"secret": f"{channel}/{app}"}
        )

        if response.status_code == requests.codes.ok:
            return decrypt(response.text, self.private_key).decode("utf-8")
        elif response.status_code == requests.codes.not_found:
            return None

        raise SlashpassError("Unexpected error")

    def __init__(self, cache, private_key):
        self.cache = cache
        self.private_key = private_key
