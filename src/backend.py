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


_backend_data = {
    BackendType.SONARR: {
        "name": "Sonarr",
        "api_path": "/api/release/push",
        "use_indexer": True,
    },
    BackendType.RADARR: {
        "name": "Radarr",
        "api_path": "/api/release/push",
        "use_indexer": True,
    },
    BackendType.LIDARR: {
        "name": "Lidarr",
        "api_path": "/api/v1/release/push",
        "use_indexer": False,
    },
}


# TODO: Make this looks nicer if possible. E.g. some for-loop
def init(config):
    if config["sonarr.apikey"] is None:
        del _backend_data[BackendType.SONARR]
    else:
        _backend_data[BackendType.SONARR]["apikey"] = config["sonarr.apikey"]
        _backend_data[BackendType.SONARR]["url"] = config["sonarr.url"]

    if config["radarr.apikey"] is None:
        del _backend_data[BackendType.RADARR]
    else:
        _backend_data[BackendType.RADARR]["apikey"] = config["radarr.apikey"]
        _backend_data[BackendType.RADARR]["url"] = config["radarr.url"]

    if config["lidarr.apikey"] is None:
        del _backend_data[BackendType.LIDARR]
    else:
        _backend_data[BackendType.LIDARR]["apikey"] = config["lidarr.apikey"]
        _backend_data[BackendType.LIDARR]["url"] = config["lidarr.url"]


def backends_to_string(backends):
    return (
        "/".join(_backend_data[x]["name"] for x in backends)
        if len(backends) > 0
        else "None"
    )


def get_configured_backends():
    return {int(x): _backend_data[x]["name"] for x in (list(_backend_data.keys()))}


def notify_which_backends(tracker_config, announced_category):
    backends = []
    for backend, category_regex in tracker_config.notify_backends.items():
        if category_regex is None:
            backends.append(backend)
        elif announced_category is not None and re.search(
            category_regex, announced_category, re.IGNORECASE
        ):
            backends.append(backend)

    # Return all configured backends if none where specified
    if len(tracker_config.notify_backends) == 0:
        backends = list(_backend_data.keys())

    return backends


def notify(announcement, backends):
    for backend in backends:
        if _notify(
            announcement,
            _backend_data[backend],
        ):
            return _backend_data[backend]["name"]

    return None


def renotify(announcement, backend_id):
    try:
        backend_type = BackendType(backend_id)
    except ValueError as e:
        logger.error("Unknown backend id, %s", e)
        return False, "Unkonwn"

    return (
        _notify(announcement, _backend_data[backend_type]),
        _backend_data[backend_type]["name"],
    )


def _notify(announcement, backend):
    headers = {"X-Api-Key": backend["apikey"]}
    params = {
        "title": announcement.title,
        "downloadUrl": announcement.torrent_url,
        "protocol": "Torrent",
        "publishDate": announcement.date.isoformat(),
    }

    if backend["use_indexer"]:
        params["indexer"] = "Irc" + announcement.indexer

    http_response = None
    try:
        http_response = requests.post(
            url="{}{}".format(backend["url"], backend["api_path"]),
            headers=headers,
            json=params,
        )
        http_response.raise_for_status()
    except HTTPError as e:
        logger.warning("%s: %s", backend["name"], e)
        return False
    except RequestException as e:
        logger.error("%s connection problem", backend["name"])
        logger.error("%s", e)
        return False

    approved = False
    try:
        json_response = http_response.json()
        if "approved" in json_response:
            approved = json_response["approved"]
    except JSONDecodeError as e:
        logger.warning(
            "Could not parse response from %s: %s",
            backend["name"],
            http_response.content,
        )
        logger.warning(e)

    return approved
