import datetime
import logging
import utils

import requests

import config

logger = logging.getLogger("RADARR")
logger.setLevel(logging.DEBUG)
cfg = config.init()


def wanted(title, download_link, indexer):
    global cfg
    approved = False

    logger.debug("Notifying Radarr of release from %s: %s @ %s", indexer, title, download_link)

    headers = {'X-Api-Key': cfg['radarr.apikey']}
    params = {
        'title': utils.replace_spaces(title, '.'),
        'downloadUrl': download_link,
        'protocol': 'Torrent',
        'publishDate': datetime.datetime.now().isoformat(),
        'indexer': indexer
    }

    resp = requests.post(url="{}/api/release/push".format(cfg['radarr.url']), headers=headers, params=params).json()
    if 'approved' in resp:
        approved = resp['approved']

    return approved
