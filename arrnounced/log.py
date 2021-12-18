import logging
import re

from logging.handlers import RotatingFileHandler

log_file = None


def init_logging(user_config, log_level, the_log_file):
    global log_file
    log_file = the_log_file
    logFormatter = logging.Formatter(
        "%(asctime)s - %(levelname)s:%(name)-28s - %(message)s"
    )
    rootLogger = logging.getLogger()
    rootLogger.setLevel(log_level)

    if user_config.log_to_console:
        consoleHandler = logging.StreamHandler()
        consoleHandler.setFormatter(logFormatter)
        rootLogger.addHandler(consoleHandler)

    if user_config.log_to_file:
        fileHandler = RotatingFileHandler(
            log_file, maxBytes=1024 * 1024 * 5, backupCount=5
        )
        fileHandler.setFormatter(logFormatter)
        rootLogger.addHandler(fileHandler)


# Returns tuple of (time, tag, message).
def get_logs():
    with open(log_file) as f:
        for line in f:
            log_parts = re.search(
                r"(^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})\s-\s(\S+)\s+-\s(.+)",
                line,
            )
            if log_parts:
                yield log_parts.group(1), log_parts.group(2), log_parts.group(3)
