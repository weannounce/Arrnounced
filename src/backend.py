import logging
import re
import requests
from enum import IntEnum
from json.decoder import JSONDecodeError
from requests.exceptions import HTTPError, RequestException


logger = logging.getLogger("BACKEND")


class BackendType(IntEnum):
    SONARR = 1
    RADARR = 2
    LIDARR = 3


def _extract_approval(http_response, backend_name):
    try:
        json_response = http_response.json()
        return "approved" in json_response and json_response["approved"]
    except JSONDecodeError as e:
        logger.warning(
            "Could not parse response from %s: %s",
            backend_name,
            http_response.content,
        )
        logger.warning(e)
        return False


class Backend:
    def __init__(self, user_backend):
        self.apikey = user_backend.apikey
        self.url = user_backend.url
        self.name = user_backend.name

    def _create_json(self, announcement):
        params = {
            "title": announcement.title,
            "downloadUrl": announcement.torrent_url,
            "protocol": "Torrent",
            "publishDate": announcement.date.isoformat(),
        }

        if self.use_indexer:
            params["indexer"] = "Irc" + announcement.indexer
        return params

    def _send_notification(self, announcement):
        headers = {"X-Api-Key": self.apikey}
        try:
            http_response = requests.post(
                url="{}{}".format(self.url, self.api_path),
                headers=headers,
                json=self._create_json(announcement),
            )
        except OSError as e:
            logger.error("%s %s: %s", self.name, type(e).__name__, e)
            return None

        try:
            http_response.raise_for_status()
        except HTTPError as e:
            logger.warning("%s: %s", self.name, e)
            return None
        except RequestException as e:
            logger.error("%s connection problem", self.name)
            logger.error("%s", e)
            return None

        return http_response

    def notify(self, announcement):
        http_response = self._send_notification(announcement)
        if not http_response:
            return False
        return _extract_approval(http_response, self.name)


class Sonarr(Backend):
    api_path = "/api/release/push"
    use_indexer = True


class Radarr(Backend):
    api_path = "/api/release/push"
    use_indexer = True


class Lidarr(Backend):
    api_path = "/api/v1/release/push"
    use_indexer = False


backend_mapping = {
    "sonarr": Sonarr,
    "radarr": Radarr,
    "lidarr": Lidarr,
}


_backends = {}


def init(user_backends):
    for user_backend in user_backends:
        _backends[user_backend.name] = backend_mapping[user_backend.type](user_backend)


def get_configured_backends():
    return list(_backends.keys())


def notify_which_backends(tracker_config, announced_category):
    notify_backends = [_backends[b] for b in tracker_config.always_notify_backends]

    if announced_category:
        for (
            backend_name,
            category_regex,
        ) in tracker_config.category_notify_backends.items():
            if re.search(category_regex, announced_category, re.IGNORECASE):
                notify_backends.append(_backends[backend_name])

    # Return all configured backends if none where specified
    if (
        len(tracker_config.always_notify_backends) == 0
        and len(tracker_config.category_notify_backends) == 0
    ):
        notify_backends = list(_backends.values())

    return notify_backends


def notify(announcement, backends):
    for backend in backends:
        if backend.notify(announcement):
            return backend

    return None


def get_backend(backend_name):
    return _backends.get(backend_name)


def renotify(announcement, backend):
    return backend.notify(announcement)
