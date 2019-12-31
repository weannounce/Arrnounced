#!/usr/bin/env python3
import argparse
import logging
import sys
import os
from logging.handlers import RotatingFileHandler

import config
import manager
import backend

############################################################
# Initialization
############################################################

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

def init_logging(config, log_level):
    logFormatter = logging.Formatter('%(asctime)s - %(levelname)s:%(name)-28s - %(message)s')
    rootLogger = logging.getLogger()
    rootLogger.setLevel(log_level)

    if config['log.to_console']:
        consoleHandler = logging.StreamHandler()
        consoleHandler.setFormatter(logFormatter)
        rootLogger.addHandler(consoleHandler)

    if config['log.to_file']:
        fileHandler = RotatingFileHandler('arrnounced.log', maxBytes=1024 * 1024 * 5, backupCount=5)
        fileHandler.setFormatter(logFormatter)
        rootLogger.addHandler(fileHandler)

############################################################
# MAIN ENTRY
############################################################
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Arrnounced - Listen for IRC announcements")
    parser.add_argument("-c", "--config", help="Configuration file", type=is_file, default="./settings.cfg")
    parser.add_argument("-t", "--trackers", help="XML tracker config path", type=is_dir, default="./autodl-trackers/trackers")
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

    init_logging(cfg, log_level)

    if cfg is None or not config.validate_config():
        print("Error: Configuration not valid", file=sys.stderr)
        sys.exit(1)

    backend.init(cfg)

    manager.run(args.trackers)
