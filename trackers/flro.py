import datetime
import logging
import time

import config
import db
from backend import sonarr_wanted
import utils

cfg = config.init()

############################################################
# Tracker Configuration
############################################################
name = "FLRO"
irc_host = "irc.filelist.ro"
irc_port = 6667
irc_channel = "#announce"
irc_tls = False
irc_tls_verify = False

# these are loaded by init
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

    decolored = utils.strip_irc_color_codes(announcement)

    # extract required information from announcement
    torrent_title = decolored[decolored.find(":")+1:decolored.find("--")].strip()
    torrent_id = utils.get_id(decolored, 0)

    # pass announcement to sonarr
    if torrent_id is not None and torrent_title is not None:
        download_link = get_torrent_link(torrent_id, utils.replace_spaces(torrent_title, '.'))

        announced = db.Announced(date=datetime.datetime.now(), title=utils.replace_spaces(torrent_title, '.'),
                                 indexer=name, torrent=download_link, pvr="Sonarr")

        if delay > 0:
            logger.debug("Waiting %s seconds to check %s", delay, torrent_title)
            time.sleep(delay)

        approved = sonarr_wanted(torrent_title, download_link, name)
        if approved:
            logger.info("Sonarr approved release: %s", torrent_title)
            snatched = db.Snatched(date=datetime.datetime.now(), title=utils.replace_spaces(torrent_title, '.'),
                                   indexer=name, torrent=download_link, pvr="Sonarr")
        else:
            logger.debug("Sonarr rejected release: %s", torrent_title)


# Generate torrent link
def get_torrent_link(torrent_id, torrent_name):
    torrent_link = "http://filelist.ro/download.php?id={}&passkey={}".format(torrent_id,
                                                                             torrent_pass)
    return torrent_link


# Initialize tracker
def init():
    global torrent_pass, delay

    torrent_pass = cfg["{}.torrent_pass".format(name.lower())]
    delay = cfg["{}.delay".format(name.lower())]

    # check torrent_pass was supplied
    if not torrent_pass:
        return False

    return True
