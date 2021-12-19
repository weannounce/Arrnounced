import logging
import os
import re
import defusedxml.ElementTree as ET
from collections import namedtuple

from arrnounced.announcement import (
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


def get_tracker_xml_configs(tracker_config_path):
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
