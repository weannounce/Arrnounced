import logging

from pluginbase import PluginBase

import utils

logger = logging.getLogger("TRACKERS")


class Trackers(object):
    plugin_base = None
    source = None
    loaded = {}

    def __init__(self):
        self.plugin_base = PluginBase(package='trackers')
        self.source = self.plugin_base.make_plugin_source(
            searchpath=['./trackers'],
            identifier='trackers')

        # Load all trackers
        logger.info("Loading trackers...")

        for tmp in self.source.list_plugins():
            tracker = self.source.load_plugin(tmp)
            loaded = tracker.init()
            if loaded:
                logger.info("Initialized tracker: %s", tracker.name)
                self.loaded[tracker.name.lower()] = tracker
            else:
                logger.info("Problem initializing tracker: %s", tracker.name)

    def get_tracker(self, name):
        if len(self.loaded) == 0:
            logger.debug("No trackers loaded...")

        return self.loaded.get(name.lower())
