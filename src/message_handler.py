import asyncio
import html
import logging
import re
import time

import announce_parser
import db
import utils
from backend import notify, notify_which_backends, backends_to_string, Backend
from tracker_config import VarType

logger = logging.getLogger("MESSAGE_HANDLER")


def _is_announcement(source, target, tracker_config):
    return (
        source in tracker_config.announcer_names
        and target in tracker_config.irc_channels
    )


def _sanitize_message(message):
    message = utils.strip_irc_color_codes(message)
    message = html.unescape(message)
    return message


@db.db_session
async def on_message(tracker_config, source, target, message):
    if not _is_announcement(source, target, tracker_config):
        logger.debug("Message is no announcement")
        return

    message = _sanitize_message(message)

    announcement = announce_parser.parse(tracker_config, message)
    if announcement is None:
        return

    backends = notify_which_backends(tracker_config, announcement.category)

    # If backends is empty backends_string is "None"
    backends_string = backends_to_string(backends)

    if tracker_config.announce_delay > 0:
        logger.debug(
            "%s: Waiting %s seconds to notify %s",
            tracker_config.short_name,
            tracker_config.announce_delay,
            announcement.torrent_name,
        )
        await asyncio.sleep(tracker_config.announce_delay)

    db_announced = db.insert_announcement(
        announcement, tracker_config.short_name, backends_string
    )
    logger.info(
        "Notifying %s of release from %s: %s",
        backends_string,
        tracker_config.short_name,
        announcement.torrent_name,
    )

    backend = notify(announcement, backends, tracker_config.short_name)

    if backend is None:
        # TODO Print rejection reason
        logger.debug("Release was rejected: %s", announcement.torrent_name)
    else:
        logger.info("%s approved release: %s", backend, announcement.torrent_name)
        db.insert_snatched(db_announced, backend)
