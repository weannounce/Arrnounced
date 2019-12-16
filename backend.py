import datetime
import logging
import requests
from enum import Enum

import config
import utils

logger = logging.getLogger("BACKEND")
cfg = config.init()

# TODO: Use same log string formating everywhere. format(...) vs the same thing wihout format...
class Backend(Enum):
    SONARR = "Sonarr"
    RADARR = "Radarr"
    LIDARR = "Lidarr"

backend_data = {
        Backend.SONARR: { 'name': 'sonarr', 'api_path': '/api/release/push', 'use_indexer': True },
        Backend.RADARR: { 'name': 'radarr', 'api_path': '/api/release/push', 'use_indexer': True },
        Backend.LIDARR: { 'name': 'lidarr', 'api_path': '/api/v1/release/push', 'use_indexer': False }
        }

def notify(announcement, tracker_name):
    for backend in announcement.backends:
        backend_name = backend_data[backend]['name'].capitalize()

        if _notify(backend_data[backend], announcement.torrent_name, announcement.torrent_url, tracker_name):
            return True, backend

    return False, None

def notify_sonarr(title, download_link, indexer):
    _notify(backend_data[Backend.SONARR], title, download_link, indexer)

def notify_radarr(title, download_link, indexer):
    _notify(backend_data[Backend.RADARR], title, download_link, indexer)

def notify_lidarr(title, download_link, indexer):
    _notify(backend_data[Backend.LIDARR], title, download_link, indexer)

def _notify(backend, title, torrent_url, tracker_name):
    global cfg
    approved = False

    headers = {'X-Api-Key': cfg[backend['name'] + '.apikey']}
    params = {
        'title': utils.replace_spaces(title, '.'),
        'downloadUrl': torrent_url,
        'protocol': 'Torrent',
        'publishDate': datetime.datetime.now().isoformat()
    }

    if backend['use_indexer']:
        params['indexer'] = tracker_name

    try:
        resp = requests.post(url="{}{}".format(cfg[backend['name'] + '.url'], backend['api_path']),
                headers=headers, json=params).json()
        if 'approved' in resp:
            approved = resp['approved']
    except ConnectionRefusedError:
        logger.error("%s refused connection", backend['name'])
    except:
        logger.error("Unable to connect to %s", backend['name'])

    return approved
