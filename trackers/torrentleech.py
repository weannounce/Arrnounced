import datetime
import logging
import time

import config
import db
from backend import sonarr_wanted, radarr_wanted
import utils

cfg = config.init()

############################################################
# Tracker Configuration
############################################################
name = "TorrentLeech"
irc_host = "irc.torrentleech.org"
irc_port = 7021
irc_channel = "#tlannounces"
invite_cmd = "TL-Monkey !invite"
irc_tls = True
irc_tls_verify = False

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

    decolored = utils.strip_irc_color_codes(announcement)
    if 'New Torrent Announcement: <' not in decolored:
        return

    # extract required information from announcement
    torrent_title = utils.replace_spaces(utils.substr(decolored, 'Name:\'', '\' uploaded', True), '.')
    torrent_id = decolored.split('/')[-1]


    if '<TV ::' in decolored:
        notify_pvr(torrent_id, torrent_title, auth_key, torrent_pass, name, 'Sonarr')
    elif '<Movies ::' in decolored:
        notify_pvr(torrent_id, torrent_title, auth_key, torrent_pass, name, 'Radarr')



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
def get_torrent_link(torrent_id, torrent_name):
    torrent_link = "https://www.torrentleech.org/rss/download/{}/{}/{}.torrent".format(torrent_id,
                                                                                        auth_key,
                                                                                        torrent_name)

    return torrent_link


# Initialize tracker
def init():
    global auth_key, torrent_pass, delay

    auth_key = cfg["{}.auth_key".format(name.lower())]
    torrent_pass = cfg["{}.torrent_pass".format(name.lower())]
    delay = cfg["{}.delay".format(name.lower())]

    # check torrent_pass was supplied
    if not auth_key:
        return False

    return True
