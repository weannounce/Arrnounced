import datetime
import logging
import time
import re
import urllib.parse
from  tracker_config import VarType
import announcement_parser

import db
from backend import notify, Backend
import utils

logger = logging.getLogger("ANNOUNCE_MANAGER")

# TODO: Move parsing to an AnnoucnementParser and move all orqestration here.
# I.e. this module calls for parsing, backend notification and db writing
# Call this module AnnoucementManager?

# TODO: Add source and target to parameters
@db.db_session
def handle_announcement(tracker_config, announcement):
    parsed_announcement = announcement_parser.parse(tracker_config, announcement)

    if tracker_config.delay > 0:
        logger.debug("{}: Waiting %s seconds to check %s",
                tracker_config.short_name, tracker_config.delay, pattern_groups["torrentName"])
        time.sleep(tracker_config.delay)

# TODO: Create string with Backend enum values as int
    backends_string = "/".join(str(x.value) for x in parsed_announcement.backends)
    db.Announced(date=datetime.datetime.now(), title=parsed_announcement.torrent_name,
            indexer=tracker_config.short_name, torrent=parsed_announcement.torrent_url, pvr=backends_string)
    logger.debug("Notifying %s of release from %s: %s @ %s", backends_string,
                tracker_config.short_name, parsed_announcement.torrent_name,
                parsed_announcement.torrent_url)

    approved, backend = notify(parsed_announcement, tracker_config.short_name)

    if approved:
        logger.info("%s approved release: %s", backend.value, parsed_announcement.torrent_name)
        snatched = db.Snatched(date=datetime.datetime.now(), title=parsed_announcement.torrent_name,
                indexer=name, torrent=download_link, pvr=pvr_name)
    else:
        logger.debug("Release was rejected: %s", parsed_announcement.torrent_name)
