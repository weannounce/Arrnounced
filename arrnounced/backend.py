import logging
import re
from asyncio import Lock
from functools import reduce
from operator import and_

from arrnounced.eventloop_utils import eventloop_util
from arrnounced.session_provider import SessionProvider


logger = logging.getLogger("BACKEND")


def _extract_approval(json_response, backend_name):
    try:
        approvals = (
            e["approved"]
            for e in (
                json_response if isinstance(json_response, list) else [json_response]
            )
        )
        # Not sure why the response is a list when the push is a single item.
        # Reducing all the values with "and" seems reasonable
        return reduce(and_, approvals)
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
                url=f"{self.url}{self.push_path}",
                headers={"X-Api-Key": self.apikey},
                json=self._create_json(announcement),
            )

        return json_response

    async def notify(self, announcement):
        json_response = await self._send_notification(announcement)
        if not json_response:
            return False
        return _extract_approval(json_response, self.name)

    async def check(self):
        json_response = await SessionProvider.get(
            url=f"{self.url}{self.diskspace_path}",
            headers={"X-Api-Key": self.apikey},
        )
        result = json_response is not None
        logger.debug("%s access: %s", self.name, "granted" if result else "failed")
        return result


class V3Api(Backend):
    push_path_v3 = "/api/v3/release/push"
    diskspace_path_v3 = "/api/v3/diskspace"
    push_path_legacy = "/api/release/push"
    diskspace_path_legacy = "/api/diskspace"

    def _create_json(self, announcement):
        params = super()._create_json(announcement)
        params["indexer"] = "Irc" + announcement.indexer

        return params

    def __init__(self, user_backend):
        self._set_v3()
        super().__init__(user_backend)

    def _set_v3(self):
        self.push_path = self.push_path_v3
        self.diskspace_path = self.diskspace_path_v3

    def _set_legacy(self):
        self.push_path = self.push_path_legacy
        self.diskspace_path = self.diskspace_path_legacy

    async def check(self):
        if await super().check():
            return True

        logger.info("%s: Falling back to legacy API", self.name)
        self._set_legacy()
        if await super().check():
            return True

        # Neither worked, setting v3 as default
        self._set_v3()
        return False


class Sonarr(V3Api): ...


class Radarr(V3Api): ...


class Lidarr(Backend):
    push_path = "/api/v1/release/push"
    diskspace_path = "/api/v1/diskspace"


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


def check():
    for backend in _backends.values():
        eventloop_util.run(backend.check())
