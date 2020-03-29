#!/usr/bin/python3
import datetime
from pony.orm import Database, db_session, Required, select, Set
import os
import sys

# This script converts a database file from the old database design to the new one.
# It takes two arguments. The old brain.db and new database to be created.
# E.g. ./convert_db.py ~/.arrnounced/brain.db new_brain.db
# Copy the old file for safe keeping and replace it with the new file.
# N.B. Since this script converts from old to new design in one single database
# session it consumes a fair bit of memory.


def def_new(db):
    class Announced(db.Entity):
        date = Required(datetime.datetime)
        title = Required(str)
        indexer = Required(str)
        torrent = Required(str)
        backend = Required(str)
        snatched = Set("Snatched")

    class Snatched(db.Entity):
        date = Required(datetime.datetime)
        announced = Required(Announced)
        backend = Required(str)


def def_old(db):
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


def open_database(filename, definition, create_db):
    db = Database()
    definition(db)
    db.bind("sqlite", os.path.realpath(filename), create_db=create_db)
    db.generate_mapping(create_tables=create_db)
    return db


if len(sys.argv) != 3:
    print("Usage: " + sys.argv[0] + " <old database> <new database>")
    sys.exit(1)

if os.path.isfile(sys.argv[2]):
    print("Error: New database cannot be existing file")
    sys.exit(1)

old_db = open_database(sys.argv[1], def_old, False)
new_db = open_database(sys.argv[2], def_new, True)

with db_session:
    old_anns = old_db.Announced.select().order_by(old_db.Announced.id)
    for old_ann in old_anns:
        new_ann = new_db.Announced(
            date=old_ann.date,
            title=old_ann.title,
            indexer=old_ann.indexer,
            torrent=old_ann.torrent,
            backend=old_ann.backend,
        )

        old_sns = list(select(s for s in old_db.Snatched if s.title == old_ann.title))
        # old_sns.show()
        if len(old_sns) == 0:
            # print(old_ann.title + " was not snatched")
            continue
        elif len(old_sns) > 1:
            print(
                "Warning: Found more than once snatch which matched an announcment. Choosing first one"
            )

        old_sn = old_sns[0]
        new_db.Snatched(date=old_sn.date, announced=new_ann, backend=old_sn.backend)

    # new_db.Announced.select().order_by(new_db.Announced.id).show()
    # new_db.Snatched.select().order_by(new_db.Snatched.id).show()
