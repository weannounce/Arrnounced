import asyncio
import html
import logging
from pony.orm.core import TransactionError

from arrnounced import announce_parser
from arrnounced import db
from arrnounced import utils
from arrnounced.announcement import create_announcement
from arrnounced.backend import notify, notify_which_backends

logger = logging.getLogger("MESSAGE_HANDLER")


def _is_announcement(source, target, tracker):
    return (
        source in tracker.config.announcer_names
        and target in tracker.config.irc_channels
    )


def _sanitize_message(message):
    message = utils.strip_irc_color_codes(message)
    message = html.unescape(message)
    return message


def _check_and_parse(tracker, source, target, message):
    if not _is_announcement(source, target, tracker):
        logger.debug("Message is no announcement")
        return

    message = _sanitize_message(message)

    variables = announce_parser.parse(tracker, message)
    if variables is None:
        return None

    return create_announcement(tracker, variables)


async def _handle_announcement(tracker, announcement):
    backends = notify_which_backends(tracker, announcement.category)

    backends_string = (
        "/".join([b.name for b in backends]) if len(backends) > 0 else "None"
    )

    if tracker.config.announce_delay > 0:
        logger.debug(
            "%s: Waiting %s seconds to notify %s",
            tracker.config.short_name,
            tracker.config.announce_delay,
            backends_string,
        )
        await asyncio.sleep(tracker.config.announce_delay)

    with db.db_session:
        db_announced = db.insert_announcement(announcement, backends_string)
    logger.info(
        "Notifying %s of release from %s: %s",
        backends_string,
        tracker.config.short_name,
        announcement.title,
    )

    backend = await notify(announcement, backends)

    if backend is None:
        # TODO Print rejection reason
        logger.debug("Release was rejected: %s", announcement.title)
    else:
        logger.info("%s approved release: %s", backend.name, announcement.title)
        with db.db_session:
            db_announced = db.get_announcement(db_announced.id)
            db.insert_snatched(db_announced, backend.name)


async def on_message(tracker, source, target, message):
    announcement = _check_and_parse(tracker, source, target, message)
    if announcement is None:
        return

    try:
        await _handle_announcement(tracker, announcement)
    except TransactionError:
        logger.exception("Database transaction failed for %s", announcement.title)
