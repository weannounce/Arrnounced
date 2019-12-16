import datetime
import logging
import time
import re
import urllib.parse
from  tracker_config import VarType

import db
from backend import notify, Backend
import utils

logger = logging.getLogger("ANNOUNCE_PARSE")

class Announcement:
    #torrent_name = None
    #torrent_url = None
    #backends = []

    def __init__(self, torrent_name, torrent_url, backends):
        self.torrent_name = torrent_name
        self.torrent_url = torrent_url
        self.backends = backends

def parse(tracker_config, announcement):
    if len(tracker_config.line_patterns) > 0:
        pattern_groups = _parse_line_patterns(tracker_config, announcement)
    elif len(tracker_config.multiline_patterns) > 0:
        pattern_groups = _parse_multiline_patterns(tracker_config, announcement)

    if len(pattern_groups) == 0:
        logger.warning("{}: No match found for '{}'".format(tracker_config.short_name, announcement))
        return None

    torrent_url = _get_torrent_link(tracker_config, pattern_groups)
    backends = _notify_which_backend(tracker_config, pattern_groups)

    return Announcement(pattern_groups["torrentName"], torrent_url, backends)

def _parse_line_patterns(tracker_config, announcement):
    logger.debug("{}: Parsing annoucement '{}'".format(tracker_config.short_name, announcement))
    pattern_groups = {}
    for pattern in tracker_config.line_patterns:
        match = re.search(pattern.regex, announcement)
        if match:
            for i, group in enumerate(pattern.groups, start=1):
                pattern_groups[group] = match.group(i)
            break

    return pattern_groups


def _parse_multiline_patterns(tracker_config, announcement):
    logger.error("Multi line announcements are not supported yet!")


def _get_torrent_link(tracker_config, pattern_groups):
    url = ""
    for var in tracker_config.torrent_url:
        if var.varType is VarType.STRING:
            url = url + var.name
        elif var.varType is VarType.VAR :
            if var.name.startswith("$"):
                url = url + pattern_groups[var.name]
            else:
                url = url + tracker_config[var.name]
        elif var.varType is VarType.VARENC:
            if var.name in pattern_groups:
                var_value = pattern_groups[var.name]
            else:
                var_value = tracker_config[var.name]
            url = url + urllib.parse.quote_plus(var_value)

    logger.debug("Torrent URL: {}".format(url))
    return url

series_re = r"\b(series|tv|television|shows?|sitcoms?|dramas?|soaps?|soapies?)\b"
movie_re = r"\b(movies?|films?|flicks?|motion pictures?|moving pictures?|cinema)\b"
music_re = r"\b(music|audio|songs?|audiobooks?|mp3|flac)\b"
def _notify_which_backend(tracker_config, pattern_groups):
    backends = []
    if tracker_config.notify_sonarr:
        backends.append(Backend.SONARR)
    if tracker_config.notify_radarr:
        backends.append(Backend.RADARR)
    if tracker_config.notify_lidarr:
        backends.append(Backend.LIDARR)

    # TOOO: This probably won't work very well. Replace/Remove.
    # Maybe specify category strings in config.
    if len(backends ) == 0 and "category" in pattern_groups:
        if re.search(series_re, pattern_groups["category"], re.IGNORECASE):
            logger.debug("Matched category Series")
            backends.append(Backend.SONARR)
        if re.search(movie_re, pattern_groups["category"], re.IGNORECASE):
            logger.debug("Matched category Movies")
            backends.append(Backend.RADARR)
        if re.search(music_re, pattern_groups["category"], re.IGNORECASE):
            logger.debug("Matched category Music")
            backends.append(Backend.LIDARR)

    if len(backends) == 0:
        backends = [ Backend.SONARR, Backend.RADARR, Backend.LIDARR ]

    return backends

#@db.db_session
#def _notify_backend(torrent_id, torrent_title, auth_key, torrent_pass, name, pvr_name):
#    if torrent_id is not None and torrent_title is not None:
#        download_link = _get_torrent_link(torrent_id, torrent_title)
#
#        announced = db.Announced(date=datetime.datetime.now(), title=torrent_title,
#                                 indexer=name, torrent=download_link, pvr=pvr_name)
#
#        if delay > 0:
#            logger.debug("Waiting %s seconds to check %s", delay, torrent_title)
#            time.sleep(delay)
#
#        if pvr_name == 'Sonarr':
#            approved = sonarr_wanted(torrent_title, download_link, name)
#        elif pvr_name == 'Radarr':
#            approved = radarr_wanted(torrent_title, download_link, name)
#
#        if approved:
#            logger.info("%s approved release: %s", pvr_name, torrent_title)
#            snatched = db.Snatched(date=datetime.datetime.now(), title=torrent_title,
#                                   indexer=name, torrent=download_link, pvr=pvr_name)
#        else:
#            logger.debug("%s rejected release: %s", pvr_name, torrent_title)
#
#    return

