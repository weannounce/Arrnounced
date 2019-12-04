import os
import xml.etree.ElementTree as ET
import re
import logging
from enum import Enum

import config
import db

cfg = config.init()
logger = logging.getLogger("TRACKERS")
track_config_path = "autodl-trackers/trackers"
debug = False

def parse_xml_configs():
    xml_configs = {}
    for trackerFile in sorted(os.listdir(track_config_path)):
        tree = ET.parse(track_config_path + "/" + trackerFile)
        tracker = TrackerXmlConfig()

        if tracker.parseConfig(tree.getroot()):
            xml_configs[tracker.trackerInfo["type"]] =  tracker
        else:
            logger.error("Could not parse tracker config: {}".format(trackerFile))
    return xml_configs

class TrackerXmlConfig:
    def parseConfig(self, root):
        self.trackerInfo = root.attrib
        self.settings = []
        self.servers = []
        self.torrentUrl = []
        self.linePatterns = []
        self.multiLinePattern = []
        self.ignores = []

        for setting in root.findall("./settings/*"):
            self.settings.append(re.sub('^(gazelle_|cookie_)', '', setting.tag))

        for server in root.findall("./servers/*"):
            self.servers.append(server.attrib)

        for extract in root.findall("./parseinfo/linepatterns/*"):
            self.linePatterns.append(self.__parseExtract(extract))

        for extract in root.findall("./parseinfo/multilinepatterns/*"):
            self.multiLinePattern.append(self.__parseExtract(extract))

        for var in root.findall("./parseinfo/linematched/var[@name='torrentUrl']/*"):
            self.torrentUrl.append(Var(var.tag, var.attrib))

        # What's up with expected?? False seems to mean to ignore the ignore??
        for ignore in root.findall("./parseinfo/ignore/*"):
            self.ignores.append(ignore.attrib['value'])


        if debug:
            for info in self.trackerInfo:
                print(info, root.attrib[info])
            print("\tSettings")
            for setting in self.settings:
                print('\t\t', setting)
            print("\tServer")
            for server in self.servers:
                for key in server:
                    print('\t\t', key, server[key])
            print("\tTorrentUrl")
            for var in self.torrentUrl:
                print('\t\t', var.varType, ": ", var.var)
            print("\tLinePatterns")
            for pattern in self.linePatterns:
                print('\t\t', pattern.regex)
                for group in pattern.groups:
                    print('\t\t\þ', group)
            print("\tMultiLinePattern")
            for pattern in self.multiLinePattern:
                print('\t\t', pattern.regex)
                for group in pattern.groups:
                    print('\t\t\t', group)
            print("\tIgnores")
            for ignore in self.ignores:
                print('\t\t', ignore)

        if self.trackerInfo is None:
            return False
        elif (0 == len(self.settings) or
                0 == len(self.servers) or
                (0 == len(self.linePatterns) and 0 == len(self.multiLinePattern))):
            return False

        return True

    def __parseExtract(self, extract):
        regex = extract.findall("./regex")
        groups = extract.findall("./vars/*")
        groupList = []
        for group in groups:
            groupList.append(group.attrib['name'])
        return Extract(regex[0].attrib['value'], groupList)

# Value is XML attribute name
class VarType(Enum):
    STRING = "value"
    VAR = "name"
    VARENC = "name"

class Var:
    def __init__(self, varType, var):
        self.varType = VarType[varType.upper()]
        self.var = var[self.varType.value]

class Extract:
    def __init__(self, regex, groups):
        self.regex = regex
        self.groups = groups

def get_trackers():
    xml_configs = parse_xml_configs()
    trackers = {}
    for user_config in cfg.sections():
        if user_config.name in config.base_sections:
            continue
        elif user_config.name not in xml_configs:
            logger.error("Tracker '{}' from configuration is not supported".format(user_config.name))
        else:
            trackers[user_config.name] = TrackerConfig(user_config, xml_configs[user_config.name])

    return trackers

class TrackerConfig:
    def __init__(self, user_config, xml_config):
        self.xml_config = xml_config
        self.user_config = user_config
        self.logger = logging.getLogger(self.user_config.name.upper())


    @db.db_session
    def parse(self, announcement):
        global name

        # extract required information from announcement
        torrent_title = utils.str_before(announcement, ' - ')
        torrent_id = utils.get_id(announcement, 1)

        # pass announcement to sonarr
        if torrent_id is not None and torrent_title is not None:
            download_link = get_torrent_link(torrent_id, utils.replace_spaces(torrent_title, '.'))

            announced = db.Announced(date=datetime.datetime.now(), title=utils.replace_spaces(torrent_title, '.'),
                                     indexer=name, torrent=download_link, pvr="Sonarr")

            if delay > 0:
                logger.debug("Waiting %s seconds to check %s", delay, torrent_title)
                time.sleep(delay)

            approved = sonarr_wanted(torrent_title, download_link, name)
            if approved:
                logger.info("Sonarr approved release: %s", torrent_title)
                snatched = db.Snatched(date=datetime.datetime.now(), title=utils.replace_spaces(torrent_title, '.'),
                                       indexer=name, torrent=download_link, pvr="Sonarr")
            else:
                logger.debug("Sonarr rejected release: %s", torrent_title)


    # Generate torrent link
    def get_torrent_link(self, torrent_id, torrent_name):
        torrent_link = "https://www.morethan.tv/torrents.php?action=download&id={}&authkey={}&torrent_pass={}" \
            .format(torrent_id, auth_key, torrent_pass)
        return torrent_link
