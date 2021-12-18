import logging
import time

from asyncio import all_tasks, run_coroutine_threadsafe

logger = logging.getLogger("LOOP_UTILS")


class EventLoopUtil:
    def __init__(self):
        self._the_eventloop = None

    def set_eventloop(self, the_eventloop):
        self._the_eventloop = the_eventloop

    def run(self, the_task):
        return run_coroutine_threadsafe(the_task, self._the_eventloop)

    def wait_till_complete(self):
        logger.info("Waiting for eventloop tasks...")
        # The backend stop task has likely not had time to start yet
        # Therefore sleep a while until it does
        time.sleep(1)
        while len(all_tasks(self._the_eventloop)) != 0:
            time.sleep(1)
        logger.info("Tasks done")

    def stop_eventloop(self):
        self._the_eventloop.call_soon_threadsafe(self._the_eventloop.stop)

        logger.info("Stopping eventloop...")
        while self._the_eventloop.is_running():
            time.sleep(1)
        self._the_eventloop.close()
        logger.info("Eventloop stopped")


eventloop_util = EventLoopUtil()
