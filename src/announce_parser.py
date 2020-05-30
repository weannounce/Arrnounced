import time
import logging
import re

from itertools import filterfalse
from multiprocessing import Lock

logger = logging.getLogger("ANNOUNCE_PARSER")


def parse(tracker_config, message):
    pattern_groups = {}
    if len(tracker_config.line_patterns) > 0:
        _, pattern_groups = _parse_message(tracker_config.line_patterns, message)
    elif len(tracker_config.multiline_patterns) > 0:
        pattern_groups = _parse_multiline_patterns(tracker_config, message)
        if pattern_groups is None:
            logger.debug(
                "%s: Messages in announcement still remaining",
                tracker_config.short_name,
            )
            return None

    if not _is_parsing_ok(tracker_config, pattern_groups, message):
        return None

    return pattern_groups


def _is_parsing_ok(tracker_config, pattern_groups, message):
    if len(pattern_groups) == 0:
        if _ignore_message(tracker_config.ignores, message):
            logger.debug("%s: Message ignored: %s", tracker_config.short_name, message)
        else:
            logger.warning(
                "%s: No match found for '%s'", tracker_config.short_name, message
            )
        return False

    return True


def _ignore_message(ignores, message):
    for ignore in ignores:
        # If message matches an expected regex it will be ignord
        # If it's not expected it works as an inverse, ignore everything which doesn't match.
        if bool(re.search(ignore.regex, message)) == ignore.expected:
            return True
    return False


def _parse_message(pattern_list, message):
    for i, pattern in enumerate(pattern_list, start=0):
        match = re.search(pattern.regex, message)
        if match:
            match_groups = {}
            for j, group_name in enumerate(pattern.groups, start=1):
                # Filter out missing non-capturing groups
                group = match.group(j)
                if group is not None and not group.isspace():
                    match_groups[group_name] = match.group(j).strip()
            return i, match_groups
    return -1, {}


######################
# Multi line patterns
######################

multiline_matches = {}
mutex = Lock()


class MultilineMatch:
    def __init__(self):
        self.time = time.time()
        self.pattern_groups = {}
        self.matched_index = -1

    # Returns true if more than 15 seconds has passed since instantiated
    def too_old(self):
        return (time.time() - self.time) > 15


# Returning None means the message matched but still waiting for remaning messages.
# Returning an empty dictionary means the message did not match anything.
def _parse_multiline_patterns(tracker_config, message):
    logger.debug(
        "%s: Parsing multiline annoucement '%s'", tracker_config.short_name, message
    )
    match_index, match_groups = _parse_message(
        tracker_config.multiline_patterns, message
    )

    if match_index == -1:
        return {}

    is_last_pattern = _is_last_multiline_pattern(
        tracker_config.multiline_patterns, match_index
    )

    with mutex:
        multiline_match = _get_multiline_match(
            tracker_config.type,
            tracker_config.multiline_patterns,
            match_index,
            is_last_pattern,
        )

        if multiline_match is None:
            return {}

        multiline_match.matched_index = match_index
        multiline_match.pattern_groups.update(match_groups)

    if is_last_pattern:
        return multiline_match.pattern_groups

    return None


def _is_valid_next_index(matched_index, next_index, patterns):
    return (next_index - matched_index) == 1 or (  # Next match
        next_index - matched_index > 1
        and all(  # Or optionals in between
            pattern.optional for pattern in patterns[matched_index + 1 : next_index]
        )
    )


# Returns True if match_index is the last pattern in the announcement
# OR if the remaining patterns are optional
def _is_last_multiline_pattern(multiline_patterns, match_index):
    return match_index + 1 == len(multiline_patterns) or all(
        pattern.optional for pattern in multiline_patterns[match_index + 1 :]
    )


def _get_multiline_match(tracker_type, patterns, match_index, last_pattern):
    global multiline_matches
    if tracker_type not in multiline_matches:
        multiline_matches[tracker_type] = []

    _clean_old_multi_announcements(multiline_matches[tracker_type])

    if match_index == 0:
        multiline_match = MultilineMatch()
        multiline_matches[tracker_type].append(multiline_match)
        return multiline_match

    for i, multiline_match in enumerate(multiline_matches[tracker_type]):
        if _is_valid_next_index(multiline_match.matched_index, match_index, patterns):
            if last_pattern:
                del multiline_matches[tracker_type][i]
            return multiline_match

    return None


def _clean_old_multi_announcements(matches):
    removes = list(filterfalse(lambda x: not x.too_old(), matches))
    for remove in removes:
        logger.warning(
            "Announcement is too old, discarding: %s",
            list(remove.pattern_groups.values()),
        )
        matches.remove(remove)
