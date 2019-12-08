import datetime
import logging
import utils
from enum import Enum

import db
import requests

import config

logger = logging.getLogger("BACKEND")
cfg = config.init()

# TODO: Use same log string formating everywhere. format(...) vs the same thing wihout format...
class Backend(Enum):
    SONARR = 1
    RADARR = 2
    LIDARR = 3

backend_data = {
        Backend.SONARR: { 'name': 'sonarr', 'api_path': '/api/release/push', 'use_indexer': True },
        Backend.RADARR: { 'name': 'radarr', 'api_path': '/api/release/push', 'use_indexer': True },
        Backend.LIDARR: { 'name': 'lidarr', 'api_path': '/api/v1/release/push', 'use_indexer': False }
        }

@db.db_session
def notify(backends, title, download_url, tracker_name):
    for backend in backends:
        backend_name = backend_data[backend]['name'].capitalize()
        logger.debug("Notifying %s of release from %s: %s @ %s",
                backend_name, tracker_name, title, download_url)
        announced = db.Announced(date=datetime.datetime.now(), title=title,
                                 indexer=tracker_name, torrent=download_url, pvr=backend_name)

        if _notify(backend_data[backend], title, download_url, tracker_name):
            logger.info("%s approved release: %s",
                    backend_name, title)
            snatched = db.Snatched(date=datetime.datetime.now(), title=torrent_title,
                                   indexer=name, torrent=download_link, pvr=pvr_name)
        else:
            logger.debug("%s rejected release: %s", backend_name, title)


def notify_sonarr(title, download_link, indexer):
    _notify(backend_data[Backend.SONARR], title, download_link, indexer)

def notify_radarr(title, download_link, indexer):
    _notify(backend_data[Backend.RADARR], title, download_link, indexer)

def notify_lidarr(title, download_link, indexer):
    _notify(backend_data[Backend.LIDARR], title, download_link, indexer)

def _notify(backend, title, download_url, tracker_name):
    global cfg
    approved = False

    headers = {'X-Api-Key': cfg[backend['name'] + '.apikey']}
    params = {
        'title': utils.replace_spaces(title, '.'),
        'downloadUrl': download_url,
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
