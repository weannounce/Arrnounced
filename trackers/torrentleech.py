import datetime
import logging

import config
import db
import sonarr
import radarr
import utils

cfg = config.init()

############################################################
# Tracker Configuration
############################################################
name = "TorrentLeech"
irc_host = "irc.torrentleech.org"
irc_port = 7021
irc_channel = "#tlannounces"
irc_tls = True
irc_tls_verify = False

# these are loaded by init
auth_key = None
torrent_pass = None

logger = logging.getLogger(name.upper())
logger.setLevel(logging.DEBUG)


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
    torrent_title = utils.substr(decolored, 'Name:\'', '\' uploaded', True)
    torrent_title = utils.replace_spaces(torrent_title, '.')
    torrent_id = decolored.split('/')[-1]

    if '<TV ::' in decolored:
        # pass announcement to sonarr
        if torrent_id is not None and torrent_title is not None:
            download_link = get_torrent_link(torrent_id, auth_key, torrent_title)

            announced = db.Announced(date=datetime.datetime.now(), title=torrent_title,
                                     indexer=name, torrent=download_link, pvr='sonarr')
            approved = sonarr.wanted(torrent_title, download_link, name)
            if approved:
                logger.debug("Sonarr approved release: %s", torrent_title)
                snatched = db.Snatched(date=datetime.datetime.now(), title=torrent_title,
                                       indexer=name, torrent=download_link, pvr='sonarr')
            else:
                logger.debug("Sonarr rejected release: %s", torrent_title)

    elif '<Movies ::' in decolored:
        # pass announcement to radarr
        if torrent_id is not None and torrent_title is not None:
            download_link = get_torrent_link(torrent_id, auth_key, torrent_title)

            announced = db.Announced(date=datetime.datetime.now(), title=torrent_title,
                                     indexer=name, torrent=download_link, pvr='radarr')
            approved = radarr.wanted(torrent_title, download_link, name)
            if approved:
                logger.debug("Radarr approved release: %s", torrent_title)
                snatched = db.Snatched(date=datetime.datetime.now(), title=torrent_title,
                                       indexer=name, torrent=download_link, pvr='radarr')
            else:
                logger.debug("Radarr rejected release: %s", torrent_title)


# Generate torrent link
def get_torrent_link(torrent_id, auth_key, torrent_name):
    torrent_link = "https://www.torrentleech.org/rss/download/{}/{}/{}.torrent".format(torrent_id,
                                                                                        auth_key,
                                                                                        torrent_name)
                                                                                              
    return torrent_link


# Initialize tracker
def init():
    global auth_key, torrent_pass

    auth_key = cfg["{}.auth_key".format(name.lower())]
    torrent_pass = cfg["{}.torrent_pass".format(name.lower())]

    # check torrent_pass was supplied
    if not auth_key:
        return False

    return True
