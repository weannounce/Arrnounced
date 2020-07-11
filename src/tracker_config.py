import logging
import os
import re
import defusedxml.ElementTree as ET
from collections import namedtuple

import config
from backend import Backend
from announcement import (
    Var,
    Http,
    Extract,
    ExtractOne,
    ExtractTags,
    VarReplace,
    SetRegex,
    If,
)


# TODO: compile and store regex
logger = logging.getLogger("TRACKER_CONF")
debug = False

Server = namedtuple("Server", "names channels announcers")
Ignore = namedtuple("Ignore", "regex expected")


def parse_xml_configs(tracker_config_path):
    xml_configs = {}
    for tracker_file in sorted(os.listdir(tracker_config_path)):
        tree = ET.parse(tracker_config_path + "/" + tracker_file)
        tracker = TrackerXmlConfig()

        try:
            if tracker.parse_config(tree.getroot()):
                xml_configs[tracker.tracker_info["type"]] = tracker
            else:
                logger.error("Could not parse tracker XML config '%s'", tracker_file)
        except KeyError as e:
            logger.error(
                "Could not parse tracker XML config '%s', missing attribute %s",
                tracker_file,
                e,
            )

    return xml_configs


def _is_optional(element):
    return (
        False
        if "optional" not in element.attrib
        else element.attrib["optional"] == "true"
    )


def var_creator(element):
    return Var(element.attrib["name"], element.findall("./*"))


def http_creator(element):
    return Http()


def extract_creator(element):
    groups = element.findall("./vars/*")
    groupList = []
    for group in groups:
        groupList.append(group.attrib["name"])

    return Extract(
        element.attrib["srcvar"] if "srcvar" in element.attrib else None,
        element.find("./regex").attrib["value"],
        groupList,
        _is_optional(element),
    )


def extract_one_creator(element):
    extracts = []
    xml_extracts = element.findall("./extract")
    for xml_extract in xml_extracts:
        extracts.append(extract_creator(xml_extract))
    return ExtractOne(extracts)


def extract_tags_creator(element):
    srcvar = element.attrib["srcvar"]
    split = element.attrib["split"]

    setvarifs = []
    for setvarif in element.findall("./setvarif"):
        setvarifs.append(
            ExtractTags.SetVarIf(
                setvarif.attrib["varName"],
                setvarif.attrib.get("regex"),
                setvarif.attrib.get("value"),
                setvarif.attrib.get("newValue"),
            )
        )

    return ExtractTags(srcvar, split, setvarifs)


def var_replace_creator(element):
    return VarReplace(
        element.attrib["name"],
        element.attrib["srcvar"],
        element.attrib["regex"],
        element.attrib["replace"],
    )


def set_regex_creator(element):
    return SetRegex(
        element.attrib["srcvar"],
        element.attrib["regex"],
        element.attrib["varName"],
        element.attrib["newValue"],
    )


def if_creator(element):
    line_matches = []
    for matched in element.findall("./*"):
        line_matches.append(_line_match_creators[matched.tag](matched))
    return If(element.attrib["srcvar"], element.attrib["regex"], line_matches)


_line_match_creators = {
    "var": var_creator,
    "http": http_creator,
    "extract": extract_creator,
    "extractone": extract_one_creator,
    "extracttags": extract_tags_creator,
    "varreplace": var_replace_creator,
    "setregex": set_regex_creator,
    "if": if_creator,
}


class TrackerXmlConfig:
    def __init__(self):
        self.settings = []
        self.servers = []
        self.line_matched = []
        self.line_patterns = []
        self.multiline_patterns = []
        self.ignores = []

    def parse_config(self, root):  # noqa: C901
        self.tracker_info = root.attrib
        # TODO: Workaround for profig handling periods as subsections
        self.tracker_info["type"] = self.tracker_info["type"].replace(".", "_")

        for setting in root.findall("./settings/*"):
            if "description" not in setting.tag:
                self.settings.append(re.sub("^(gazelle_|cookie_)", "", setting.tag))

        for server in root.findall("./servers/*"):
            self.servers.append(
                Server(
                    server.attrib["serverNames"].lower().split(","),
                    server.attrib["channelNames"].lower().split(","),
                    server.attrib["announcerNames"].split(","),
                )
            )

        for extract in root.findall("./parseinfo/linepatterns/*"):
            self.line_patterns.append(extract_creator(extract))

        for extract in root.findall("./parseinfo/multilinepatterns/*"):
            self.multiline_patterns.append(extract_creator(extract))

        for element in root.findall("./parseinfo/linematched/*"):
            self.line_matched.append(_line_match_creators[element.tag](element))

        for ignore in root.findall("./parseinfo/ignore/*"):
            self.ignores.append(
                Ignore(
                    ignore.attrib["value"],
                    (
                        "expected" not in ignore.attrib
                        or ignore.attrib["expected"] == "true"
                    ),
                )
            )

        if debug:
            for info in self.tracker_info:
                print(info, root.attrib[info])
            print("\tSettings")
            for setting in self.settings:
                print("\t\t", setting)
            print("\tServer")
            for server in self.servers:
                print("\t\tnames:", server.names)
                print("\t\tchannels", server.channels)
                print("\t\tannouncers", server.announcers)
            print("\tTorrentUrl")
            for var in self.line_matched:
                print("\t\t", var.varType, ": ", var.name)
            print("\tLinePatterns")
            for pattern in self.line_patterns:
                print("\t\t", pattern.regex, pattern.optional)
                for group in pattern.groups:
                    print("\t\t\t", group)
            print("\tMultiLinePattern")
            for pattern in self.multiline_patterns:
                print("\t\t", pattern.regex, pattern.optional)
                for group in pattern.groups:
                    print("\t\t\t", group)
            print("\tIgnores")
            for ignore in self.ignores:
                print("\t\t", ignore.regex, "-", ignore.expected)

        if self.tracker_info is None:
            logger.error("No 'tracker_info' found")
            return False
        elif 0 == len(self.line_patterns) and 0 == len(self.multiline_patterns):
            logger.error("No announcement patterns found")
        elif len(self.servers) == 0:
            logger.error("No servers found")
            return False
        elif len(self.line_matched) == 0:
            logger.error("No items to build URL")
            return False

        return True


def get_trackers(tracker_config_path):
    xml_configs = parse_xml_configs(tracker_config_path)
    trackers = {}
    for user_config in config.sections():
        if user_config.name in config.base_sections:
            continue
        elif user_config.name not in xml_configs:
            logger.error(
                "Tracker '%s' from configuration is not supported", user_config.name
            )
        elif _are_settings_configured(
            user_config, xml_configs[user_config.name].settings
        ):
            trackers[user_config.name] = TrackerConfig(
                user_config, xml_configs[user_config.name]
            )

    return trackers


# Check that all setting from the XML tracker config is configured in the user config.
def _are_settings_configured(user_config, required_settings):
    configured = True
    for setting in required_settings:
        if setting == "cookie":
            logger.warning(
                "%s: Tracker seems to require cookies to download torrent file. "
                + "Sonarr/Radarr/Lidarr API does not support cookies",
                user_config.name,
            )
        elif setting not in user_config:
            logger.error("%s: Must specify '%s' in config", user_config.name, setting)
            configured = False
    return configured


def parse_bool(string):
    true_strings = ["true", "True", "yes", "Yes", "1"]
    false_strings = ["false", "False", "no", "No", "0"]
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
    def irc_nickname(self):
        return self._user_config["irc_nickname"]

    @property
    def irc_server(self):
        return self._user_config["irc_server"]

    @property
    def irc_tls(self):
        return self._user_config["irc_tls"]

    @property
    def irc_tls_verify(self):
        return self._user_config["irc_tls_verify"]

    @property
    def irc_ident_password(self):
        return self._user_config["irc_ident_password"]

    @property
    def irc_inviter(self):
        return self._user_config["irc_inviter"]

    @property
    def irc_invite_cmd(self):
        return self._user_config["irc_invite_cmd"]

    @property
    def announce_delay(self):
        return self._user_config["announce_delay"]

    @property
    def notify_backends(self):
        return self.backends

    @property
    def short_name(self):
        return self._xml_config.tracker_info["shortName"]

    @property
    def type(self):
        return self._xml_config.tracker_info["type"]

    @property
    def user_channels(self):
        return [x.strip() for x in self._user_config["irc_channels"].split(",")]

    # Return both channels from XML and user config
    @property
    def irc_channels(self):
        for server in self._xml_config.servers:
            for channel in server.channels:
                yield channel

        for channel in self.user_channels:
            yield channel

    @property
    def announcer_names(self):
        for server in self._xml_config.servers:
            for announcer in server.announcers:
                yield announcer

    @property
    def line_patterns(self):
        return self._xml_config.line_patterns

    @property
    def multiline_patterns(self):
        return self._xml_config.multiline_patterns

    @property
    def ignores(self):
        return self._xml_config.ignores

    @property
    def line_matched(self):
        return self._xml_config.line_matched
