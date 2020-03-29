#!/usr/bin/env python3
import argparse
import logging
import os
import sys
from pathlib import Path

import backend
import config
import db
import log
import manager


def is_file(path):
    if os.path.isfile(path):
        return path
    else:
        raise FileNotFoundError("Error: '" + path + "' is not a valid file")


def is_dir(path):
    if os.path.isdir(path):
        return path
    else:
        raise NotADirectoryError("Error: '" + path + "' is not a valid directory")


############################################################
# MAIN ENTRY
############################################################
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Arrnounced - Listen for IRC announcements"
    )
    parser.add_argument(
        "-d",
        "--data",
        type=is_dir,
        help="Data directory for storing logs and database. Default ~/.arrnounced",
        default=str(Path.home().joinpath(".arrnounced")),
    )
    parser.add_argument(
        "-c",
        "--config",
        type=is_file,
        help="Configuration file. Default ~/.arrnounced/settings.cfg",
        default=str(Path.home().joinpath(".arrnounced", "settings.cfg")),
    )
    parser.add_argument(
        "-t",
        "--trackers",
        type=is_dir,
        help="XML tracker config path. Default ~/.arrnounced/autodl-trackers/trackers",
        default=str(Path.home().joinpath(".arrnounced", "autodl-trackers", "trackers")),
    )
    parser.add_argument("-v", "--verbose", help="Verbose logging", action="store_true")

    try:
        args = parser.parse_args()
    except Exception as e:
        print(e)
        sys.exit(1)

    cfg = config.init(args.config)

    log_level = logging.INFO
    if args.verbose:
        log_level = logging.DEBUG

    log_file = Path(args.data).joinpath("arrnounced.log")
    log.init_logging(cfg, log_level, log_file)

    if cfg is None or not config.validate_config():
        print("Error: Configuration not valid", file=sys.stderr)
        sys.exit(1)

    backend.init(cfg)
    db.init(args.data)

    manager.run(args.trackers)
