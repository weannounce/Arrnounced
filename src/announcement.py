import logging
import urllib.parse
from datetime import datetime
from enum import Enum

logger = logging.getLogger("ANNOUNCEMENT")


class Announcement:
    def __init__(self, title, url, category=None, date=None, indexer=None):
        self.title = title
        self.torrent_url = url
        self.category = category
        self.date = date
        self.indexer = indexer


def create_announcement(tracker_config, variables):
    for line_match in tracker_config.line_matched:
        line_match.process(tracker_config, variables)

    # TODO: Handle missing variables
    if variables.get("torrentName") is None:
        logger.warning("Missing torrent name")
        return None

    # TODO: User config option to use https
    return Announcement(
        variables["torrentName"],
        variables["torrentUrl"],
        variables.get("category"),
        date=datetime.now(),
        indexer=tracker_config.short_name,
    )


class Var:
    def __init__(self, var_name, elements):
        self.var_name = var_name
        self.elements = []
        for element in elements:
            self.elements.append(Var.Element(element.tag, element.attrib))

    def process(self, tracker_config, variables):
        var = ""
        for element in self.elements:
            if element.var_type is self.Element.Type.STRING:
                var = var + element.name
            elif element.var_type is self.Element.Type.VAR:
                if element.name in variables:
                    var = var + variables[element.name]
                else:
                    var = var + tracker_config[element.name]
            elif element.var_type is self.Element.Type.VARENC:
                if element.name in variables:
                    var_value = variables[element.name]
                else:
                    var_value = tracker_config[element.name]
                var = var + urllib.parse.quote_plus(var_value)

        variables[self.var_name] = var

    class Element:
        class Type(Enum):
            STRING = 1
            VAR = 2
            VARENC = 3

        type_to_name = {Type.STRING: "value", Type.VAR: "name", Type.VARENC: "name"}

        def __init__(self, var_type, var):
            self.var_type = self.Type[var_type.upper()]
            self.name = var[self.type_to_name[self.var_type]]


class Http:
    def __init__(self):
        pass

    def process(self, tracker_config, variables):
        pass


class Extract:
    def __init__(self):
        pass

    def process(self, tracker_config, variables):
        pass


class ExtractOne:
    def __init__(self):
        pass

    def process(self, tracker_config, variables):
        pass


class ExtractTags:
    def __init__(self):
        pass

    def process(self, tracker_config, variables):
        pass


class VarReplace:
    def __init__(self):
        pass

    def process(self, tracker_config, variables):
        pass


class SetRegex:
    def __init__(self):
        pass

    def process(self, tracker_config, variables):
        pass


class If:
    def __init__(self):
        pass

    def process(self, tracker_config, variables):
        pass
