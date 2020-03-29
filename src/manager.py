import logging
import sys
from time import sleep
from worker import Worker

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

    thread_irc = irc_task(tracker_configs)
    thread_webui = webui_task(tracker_configs)

    thread_irc.fire("START")
    thread_webui.fire("START")

    thread_irc.wait_thread(thread_irc)
    thread_webui.wait_thread(thread_webui)

    logger.debug("Finished waiting for irc & webui threads")


############################################################
# Tasks
############################################################


def irc_task(tracker_configs):
    worker = Worker()
    working = True

    @worker.listen("START")
    def _(event):
        logger.debug("Start IRC Task signaled")
        while working:
            try:
                irc.start(tracker_configs)
            except Exception:
                logger.exception("Exception irc_task START: ")

            sleep(30)

        logger.debug("IRC Task finished")

    return worker.start()


def webui_task(tracker_configs):
    worker = Worker()
    working = True

    @worker.listen("START")
    def _(event):
        logger.debug("Start WebUI Task signaled")
        while working:
            try:
                webui.run(tracker_configs)
            except Exception:
                logger.exception("Exception webui_task START: ")

            sleep(30)

        logger.debug("WebUI Task finished")

    return worker.start()
