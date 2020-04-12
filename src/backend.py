import datetime
import logging
import re
import requests
from enum import Enum
from json.decoder import JSONDecodeError
from requests.exceptions import HTTPError, RequestException


logger = logging.getLogger("BACKEND")


class Backend(Enum):
    SONARR = 1
    RADARR = 2
    LIDARR = 3


_backend_data = {
    Backend.SONARR: {
        "name": "Sonarr",
        "api_path": "/api/release/push",
        "use_indexer": True,
    },
    Backend.RADARR: {
        "name": "Radarr",
        "api_path": "/api/release/push",
        "use_indexer": True,
    },
    Backend.LIDARR: {
        "name": "Lidarr",
        "api_path": "/api/v1/release/push",
        "use_indexer": False,
    },
}


# TODO: Make this looks nicer if possible. E.g. some for-loop
def init(config):
    if config["sonarr.apikey"] is None:
        del _backend_data[Backend.SONARR]
    else:
        _backend_data[Backend.SONARR]["apikey"] = config["sonarr.apikey"]
        _backend_data[Backend.SONARR]["url"] = config["sonarr.url"]

    if config["radarr.apikey"] is None:
        del _backend_data[Backend.RADARR]
    else:
        _backend_data[Backend.RADARR]["apikey"] = config["radarr.apikey"]
        _backend_data[Backend.RADARR]["url"] = config["radarr.url"]

    if config["lidarr.apikey"] is None:
        del _backend_data[Backend.LIDARR]
    else:
        _backend_data[Backend.LIDARR]["apikey"] = config["lidarr.apikey"]
        _backend_data[Backend.LIDARR]["url"] = config["lidarr.url"]


def _string_to_backend(backend_name):
    for backend in _backend_data.keys():
        if _backend_data[backend]["name"] == backend_name:
            return backend
    return None


def backends_to_string(backends):
    return (
        "/".join(_backend_data[x]["name"] for x in backends)
        if len(backends) > 0
        else "None"
    )


def get_configured_backends():
    return [_backend_data[x]["name"] for x in (list(_backend_data.keys()))]


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


def notify(announcement, backends, tracker_name):
    for backend in backends:
        if _notify(
            _backend_data[backend],
            announcement.torrent_name,
            announcement.torrent_url,
            "Irc" + tracker_name,
        ):
            return _backend_data[backend]["name"]

    return None


def renotify(backend_name, title, download_link, indexer):
    backend = _string_to_backend(backend_name)
    if backend is None:
        logger.warning("Unknown backend %s", backend_name)
        return False

    return _notify(_backend_data[backend], title, download_link, "Irc" + indexer)


def _notify(backend, title, torrent_url, indexer):
    headers = {"X-Api-Key": backend["apikey"]}
    params = {
        "title": title,
        "downloadUrl": torrent_url,
        "protocol": "Torrent",
        "publishDate": datetime.datetime.now().isoformat(),
    }

    if backend["use_indexer"]:
        params["indexer"] = indexer

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
