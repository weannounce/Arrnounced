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


class Snatched(db.Entity):
    date = Required(datetime.datetime)
    title = Required(str)
    indexer = Required(str)
    torrent = Required(str)
    backend = Required(str)


def init(destination_dir):
    db.bind('sqlite', os.path.join(os.path.realpath(destination_dir), "brain.db"), create_db=True)
    db.generate_mapping(create_tables=True)
