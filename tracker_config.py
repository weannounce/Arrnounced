import os
import xml.etree.ElementTree as ET
import re
import logging
from enum import Enum

import config
import db

cfg = config.init()
logger = logging.getLogger("TRACKER_CONF")
track_config_path = "autodl-trackers/trackers"
debug = False

def parse_xml_configs():
    xml_configs = {}
    for trackerFile in sorted(os.listdir(track_config_path)):
        tree = ET.parse(track_config_path + "/" + trackerFile)
        tracker = TrackerXmlConfig()

        if tracker.parseConfig(tree.getroot()):
            xml_configs[tracker.tracker_info["type"]] =  tracker
        else:
            logger.error("Could not parse tracker XML config: {}".format(trackerFile))
    return xml_configs

class TrackerXmlConfig:
    def parseConfig(self, root):
        self.tracker_info = root.attrib
        # TODO: Workaround for profig handling periods as subsections
        self.tracker_info["type"] = self.tracker_info["type"].replace('.', '_')
        self.settings = []
        self.server = None
        self.torrent_url = []
        self.line_patterns = []
        self.multiline_patterns = []
        self.ignores = []

        for setting in root.findall("./settings/*"):
            if "description" not in setting.tag:
                self.settings.append(re.sub('^(gazelle_|cookie_)', '', setting.tag))

        for server in root.findall("./servers/*"):
            self.server = server.attrib

        for extract in root.findall("./parseinfo/linepatterns/*"):
            self.line_patterns.append(self._parseExtract(extract))

        for extract in root.findall("./parseinfo/multilinepatterns/*"):
            self.multiline_patterns.append(self._parseExtract(extract))

        for var in root.findall("./parseinfo/linematched/var[@name='torrentUrl']/*"):
            self.torrent_url.append(Var(var.tag, var.attrib))

        # What's up with expected?? False seems to mean to ignore the ignore??
        for ignore in root.findall("./parseinfo/ignore/*"):
            self.ignores.append(ignore.attrib['value'])


        if debug:
            for info in self.tracker_info:
                print(info, root.attrib[info])
            print("\tSettings")
            for setting in self.settings:
                print('\t\t', setting)
            print("\tServer")
            for key in self.server:
                print('\t\t', key, self.server[key])
            print("\tTorrentUrl")
            for var in self.torrent_url:
                print('\t\t', var.varType, ": ", var.name)
            print("\tLinePatterns")
            for pattern in self.line_patterns:
                print('\t\t', pattern.regex)
                for group in pattern.groups:
                    print('\t\t\þ', group)
            print("\tMultiLinePattern")
            for pattern in self.multiline_patterns:
                print('\t\t', pattern.regex)
                for group in pattern.groups:
                    print('\t\t\t', group)
            print("\tIgnores")
            for ignore in self.ignores:
                print('\t\t', ignore)

        if self.tracker_info is None:
            return False
        elif (0 == len(self.settings) or
              self.server is None or
              (0 == len(self.line_patterns) and 0 == len(self.multiline_patterns))):
            return False

        return True

    def _parseExtract(self, extract):
        regex = extract.findall("./regex")
        groups = extract.findall("./vars/*")
        groupList = []
        for group in groups:
            groupList.append(group.attrib['name'])
        return Extract(regex[0].attrib['value'], groupList)

class VarType(Enum):
    STRING = 1
    VAR = 2
    VARENC = 3

vartype_to_name = { VarType.STRING: "value", VarType.VAR: "name", VarType.VARENC: "name" }

class Var:
    def __init__(self, varType, var):
        self.varType = VarType[varType.upper()]
        self.name = var[vartype_to_name[self.varType]]

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
        elif len(xml_configs[user_config.name].multiline_patterns) > 0:
            logger.error("{}: Multiline announcements are not supported yet!".format(user_config.name))
        elif _are_settings_configured(user_config, xml_configs[user_config.name].settings):
            trackers[user_config.name] = TrackerConfig(user_config, xml_configs[user_config.name])

    return trackers

def _are_settings_configured(user_config, required_settings):
    configured = True
    for setting in required_settings:
        if setting not in user_config:
            logger.error("{}: Must specify '{}' in config".format(user_config.name, setting))
            configured = False
    return configured

def parse_bool(string):
    true_strings = [ "true", "True", "yes", "Yes", "1" ]
    false_strings = [ "false", "False", "no", "No", "0" ]
    if string in true_strings:
        return True
    elif string in false_strings:
        return False
    else:
        return None


class TrackerConfig:
    def __init__(self, user_config, xml_config):
        self._xml_config = xml_config
        self._user_config = user_config

    def __getitem__(self, key):
        return self._user_config[key]

    @property
    def irc_port(self):
        return self._user_config["irc_port"]

    @property
    def irc_nick(self):
        return self._user_config["nick"] if "nick" in self._user_config else None

    @property
    def irc_tls(self):
        return self._user_config["tls"]

    @property
    def irc_tls_verify(self):
        return self._user_config["tls_verify"]

    @property
    def nick_pass(self):
        return self._user_config["nick_pass"]

    @property
    def inviter(self):
        return self._user_config["inviter"]

    @property
    def invite_cmd(self):
        return self._user_config["invite_cmd"]

    @property
    def delay(self):
        return self._user_config["delay"]

    @property
    def notify_sonarr(self):
        return self._user_config["notify_sonarr"]

    @property
    def notify_radarr(self):
        return self._user_config["notify_radarr"]

    @property
    def notify_lidarr(self):
        return self._user_config["notify_lidarr"]

    @property
    def short_name(self):
        return self._xml_config.tracker_info["shortName"]

    @property
    def irc_server(self):
        return self._xml_config.server["serverNames"]

    @property
    def irc_channel(self):
        return self._xml_config.server["channelNames"]

    @property
    def announcer_name(self):
        return self._xml_config.server["announcerNames"]

    @property
    def line_patterns(self):
        return self._xml_config.line_patterns

    @property
    def multiline_patterns (self):
        return self._xml_config.multiline_patterns

    @property
    def torrent_url (self):
        return self._xml_config.torrent_url
