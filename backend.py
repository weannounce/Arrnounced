import datetime
import logging
import requests
import re
from enum import Enum

import config
import utils

logger = logging.getLogger("BACKEND")
cfg = config.init()

# TODO: Use same log string formating everywhere. format(...) vs the same thing wihout format...
class Backend(Enum):
    SONARR = 1
    RADARR = 2
    LIDARR = 3

_backend_data = {
        Backend.SONARR: { 'name': 'Sonarr', 'api_path': '/api/release/push', 'use_indexer': True,
            'configured': cfg['sonarr.apikey'] is not None },
        Backend.RADARR: { 'name': 'Radarr', 'api_path': '/api/release/push', 'use_indexer': True,
            'configured': cfg['radarr.apikey'] is not None },
        Backend.LIDARR: { 'name': 'Lidarr', 'api_path': '/api/v1/release/push', 'use_indexer': False,
            'configured': cfg['lidarr.apikey'] is not None }
        }

def backends_to_string(backends):
    return "/".join(_backend_data[x]['name'] for x in backends)

series_re = r"\b(series|tv|television|shows?|sitcoms?|dramas?|soaps?|soapies?)\b"
movie_re = r"\b(movies?|films?|flicks?|motion pictures?|moving pictures?|cinema)\b"
music_re = r"\b(music|audio|songs?|audiobooks?|mp3|flac)\b"
def notify_which_backends(tracker_config, category):
    backends = tracker_config.notify_backends
    # TODO: Only add configured backends.
    # Print warning if tracker_config.notify_backends contains unconfigured backend

    # TODO: This probably won't work very well. Replace/Remove.
    # Maybe specify category strings in config.
    if len(backends) == 0 and category is not None:
        if re.search(series_re, category, re.IGNORECASE):
            logger.debug("Matched category Series")
            backends.append(Backend.SONARR)
        if re.search(movie_re, category, re.IGNORECASE):
            logger.debug("Matched category Movies")
            backends.append(Backend.RADARR)
        if re.search(music_re, category, re.IGNORECASE):
            logger.debug("Matched category Music")
            backends.append(Backend.LIDARR)

    if len(backends) == 0:
        backends = [ Backend.SONARR, Backend.RADARR, Backend.LIDARR ]

    return backends


def notify(announcement, backends, tracker_name):
    for backend in backends:
        backend_name = _backend_data[backend]['name']

        if _notify(_backend_data[backend], announcement.torrent_name, announcement.torrent_url, tracker_name):
            return _backend_data[backend]['name']

    return None

def notify_sonarr(title, download_link, indexer):
    _notify(_backend_data[Backend.SONARR], title, download_link, indexer)

def notify_radarr(title, download_link, indexer):
    _notify(_backend_data[Backend.RADARR], title, download_link, indexer)

def notify_lidarr(title, download_link, indexer):
    _notify(_backend_data[Backend.LIDARR], title, download_link, indexer)

def _notify(backend, title, torrent_url, tracker_name):
    global cfg
    approved = False

    # TODO: Get cfg_backend section to separate variable first
    headers = {'X-Api-Key': cfg[backend['name'].lower() + '.apikey']}
    params = {
        'title': utils.replace_spaces(title, '.'),
        'downloadUrl': torrent_url,
        'protocol': 'Torrent',
        'publishDate': datetime.datetime.now().isoformat()
    }

    if backend['use_indexer']:
        params['indexer'] = tracker_name

    try:
        resp = requests.post(url="{}{}".format(cfg[backend['name'].lower() + '.url'], backend['api_path']),
                headers=headers, json=params).json()
        if 'approved' in resp:
            approved = resp['approved']
    except ConnectionRefusedError:
        logger.error("%s refused connection", backend['name'])
    except:
        logger.error("Unable to connect to %s", backend['name'])

    return approved
