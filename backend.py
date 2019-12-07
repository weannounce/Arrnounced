import datetime
import logging
import utils

import requests

import config

logger = logging.getLogger("BACKEND")
cfg = config.init()

sonarr_backend = { 'name': 'sonarr', 'api_path': '/api/release/push', 'use_indexer': True }
radarr_backend = { 'name': 'radarr', 'api_path': '/api/release/push', 'use_indexer': True }
lidarr_backend = { 'name': 'lidarr', 'api_path': '/api/v1/release/push', 'use_indexer': False }

def notify_sonarr(title, download_link, indexer):
    __wanted(sonarr_backend, title, download_link, indexer)

def notify_radarr(title, download_link, indexer):
    __wanted(radarr_backend, title, download_link, indexer)

def notify_lidarr(title, download_link, indexer):
    __wanted(lidarr_backend, title, download_link, indexer)

def __wanted(backend, title, download_link, indexer):
    global cfg
    approved = False

    logger.info("Notifying %s of release from %s: %s @ %s",
            backend['name'].capitalize(), indexer, title, download_link)

    headers = {'X-Api-Key': cfg[backend['name'] + '.apikey']}
    params = {
        'title': utils.replace_spaces(title, '.'),
        'downloadUrl': download_link,
        'protocol': 'Torrent',
        'publishDate': datetime.datetime.now().isoformat()
    }

    if backend['use_indexer']:
        params['indexer'] = indexer

    resp = requests.post(url="{}/api/release/push".format(cfg[backend['name'] + '.url']), headers=headers, json=params).json()
    if 'approved' in resp:
        approved = resp['approved']

    return approved
