import logging
import os
import re
import xml.etree.ElementTree as ET
from enum import Enum
from collections import namedtuple

import config
from backend import Backend

logger = logging.getLogger("TRACKER_CONF")
debug = False

Server = namedtuple('Server', 'names channels announcers')

def parse_xml_configs(tracker_config_path):
    xml_configs = {}
    for trackerFile in sorted(os.listdir(tracker_config_path)):
        tree = ET.parse(tracker_config_path + "/" + trackerFile)
        tracker = TrackerXmlConfig()

        if tracker.parse_config(tree.getroot()):
            xml_configs[tracker.tracker_info["type"]] =  tracker
        else:
            logger.error("Could not parse tracker XML config: %s", trackerFile)

    return xml_configs

class TrackerXmlConfig:
    def parse_config(self, root):
        self.tracker_info = root.attrib
        # TODO: Workaround for profig handling periods as subsections
        self.tracker_info["type"] = self.tracker_info["type"].replace('.', '_')
        self.settings = []
        self.servers = []
        self.torrent_url = []
        self.line_patterns = []
        self.multiline_patterns = []
        self.ignores = []

        for setting in root.findall("./settings/*"):
            if "description" not in setting.tag:
                self.settings.append(re.sub('^(gazelle_|cookie_)', '', setting.tag))

        for server in root.findall("./servers/*"):
            self.servers.append(Server(
                server.attrib["serverNames"].lower().split(','),
                server.attrib["channelNames"].lower().split(','),
                server.attrib["announcerNames"].split(',')))

        for extract in root.findall("./parseinfo/linepatterns/*"):
            self.line_patterns.append(self._parseExtract(extract))

        for extract in root.findall("./parseinfo/multilinepatterns/*"):
            self.multiline_patterns.append(self._parseExtract(extract))

        for var in root.findall("./parseinfo/linematched/var[@name='torrentUrl']/*"):
            self.torrent_url.append(Var(var.tag, var.attrib))

        for ignore in root.findall("./parseinfo/ignore/*"):
            self.ignores.append(
                    (ignore.attrib['value'],
                     ("expected" not in ignore.attrib or
                         ignore.attrib['expected'] == "true")))


        if debug:
            for info in self.tracker_info:
                print(info, root.attrib[info])
            print("\tSettings")
            for setting in self.settings:
                print('\t\t', setting)
            print("\tServer")
            for server in self.servers:
                print('\t\tnames:', server.names)
                print('\t\tchannels', server.channels)
                print('\t\tannouncers', server.announcers)
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
        # TODO: maybe not require servers
        elif (0 == len(self.settings) or
              len(self.servers) == 0  or
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

def get_trackers(tracker_config_path):
    xml_configs = parse_xml_configs(tracker_config_path)
    trackers = {}
    for user_config in config.sections():
        if user_config.name in config.base_sections:
            continue
        elif user_config.name not in xml_configs:
            logger.error("Tracker '%s' from configuration is not supported", user_config.name)
        elif len(xml_configs[user_config.name].multiline_patterns) > 0:
            logger.error("%s: Multiline announcements are not supported yet!", user_config.name)
        elif _are_settings_configured(user_config, xml_configs[user_config.name].settings):
            trackers[user_config.name] = TrackerConfig(user_config, xml_configs[user_config.name])

    return trackers

"""
Check that all setting from the XML tracker config is configured in the user config.
"""
def _are_settings_configured(user_config, required_settings):
    configured = True
    for setting in required_settings:
        if setting not in user_config:
            logger.error("%s: Must specify '%s' in config", user_config.name, setting)
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

        self.backends = {}
        if self._user_config["notify_sonarr"]:
            self.backends[Backend.SONARR] = None
        if self._user_config["notify_radarr"]:
            self.backends[Backend.RADARR] = None
        if self._user_config["notify_lidarr"]:
            self.backends[Backend.LIDARR] = None

        if self._user_config["category_sonarr"] is not None:
            self.backends[Backend.SONARR] = self._user_config["category_sonarr"]
        if self._user_config["category_radarr"] is not None:
            self.backends[Backend.RADARR] = self._user_config["category_radarr"]
        if self._user_config["category_lidarr"] is not None:
            self.backends[Backend.LIDARR] = self._user_config["category_lidarr"]

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
    def notify_backends(self):
        return self.backends

    @property
    def short_name(self):
        return self._xml_config.tracker_info["shortName"]

    @property
    def irc_server(self):
        return self._xml_config.servers[0].names[0]

    @property
    def irc_channel(self):
        return self._xml_config.servers[0].channels[0]

    @property
    def announcer_name(self):
        return self._xml_config.servers[0].announcers[0]

    @property
    def line_patterns(self):
        return self._xml_config.line_patterns

    @property
    def multiline_patterns (self):
        return self._xml_config.multiline_patterns

    @property
    def ignores (self):
        return self._xml_config.ignores

    @property
    def torrent_url (self):
        return self._xml_config.torrent_url
