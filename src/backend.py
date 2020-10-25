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
        http_response = requests.post(
            url="{}{}".format(self.url, self.api_path),
            headers=headers,
            json=self._create_json(announcement),
        )

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

    def __init__(self, apikey, url):
        self.apikey = apikey
        self.url = url
        self.name = Sonarr.__name__


class Radarr(Backend):
    api_path = "/api/release/push"
    use_indexer = True

    def __init__(self, apikey, url):
        self.apikey = apikey
        self.url = url
        self.name = Radarr.__name__


class Lidarr(Backend):
    api_path = "/api/v1/release/push"
    use_indexer = False

    def __init__(self, apikey, url):
        self.apikey = apikey
        self.url = url
        self.name = Lidarr.__name__


_backends = {}


def init(config):
    if config["sonarr.apikey"]:
        sonarr = Sonarr(config["sonarr.apikey"], config["sonarr.url"])
        _backends[BackendType.SONARR] = sonarr

    if config["radarr.apikey"]:
        radarr = Radarr(config["radarr.apikey"], config["radarr.url"])
        _backends[BackendType.RADARR] = radarr

    if config["lidarr.apikey"]:
        lidarr = Lidarr(config["lidarr.apikey"], config["lidarr.url"])
        _backends[BackendType.LIDARR] = lidarr


def get_configured_backends():
    return {int(x): _backends[x].name for x in (list(_backends.keys()))}


def notify_which_backends(tracker_config, announced_category):
    notify_backends = [_backends[bt] for bt in tracker_config.always_notify_backends]

    if announced_category:
        for (
            backend_type,
            category_regex,
        ) in tracker_config.category_notify_backends.items():
            if re.search(category_regex, announced_category, re.IGNORECASE):
                notify_backends.append(_backends[backend_type])

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


def get_backend_from_id(backend_id):
    try:
        backend_type = BackendType(backend_id)
    except ValueError as e:
        logger.error("Unknown backend id, %s", e)
        return None

    return _backends.get(backend_type)


def renotify(announcement, backend):
    return backend.notify(announcement)
