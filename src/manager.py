import logging
import sys
import threading

import irc
import tracker_config
import webui

thread_irc = None
thread_webui = None
logger = logging.getLogger("MANAGER")


def run(tracker_config_path):
    global thread_irc, thread_webui

    tracker_configs = tracker_config.get_trackers(tracker_config_path)
    if len(tracker_configs) == 0:
        logger.error("No trackers configured, exiting...")
        sys.exit(1)

    thread_irc = threading.Thread(target=irc_task, args=(tracker_configs,))
    thread_webui = threading.Thread(target=webui_task)

    thread_irc.start()
    thread_webui.start()

    thread_irc.join()
    thread_webui.join()


def irc_task(tracker_configs):
    logger.debug("Start IRC thread")
    try:
        irc.start(tracker_configs)
    except Exception:
        logger.exception("Exception in irc_task START: ")

    logger.debug("IRC thread finished")


def webui_task():
    logger.debug("Start WebUI thread")
    try:
        webui.run()
    except Exception:
        logger.exception("Exception in WebUI thread")

    logger.debug("WebUI thread finished")
