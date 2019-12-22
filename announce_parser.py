import datetime
import logging
import time
import re
import urllib.parse
from  tracker_config import VarType

import db
from backend import notify, Backend
import utils

logger = logging.getLogger("ANNOUNCE_PARSER")

class Announcement:
    def __init__(self, torrent_name, torrent_url, category):
        self.torrent_name = torrent_name
        self.torrent_url = torrent_url
        self.category = category

def parse(tracker_config, message):
    if len(tracker_config.line_patterns) > 0:
        pattern_groups = _parse_line_patterns(tracker_config, message)
    elif len(tracker_config.multiline_patterns) > 0:
        pattern_groups = _parse_multiline_patterns(tracker_config, message)

    if len(pattern_groups) == 0:
        logger.warning("{}: No match found for '{}'".format(tracker_config.short_name, message))
        return None

    torrent_url = _get_torrent_link(tracker_config, pattern_groups)

    return Announcement(pattern_groups["torrentName"], torrent_url,
            pattern_groups.get('category'))

def _parse_line_patterns(tracker_config, message):
    logger.debug("{}: Parsing annoucement '{}'".format(tracker_config.short_name, message))
    pattern_groups = {}
    for pattern in tracker_config.line_patterns:
        match = re.search(pattern.regex, message)
        if match:
            for i, group in enumerate(pattern.groups, start=1):
                pattern_groups[group] = match.group(i)
            break

    return pattern_groups


def _parse_multiline_patterns(tracker_config, message):
    logger.error("Multi line announcements are not supported yet!")
    return {}


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
