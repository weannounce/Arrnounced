import unittest
from src import announce_parser, tracker_config
from tracker_config import VarType

class LinePattern:
    def __init__(self, regex, groups):
        self.regex = regex
        self.groups = groups

class HelperVar:
    def __init__(self, varType, name):
        self.varType = varType
        self.name = name

class TrackerConfigHelper(tracker_config.TrackerConfig):
    def __init__(self, regex = None, regex_groups = [], url_vars = [],
            tracker_name = "trackername"):
        self._user_config = {}
        self._user_config["notify_sonarr"] = False
        self._user_config["notify_radarr"] = False
        self._user_config["notify_lidarr"] = False
        self._user_config["category_sonarr"] = False
        self._user_config["category_radarr"] = False
        self._user_config["category_lidarr"] = False

        self._xml_config = tracker_config.TrackerXmlConfig()
        self._xml_config.tracker_info = {"shortName": tracker_name}
        self._xml_config.line_patterns = []
        self._xml_config.torrent_url = []

    def insert_regex(self, regex, regex_groups):
        self._xml_config.line_patterns.append(LinePattern(regex, regex_groups))

    def insert_url_var(self, vartype, name):
        self._xml_config.torrent_url.append(HelperVar(vartype, name))

    def __setitem__(self, key, value):
        self._user_config[key] = value

class ParserTest(unittest.TestCase):
    def test_single_line_pattern_no_match(self):
        tc_helper = TrackerConfigHelper()
        tc_helper.insert_regex(regex = r"This Test (.*) (.*)",
                regex_groups = ["torrentName", "$group2"])
        tc_helper.insert_url_var(VarType.STRING, "fixed1")
        tc_helper.insert_url_var(VarType.VAR, "$group2")

        ann = announce_parser.parse(tc_helper, "No matching message")
        self.assertEqual(ann, None, "No match should return None")

    def test_single_line_pattern_with_match(self):
        tc_helper1 = TrackerConfigHelper()
        tc_helper1.insert_regex(regex = r"Test name: (.*) g2: (.*) g3: (.*)",
                regex_groups = ["torrentName", "$g2", "$g3"])
        tc_helper1.insert_url_var(VarType.STRING, "Start ")
        tc_helper1.insert_url_var(VarType.VAR, "$g2")
        tc_helper1.insert_url_var(VarType.STRING, " ")
        tc_helper1.insert_url_var(VarType.VARENC, "$g3")
        tc_helper1.insert_url_var(VarType.STRING, " ")
        # From user config
        tc_helper1.insert_url_var(VarType.VAR, "g4")
        tc_helper1.insert_url_var(VarType.STRING, " ")
        tc_helper1.insert_url_var(VarType.VARENC, "g5")
        tc_helper1["g4"] = "g4_text&"
        tc_helper1["g5"] = "g5_text&"

        ann = announce_parser.parse(tc_helper1, "Test name: the_name g2: g2_text& g3: g3_text&")
        self.assertEqual(ann.torrent_name, "the_name", "Name did not match")
        self.assertEqual(ann.torrent_url, "Start g2_text& g3_text%26 g4_text& g5_text%26", "Torrent URL did not match")
        self.assertEqual(ann.category, None, "Categroy was not None")

    def test_single_line_pattern_with_category(self):
        tc_helper1 = TrackerConfigHelper()
        tc_helper1.insert_regex(regex = r"Test name: (.*) g2: (.*) category: (.*)",
                regex_groups = ["torrentName", "$g2", "category"])
        tc_helper1.insert_url_var(VarType.VAR, "$g2")

        ann = announce_parser.parse(tc_helper1, "Test name: a_name g2: g2_text category: this_is_category")
        self.assertEqual(ann.torrent_name, "a_name", "Name did not match")
        self.assertEqual(ann.torrent_url, "g2_text", "Torrent URL did not match")
        self.assertEqual(ann.category, "this_is_category", "Categroy was not None")

if __name__ == "__main__":
    unittest.main()
