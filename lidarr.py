import datetime
import logging
import utils

import requests

import config

logger = logging.getLogger("LIDARR")
logger.setLevel(logging.DEBUG)
cfg = config.init()


def wanted(title, download_link, indexer):
    global cfg
    approved = False

    logger.debug("Notifying Lidarr of release from %s: %s @ %s", indexer, title, download_link)

    headers = {'X-Api-Key': cfg['lidarr.apikey']}
    params = {
        'title': utils.replace_spaces(title, '.'),
        'downloadUrl': download_link,
        'protocol': 'Torrent',
        'publishDate': datetime.datetime.now().isoformat()
    }

    resp = requests.post(url="{}/api/v1/release/push".format(cfg['lidarr.url']), headers=headers, json=params).json()
    if 'approved' in resp:
        approved = resp['approved']

    return approved
