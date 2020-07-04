import logging
import urllib.parse
from datetime import datetime
from enum import Enum
import re

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

    # TODO: Handle missing https variables
    if variables.get("torrentName") is None:
        logger.warning("Missing torrent name")
        return None
    elif variables.get("torrentUrl") is None:
        logger.warning("Missing torrent URL")
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
    def __init__(self, srcvar, regex, groups, optional):
        self.srcvar = srcvar
        self.regex = regex
        self.groups = groups
        self.optional = optional

    # Returns None when no match was found
    def process_string(self, string):
        matches = re.search(self.regex, string)
        if matches:
            match_groups = {}
            for j, group_name in enumerate(self.groups, start=1):
                # Filter out missing non-capturing groups
                match = matches.group(j)
                if match is not None and not match.isspace():
                    match_groups[group_name] = match.strip()
            return match_groups

        return None

    def get_extract_variables(self, variables):
        match_groups = None
        if self.srcvar in variables:
            match_groups = self.process_string(variables[self.srcvar])
        return match_groups

    def process(self, tracker_config, variables):
        match_groups = self.get_extract_variables(variables)

        if match_groups is not None:
            variables.update(match_groups)
        elif not self.optional:
            logger.warning(
                "Extract: Variable '%s' did not match regex '%s'",
                self.srcvar,
                self.regex,
            )


class ExtractOne:
    def __init__(self, extracts):
        self.extracts = extracts

    def process(self, tracker_config, variables):
        for extract in self.extracts:
            extract_vars = extract.get_extract_variables(variables)
            if extract_vars is not None:
                variables.update(extract_vars)
                return

        logger.warning("ExtractOne: No matching regex found")


class ExtractTags:
    def __init__(self, srcvar, split, setvarifs):
        self.srcvar = srcvar
        self.split = split
        self.setvarifs = setvarifs

    def process(self, tracker_config, variables):
        if self.srcvar not in variables:
            logger.warning(
                "ExtractTags: Could not extract tags, variable '%s' not found",
                self.srcvar,
            )
            return

        for tag_name in [
            x.strip() for x in re.split(self.split, variables[self.srcvar])
        ]:
            if not tag_name:
                continue

            for setvarif in self.setvarifs:
                new_value = setvarif.get_value(tag_name)
                if new_value is not None:
                    variables[setvarif.var_name] = new_value
                    break

    class SetVarIf:
        def __init__(self, var_name, regex, value, new_value):
            self.var_name = var_name
            self.regex = regex
            self.value = value
            self.new_value = new_value

        def get_value(self, tag_name):
            if (self.value is not None and self.value.lower() != tag_name.lower()) or (
                self.regex is not None and re.search(self.regex, tag_name) is None
            ):
                return None

            return self.new_value if self.new_value is not None else tag_name


class VarReplace:
    def __init__(self, name, srcvar, regex, replace):
        self.name = name
        self.srcvar = srcvar
        self.regex = regex
        self.replace = replace

    def process(self, tracker_config, variables):
        if self.srcvar not in variables:
            logger.warning(
                "VarReplace: Could not replace, variable '%s' not found", self.srcvar
            )
            return

        variables[self.name] = re.sub(self.regex, self.replace, variables[self.srcvar])


class SetRegex:
    def __init__(self, srcvar, regex, var_name, new_value):
        self.srcvar = srcvar
        self.regex = regex
        self.var_name = var_name
        self.new_value = new_value

    def process(self, tracker_config, variables):
        if self.srcvar not in variables:
            logger.warning(
                "SetRegex: Could not set variable, variable '%s' not found", self.srcvar
            )
            return

        if re.search(self.regex, variables[self.srcvar]):
            variables[self.var_name] = self.new_value


class If:
    def __init__(self):
        pass

    def process(self, tracker_config, variables):
        pass
