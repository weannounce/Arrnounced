#!/usr/bin/env python3
import argparse
import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

import backend
import db
import config
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

def init_logging(config, log_level, destination_dir):
    logFormatter = logging.Formatter('%(asctime)s - %(levelname)s:%(name)-28s - %(message)s')
    rootLogger = logging.getLogger()
    rootLogger.setLevel(log_level)

    if config['log.to_console']:
        consoleHandler = logging.StreamHandler()
        consoleHandler.setFormatter(logFormatter)
        rootLogger.addHandler(consoleHandler)

    if config['log.to_file']:
        fileHandler = RotatingFileHandler(destination_dir + '/arrnounced.log', maxBytes=1024 * 1024 * 5, backupCount=5)
        fileHandler.setFormatter(logFormatter)
        rootLogger.addHandler(fileHandler)

############################################################
# MAIN ENTRY
############################################################
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Arrnounced - Listen for IRC announcements")
    parser.add_argument("-d", "--data", type=is_dir,
            help="Data directory for storing logs and database. Default ~/.arrnounced",
            default=str(Path.home().joinpath(".arrnounced")))
    parser.add_argument("-c", "--config", type=is_file,
            help="Configuration file. Default ~/.arrnounced/settings.cfg",
            default=str(Path.home().joinpath(".arrnounced", "settings.cfg")))
    parser.add_argument("-t", "--trackers", type=is_dir,
            help="XML tracker config path. Default ~/.arrnounced/autodl-trackers/trackers",
            default=str(Path.home().joinpath(".arrnounced", "autodl-trackers", "trackers")))
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

    init_logging(cfg, log_level, args.data)

    if cfg is None or not config.validate_config():
        print("Error: Configuration not valid", file=sys.stderr)
        sys.exit(1)

    backend.init(cfg)
    db.init(args.data)

    manager.run(args.trackers)
