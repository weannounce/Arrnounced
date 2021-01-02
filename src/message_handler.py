import asyncio
import html
import logging
from pony.orm.core import TransactionError

import announce_parser
import db
import utils
from announcement import create_announcement
from backend import notify, notify_which_backends

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


def _check_and_parse(tracker_config, source, target, message):
    if not _is_announcement(source, target, tracker_config):
        logger.debug("Message is no announcement")
        return

    message = _sanitize_message(message)

    variables = announce_parser.parse(tracker_config, message)
    if variables is None:
        return None

    return create_announcement(tracker_config, variables)


@db.db_session
async def _handle_announcement(tracker_config, announcement):
    backends = notify_which_backends(tracker_config, announcement.category)

    backends_string = (
        "/".join([b.name for b in backends]) if len(backends) > 0 else "None"
    )

    if tracker_config.announce_delay > 0:
        logger.debug(
            "%s: Waiting %s seconds to notify %s",
            tracker_config.short_name,
            tracker_config.announce_delay,
            backends_string,
        )
        await asyncio.sleep(tracker_config.announce_delay)

    db_announced = db.insert_announcement(announcement, backends_string)
    logger.info(
        "Notifying %s of release from %s: %s",
        backends_string,
        tracker_config.short_name,
        announcement.title,
    )

    backend = notify(announcement, backends)

    if backend is None:
        # TODO Print rejection reason
        logger.debug("Release was rejected: %s", announcement.title)
    else:
        logger.info("%s approved release: %s", backend.name, announcement.title)
        db.insert_snatched(db_announced, backend.name)


async def on_message(tracker_config, source, target, message):
    announcement = _check_and_parse(tracker_config, source, target, message)
    if announcement is None:
        return

    try:
        await _handle_announcement(tracker_config, announcement)
    except TransactionError as e:
        logger.error("Database transaction failed")
        logger.error("%s: %s", type(e).__name__, e)
