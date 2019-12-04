import datetime
import logging
import time
import re

import config
import db
from backend import lidarr_wanted
import utils

cfg = config.init()

############################################################
# Tracker Configuration
############################################################
name = "Red"
irc_port = 6697
irc_host = "irc.scratch-network.net"
irc_channel = "#red-announce"
inviter = "Drone"
invite_cmd = "enter " + irc_channel
irc_tls = True
irc_tls_verify = False
parse_re = r"^(.+)\s+-\s+https?:.*[&?]id=.*https?:.*[&?]id=(\d+)\s"

# these are loaded by init
auth_key = None
torrent_pass = None
delay = 0

logger = logging.getLogger(name.upper())

############################################################
# Tracker Framework (all trackers must follow)
############################################################
# Parse announcement message
@db.db_session
def parse(announcement):
    global name

    torrent_title = None
    torrent_id = None

    match = re.search(parse_re, announcement)
    if match:
        torrent_title = match.group(1)
        torrent_id = match.group(2)

    # pass announcement to lidarr
    if torrent_id is not None and torrent_title is not None:
        download_link = get_torrent_link(torrent_id, utils.replace_spaces(torrent_title, '.'))

        announced = db.Announced(date=datetime.datetime.now(), title=utils.replace_spaces(torrent_title, '.'),
                                 indexer=name, torrent=download_link, pvr="Lidarr")

        if delay > 0:
            logger.debug("Waiting %s seconds to check %s", delay, torrent_title)
            time.sleep(delay)

        approved = lidarr_wanted(torrent_title, download_link, name)
        if approved:
            logger.info("Lidarr approved release: %s", torrent_title)
            snatched = db.Snatched(date=datetime.datetime.now(), title=utils.replace_spaces(torrent_title, '.'),
                                   indexer=name, torrent=download_link, pvr="Lidarr")
        else:
            logger.debug("Lidarr rejected release: %s", torrent_title)


# Generate torrent link
def get_torrent_link(torrent_id, torrent_name):
    torrent_link = "https://redacted.ch/torrents.php?action=download&id={}&authkey={}&torrent_pass={}" \
        .format(torrent_id, auth_key, torrent_pass)

    return torrent_link


# Initialize tracker
def init():
    global auth_key, torrent_pass, delay

    auth_key = cfg["{}.auth_key".format(name.lower())]
    torrent_pass = cfg["{}.torrent_pass".format(name.lower())]
    delay = cfg["{}.delay".format(name.lower())]

    # check auth_key && torrent_pass was supplied
    if not auth_key or not torrent_pass:
        return False

    return True
