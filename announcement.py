import datetime
import logging
import time
import re
from  tracker_config import VarType

import db
from backend import notify_sonarr, notify_radarr, notify_lidarr
import utils

#name = "TorrentLeech"
#irc_host = "irc.torrentleech.org"
#irc_port = 7021
#irc_channel = "#tlannounces"
#invite_cmd = "TL-Monkey !invite"
#irc_tls = True
#irc_tls_verify = False
#
## these are loaded by init
#auth_key = None
#torrent_pass = None
#delay = 0

logger = logging.getLogger("ANNOUNCEMENT")


# Parse announcement message
def parse_and_notify(tracker_config, announcement):
    if len(tracker_config.line_patterns) > 0:
        _parse_line_patterns(tracker_config, announcement)
    elif len(tracker_config.multi_line_patterns) > 0:
        _parse_multi_line_patterns(tracker_config, announcement)

@db.db_session
def _parse_line_patterns(tracker_config, announcement):
    pattern_groups = {}
    for pattern in tracker_config.line_patterns:
        match = re.search(pattern.regex, announcement)
        if match:
            for i, group in enumerate(pattern.groups, start=1):
                pattern_groups[group] = match.group(i)
            break
    torrent_url = get_torrent_link(tracker_config, pattern_groups)
    logger.debug("Torrent URL: {}".format(torrent_url))

def _parse_multi_line_patterns(tracker_config, announcement):
    logger.error("Multi line announcements are not supported yet!")

def notify_pvr(torrent_id, torrent_title, auth_key, torrent_pass, name, pvr_name):
    if torrent_id is not None and torrent_title is not None:
        download_link = get_torrent_link(torrent_id, torrent_title)

        announced = db.Announced(date=datetime.datetime.now(), title=torrent_title,
                                 indexer=name, torrent=download_link, pvr=pvr_name)

        if delay > 0:
            logger.debug("Waiting %s seconds to check %s", delay, torrent_title)
            time.sleep(delay)

        if pvr_name == 'Sonarr':
            approved = sonarr_wanted(torrent_title, download_link, name)
        elif pvr_name == 'Radarr':
            approved = radarr_wanted(torrent_title, download_link, name)

        if approved:
            logger.info("%s approved release: %s", pvr_name, torrent_title)
            snatched = db.Snatched(date=datetime.datetime.now(), title=torrent_title,
                                   indexer=name, torrent=download_link, pvr=pvr_name)
        else:
            logger.debug("%s rejected release: %s", pvr_name, torrent_title)

    return


# Generate torrent link
def get_torrent_link(tracker_config, pattern_groups):
    url = ""
    for var in tracker_config.torrent_url:
        if var.varType is VarType.STRING:
            url = url + var.var
        elif var.varType is VarType.VAR :
            if var.var.startswith("$"):
                url = url + pattern_groups[var.var]
            else:
                # TODO: Nicer fetching of this variable variables
                url = url + tracker_config.user_config[var.var]
        elif var.varType is VarType.VARENC:
            # TODO: Difference with VAR?
            pass
    return url
