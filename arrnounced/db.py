from datetime import datetime, timedelta
import logging
import os
import threading

from pony.orm import Database, desc, pony, Required, Set
from pony.orm import db_session  # noqa: F401

logger = logging.getLogger("DB")
db = Database()


class Announced(db.Entity):
    date = Required(datetime)
    title = Required(str)
    indexer = Required(str)
    torrent = Required(str)
    backend = Required(str)
    snatched = Set("Snatched")

    def serialize(self, transform_date):
        return {
            "id": self.id,
            "date": transform_date(self.date),
            "title": self.title,
            "indexer": self.indexer,
            "torrent": self.torrent,
            "backend": self.backend,
        }


class Snatched(db.Entity):
    date = Required(datetime)
    announced = Required(Announced)
    backend = Required(str)


def init(destination_dir):
    try:
        db.bind(
            "sqlite",
            os.path.join(os.path.realpath(destination_dir), "brain.db"),
            create_db=True,
        )
        db.generate_mapping(create_tables=True)
    except pony.orm.dbapiprovider.OperationalError as e:
        logger.error(
            "Could not initiate database: %s",
            e,
        )
        return False

    return True


def snatched_to_dict(snatched, transform_date):
    return {
        "date": transform_date(snatched[1]),
        "indexer": snatched[2],
        "title": snatched[3],
        "backend": snatched[4],
    }


def get_snatched(limit, page):
    # Order by first attribute in tuple i.e. s.id
    ss = (
        pony.orm.select(
            (s.id, s.date, a.indexer, a.title, s.backend)
            for s in Snatched
            for a in s.announced
        )
        .order_by(desc(1))
        .limit(limit, offset=(page - 1) * limit)
    )
    return ss


def get_announced(limit, page):
    return (
        Announced.select()
        .order_by(desc(Announced.id))
        .limit(limit, offset=(page - 1) * limit)
    )


def get_announcement(id):
    return Announced.get(id=id)


def insert_announcement(announcement, backends):
    return Announced(
        date=announcement.date,
        title=announcement.title,
        torrent=announcement.torrent_url,
        indexer=announcement.indexer,
        backend=backends,
    )


def insert_snatched(announcement, backend):
    Snatched(date=datetime.now(), announced=announcement, backend=backend)


def get_announced_count():
    return pony.orm.count(a for a in Announced)


def get_snatched_count():
    return pony.orm.count(s for s in Snatched)


_stop_thread = threading.Event()


def stop():
    logger.debug("Stopping database purge thread")
    _stop_thread.set()


def run(user_config):
    one_day = 24 * 60 * 60
    running = user_config.db_purge_days > 0
    while running:
        with db_session:
            old = pony.orm.select(
                a
                for a in Announced
                if a.date < datetime.now() - timedelta(days=user_config.db_purge_days)
            )
            deleted = old.delete(bulk=False)
            if deleted > 0:
                logger.debug("Purged %s old entries from the database", deleted)

        running = not _stop_thread.wait(timeout=one_day)
