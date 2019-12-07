#!/usr/bin/env python3
import argparse
import logging
import sys
from logging.handlers import RotatingFileHandler

import config
import manager

############################################################
# Configuration
############################################################

cfg = config.init()

############################################################
# Initialization
############################################################

# Setup logging
def init_logging(log_level):
    logFormatter = logging.Formatter('%(asctime)s - %(levelname)s:%(name)-28s - %(message)s')
    rootLogger = logging.getLogger()
    rootLogger.setLevel(log_level)

    if cfg['bot.debug_console']:
        consoleHandler = logging.StreamHandler()
        consoleHandler.setFormatter(logFormatter)
        rootLogger.addHandler(consoleHandler)

    if cfg['bot.debug_file']:
        fileHandler = RotatingFileHandler('arrnounced.log', maxBytes=1024 * 1024 * 5, backupCount=5)
        fileHandler.setFormatter(logFormatter)
        rootLogger.addHandler(fileHandler)

############################################################
# MAIN ENTRY
############################################################
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Arrnounced - Listen for IRC announcements")
    parser.add_argument("-v", "--verbose", help="Verbose logging", action="store_true")
    args = parser.parse_args()

    log_level = logging.INFO
    if args.verbose:
        log_level = logging.DEBUG

    init_logging(log_level)

    if cfg is None or not config.validate_config():
        print("Error: Configuration not valid", file=sys.stderr)
        sys.exit(1)



    manager.run()
