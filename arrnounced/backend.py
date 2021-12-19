import logging
import re
from asyncio import Lock

from arrnounced.session_provider import SessionProvider


logger = logging.getLogger("BACKEND")


def _extract_approval(json_response, backend_name):
    try:
        return json_response["approved"]
    except TypeError:
        logger.warning("No valid JSON reply from %s", backend_name, exc_info=True)
    except KeyError:
        logger.warning("No approval info in reply from %s", backend_name, exc_info=True)
    return False


class Backend:
    def __init__(self, user_backend):
        self.apikey = user_backend.apikey
        self.url = user_backend.url
        self.name = user_backend.name
        self.lock = Lock()

    def _create_json(self, announcement):
        params = {
            "title": announcement.title,
            "downloadUrl": announcement.torrent_url,
            "protocol": "Torrent",
            "publishDate": announcement.date.isoformat(),
        }

        return params

    async def _send_notification(self, announcement):
        # Mitigate https://github.com/Sonarr/Sonarr/issues/2975
        async with Lock():
            json_response = await SessionProvider.post(
                url=f"{self.url}{self.api_path}",
                headers={"X-Api-Key": self.apikey},
                json=self._create_json(announcement),
            )

        return json_response

    async def notify(self, announcement):
        json_response = await self._send_notification(announcement)
        if not json_response:
            return False
        return _extract_approval(json_response, self.name)


class UseIndexer(Backend):
    def _create_json(self, announcement):
        params = super()._create_json(announcement)
        params["indexer"] = "Irc" + announcement.indexer

        return params


class Sonarr(UseIndexer):
    api_path = "/api/release/push"


class Radarr(UseIndexer):
    api_path = "/api/release/push"


class Lidarr(Backend):
    api_path = "/api/v1/release/push"


backend_mapping = {
    "sonarr": Sonarr,
    "radarr": Radarr,
    "lidarr": Lidarr,
}


_backends = {}


def init(user_backends):
    for user_backend in user_backends:
        _backends[user_backend.name] = backend_mapping[user_backend.type](user_backend)


async def stop():
    await SessionProvider.close_session()


def get_configured_backends():
    return list(_backends.keys())


def notify_which_backends(tracker, announced_category):
    notify_backends = [_backends[b] for b in tracker.config.always_notify_backends]

    if announced_category:
        for (
            backend_name,
            category_regex,
        ) in tracker.config.category_notify_backends.items():
            if re.search(category_regex, announced_category, re.IGNORECASE):
                notify_backends.append(_backends[backend_name])

    # Return all configured backends if none where specified
    if (
        len(tracker.config.always_notify_backends) == 0
        and len(tracker.config.category_notify_backends) == 0
    ):
        notify_backends = list(_backends.values())

    return notify_backends


async def notify(announcement, backends):
    for backend in backends:
        if await backend.notify(announcement):
            return backend

    return None


def get_backend(backend_name):
    return _backends.get(backend_name)


async def renotify(announcement, backend):
    return await backend.notify(announcement)
