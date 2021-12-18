import logging
from math import ceil
from pony.orm.core import TransactionError

from arrnounced import db
from arrnounced import irc
from arrnounced import utils

from arrnounced.backend import renotify, get_configured_backends, get_backend, stop
from arrnounced.eventloop_utils import eventloop_util
from arrnounced.announcement import Announcement

logger = logging.getLogger("WEB-HANDLER")


def shutdown():
    for task in irc.get_stop_tasks():
        eventloop_util.run(task)
    eventloop_util.wait_till_complete()

    eventloop_util.run(stop())
    eventloop_util.wait_till_complete()

    eventloop_util.stop_eventloop()


# Request to check this torrent again
def _locked_notify(announcement_id, backend):
    with db.db_session:
        db_announcement = db.get_announcement(announcement_id)

    if db_announcement is None or len(db_announcement.title) == 0:
        logger.warning("Announcement to notify not found in database")
        return False

    logger.debug("Checking announcement again: %s", db_announcement.title)
    announcement = Announcement(
        db_announcement.title,
        db_announcement.torrent,
        indexer=db_announcement.indexer,
        date=db_announcement.date,
    )

    future = eventloop_util.run(renotify(announcement, backend))
    if future.result():
        logger.debug("%s accepted the torrent this time!", backend.name)
        with db.db_session:
            db_announcement = db.get_announcement(db_announcement.id)
            db.insert_snatched(db_announcement, backend.name)
        return True

    logger.debug("%s still refused this torrent...", backend.name)
    return False


def notify_backend(announcement_id, backend_name):
    backend = get_backend(backend_name)
    if backend:
        try:
            return _locked_notify(announcement_id, backend)
        except TransactionError:
            logger.exception("Database transaction failed")
    else:
        logger.warning(
            "Could not find the requested backend '%s'",
            backend_name,
        )

    return False


def get_page_counts(page_size):
    try:
        with db.db_session:
            return (
                ceil(db.get_announced_count() / page_size),
                ceil(db.get_snatched_count() / page_size),
            )
    except TransactionError as e:
        logger.error("%s: %s", type(e).__name__, e)

    return 0, 0


def get_announced_page(page_nr, page_size):
    try:
        with db.db_session:
            return (
                [
                    e.serialize(utils.human_datetime)
                    for e in db.get_announced(limit=page_size, page=page_nr)
                ],
                get_configured_backends(),
            )
    except TransactionError as e:
        logger.error("%s: %s", type(e).__name__, e)

    return [], []


def get_snatched_page(page_nr, page_size):
    try:
        with db.db_session:
            return [
                db.snatched_to_dict(e, utils.human_datetime)
                for e in db.get_snatched(limit=page_size, page=page_nr)
            ]
    except TransactionError as e:
        logger.error("%s: %s", type(e).__name__, e)

    return []
