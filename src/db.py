import datetime
import logging
from pony.orm import *
import os

logger = logging.getLogger("DB")

db = Database()

class Announced(db.Entity):
    date = Required(datetime.datetime)
    title = Required(str)
    indexer = Required(str)
    torrent = Required(str)
    backend = Required(str)
    snatched = Set('Snatched')


class Snatched(db.Entity):
    date = Required(datetime.datetime)
    announced = Required(Announced)
    backend = Required(str)

def init(destination_dir):
    db.bind('sqlite', os.path.join(os.path.realpath(destination_dir), "brain.db"), create_db=True)
    db.generate_mapping(create_tables=True)

def get_snatched(limit, page):
    # Order by first attribute in tuple i.e. s.id
    ss = pony.orm.select(
            (s.id, s.date, a.indexer, a.title, s.backend)
            for s in Snatched for a in s.announced
            ).order_by(desc(1)).limit(limit, offset=page*limit)
    return ss

def get_announced(limit, page):
    return Announced.select().order_by(desc(Announced.id)).limit(limit, offset=page*limit)

def get_announcement(id):
    return Announced.get(id=id)

def insert_announcement(announcement, indexer, backends):
    return Announced(date=datetime.datetime.now(),
            title=announcement.torrent_name,
            torrent=announcement.torrent_url,
            indexer=indexer,
            backend=backends)

def insert_snatched(announcement, backend):
    Snatched(date=datetime.datetime.now(),
            announced=announcement,
            backend=backend)
