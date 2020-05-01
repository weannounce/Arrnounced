import logging
import sys
import threading

import irc
import tracker_config
import webui

logger = logging.getLogger("MANAGER")


def run(tracker_config_path):
    tracker_configs = tracker_config.get_trackers(tracker_config_path)
    if len(tracker_configs) == 0:
        logger.error("No trackers configured, exiting...")
        sys.exit(1)

    irc_thread = threading.Thread(target=irc.run, args=(tracker_configs,))
    webui_thread = threading.Thread(target=webui.run)

    irc_thread.start()
    webui_thread.start()

    irc_thread.join()
    webui_thread.join()

    logger.debug("Threads joined")
