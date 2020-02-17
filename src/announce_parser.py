import logging
import re
import urllib.parse

from  tracker_config import VarType

logger = logging.getLogger("ANNOUNCE_PARSER")

class Announcement:
    def __init__(self, torrent_name, torrent_url, category):
        self.torrent_name = torrent_name
        self.torrent_url = torrent_url
        self.category = category

def _ignore_message(ignores, message):
    for ignore in ignores:
        # If message matches an expected regex it will be ignord
        # If it's not expected it works as an inverse, ignore everything which doesn't match.
        if bool(re.search(ignore.regex, message)) == ignore.expected:
            return True
    return False

def parse(tracker_config, message):
    if _ignore_message(tracker_config.ignores, message):
        logger.debug("%s: Message ignored: %s", tracker_config.short_name, message)
        return None

    if len(tracker_config.line_patterns) > 0:
        pattern_groups = _parse_line_patterns(tracker_config, message)
    elif len(tracker_config.multiline_patterns) > 0:
        pattern_groups = _parse_multiline_patterns(tracker_config, message)

    if len(pattern_groups) == 0:
        logger.warning("%s: No match found for '%s'", tracker_config.short_name, message)
        return None

    torrent_url = _get_torrent_link(tracker_config, pattern_groups)

    return Announcement(pattern_groups["torrentName"], torrent_url,
            pattern_groups.get('category'))

def _parse_line_patterns(tracker_config, message):
    logger.debug("%s: Parsing annoucement '%s'", tracker_config.short_name, message)
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

    logger.debug("Torrent URL: %s", url)
    return url
