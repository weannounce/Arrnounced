import logging
import datetime
from pony.orm import *

logger = logging.getLogger("DB")

db = Database()


class Announced(db.Entity):
    date = Required(datetime.datetime)
    title = Required(str)
    indexer = Required(str)
    torrent = Required(str)
    pvr = Required(str)


class Snatched(db.Entity):
    date = Required(datetime.datetime)
    title = Required(str)
    indexer = Required(str)
    torrent = Required(str)
    pvr = Required(str)


db.bind('sqlite', 'brain.db', create_db=True)
db.generate_mapping(create_tables=True)
