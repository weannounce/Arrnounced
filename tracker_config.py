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
            xml_configs[tracker.trackerInfo["type"]] =  tracker
        else:
            logger.error("Could not parse tracker XML config: {}".format(trackerFile))
    return xml_configs

class TrackerXmlConfig:
    def parseConfig(self, root):
        self.trackerInfo = root.attrib
        # TODO: Workaround for profig handling periods as subsections
        self.trackerInfo["type"] = self.trackerInfo["type"].replace('.', '_')
        self.settings = []
        self.server = None
        self.torrent_url = []
        self.line_patterns = []
        self.multi_line_patterns = []
        self.ignores = []

        for setting in root.findall("./settings/*"):
            self.settings.append(re.sub('^(gazelle_|cookie_)', '', setting.tag))

        for server in root.findall("./servers/*"):
            self.server = server.attrib

        for extract in root.findall("./parseinfo/linepatterns/*"):
            self.line_patterns.append(self._parseExtract(extract))

        for extract in root.findall("./parseinfo/multilinepatterns/*"):
            self.multi_line_patterns.append(self._parseExtract(extract))

        for var in root.findall("./parseinfo/linematched/var[@name='torrentUrl']/*"):
            self.torrent_url.append(Var(var.tag, var.attrib))

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
            for key in self.server:
                print('\t\t', key, server[key])
            print("\tTorrentUrl")
            for var in self.torrent_url:
                print('\t\t', var.varType, ": ", var.var)
            print("\tLinePatterns")
            for pattern in self.line_patterns:
                print('\t\t', pattern.regex)
                for group in pattern.groups:
                    print('\t\t\þ', group)
            print("\tMultiLinePattern")
            for pattern in self.multi_line_patterns:
                print('\t\t', pattern.regex)
                for group in pattern.groups:
                    print('\t\t\t', group)
            print("\tIgnores")
            for ignore in self.ignores:
                print('\t\t', ignore)

        if self.trackerInfo is None:
            return False
        elif (0 == len(self.settings) or
              self.server is None or
              (0 == len(self.line_patterns) and 0 == len(self.multi_line_patterns))):
            return False

        return True

    def _parseExtract(self, extract):
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
        # TODO: Multipattern not supported from the get go
        else:
            # TODO: Check that all variables (var/varenc) from torrentUrl is specified in user_config
            # TODO: Move initialization here?
            trackers[user_config.name] = TrackerConfig(user_config, xml_configs[user_config.name])

    return trackers

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
        self.xml_config = xml_config
        self.user_config = user_config
        self.logger = logging.getLogger(self.user_config.name.upper())

    @property
    def irc_port(self):
        return self.user_config["irc_port"]

    @property
    def irc_nick(self):
        return self.user_config["nick"] if "nick" in self.user_config else None

    @property
    def irc_tls(self):
        return self.user_config["tls"]

    @property
    def irc_tls_verify(self):
        return self.user_config["tls_verify"]

    @property
    def nick_pass(self):
        return self.user_config["nick_pass"]

    #@property
    #def auth_key(self):
    #    return self.user_config["auth_key"]

    #@property
    #def torrent_pass(self):
    #    return self.user_config["torrent_pass"]

    @property
    def inviter(self):
        return self.user_config["inviter"]

    @property
    def invite_cmd(self):
        return self.user_config["invite_cmd"]

    @property
    def delay(self):
        return self.user_config["delay"]

    @property
    def irc_server(self):
        return self.xml_config.server["serverNames"]

    @property
    def irc_channel(self):
        return self.xml_config.server["channelNames"]

    @property
    def line_patterns(self):
        return self.xml_config.line_patterns

    @property
    def multi_line_patterns (self):
        return self.xml_config.multi_line_patterns

    @property
    def torrent_url (self):
        return self.xml_config.torrent_url
