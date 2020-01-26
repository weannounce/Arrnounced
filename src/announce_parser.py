import datetime
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
    pattern_groups = {}
    if len(tracker_config.line_patterns) > 0:
        pattern_groups = _parse_line_patterns(tracker_config, message)
    elif len(tracker_config.multiline_patterns) > 0:
        pattern_groups = _parse_multiline_patterns(tracker_config, message)
        if pattern_groups is None:
            logger.warning("%s: Not final line", tracker_config.short_name)
            return None

    if len(pattern_groups) == 0:
        if _ignore_message(tracker_config.ignores, message):
            logger.debug("%s: Message ignored: %s", tracker_config.short_name, message)
        else:
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


class MultilineMatch:
    def __init__(self):
        self.time = datetime.datetime.now()
        self.pattern_groups = {}
        self.lines_matched = 1


# TODO: Thread safe global
multiline_matches = {}
def _get_multiline_match(tracker_name, patterns, match_number):
    global multiline_matches
    if tracker_name not in multiline_matches:
        multiline_matches[tracker_name] = []

    if match_number == 0:
        multiline_match = MultilineMatch()
        multiline_matches[tracker_name].append(multiline_match)
        return multiline_match

    for i, multiline_match in enumerate(multiline_matches[tracker_name]):
        logger.debug("lines_matched: %d", multiline_match.lines_matched)
        logger.debug("Checking line %d", match_number)
        if multiline_match.lines_matched == match_number - 1:
            logger.debug("Was the next one")
            if match_number + 1 == len(patterns):
                del multiline_matches[tracker_name][i]
            return multiline_match
        elif multiline_match.lines_matched < match_number:
            for j in range(multiline_match.lines_matched - 1, match_number):
                if j == match_number:
                    if j + 1 == len(patterns):
                        del multiline_matches[tracker_name][i]
                    return multiline_match
                elif not patterns[j].optional:
                    break

    return None


def _parse_multiline_patterns(tracker_config, message):
    logger.debug("%s: Parsing multiline annoucement '%s'", tracker_config.short_name, message)
    for i, pattern in enumerate(tracker_config.multiline_patterns, start=0):
        match = re.search(pattern.regex, message)
        if match:
            multiline_match = _get_multiline_match(tracker_config.short_name,
                    tracker_config.multiline_patterns, i)
            if multiline_match  is None:
                logger.debug("Did not find it")
            else:
                logger.debug("Found it")
                multiline_match.lines_matched = i
                for j, group in enumerate(pattern.groups, start=1):
                    multiline_match.pattern_groups[group] = match.group(j)
                # Or if ends with optional. And remove from list
                if i + 1 == len(tracker_config.multiline_patterns):
                    return multiline_match.pattern_groups

            return None
    return {}


def _get_torrent_link(tracker_config, pattern_groups):
    url = ""
    for var in tracker_config.torrent_url:
        if var.varType is VarType.STRING:
            url = url + var.name
        elif var.varType is VarType.VAR:
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
