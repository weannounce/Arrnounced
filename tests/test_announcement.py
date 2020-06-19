import unittest

from src import announcement, tracker_config
from announcement import Var

#    Http,
#    Extract,
#    ExtractOne,
#    ExtractTags,
#    VarReplace,
#    SetRegex,
#    If,


class HelperXml:
    def __init__(self, data):
        self.tag = data[0]
        self.attrib = {data[1]: data[2]}


class TrackerConfigHelper(tracker_config.TrackerConfig):
    def __init__(
        self,
        regex=None,
        regex_groups=[],
        url_vars=[],
        tracker_name="trackername",
        tracker_type="trackertype",
    ):
        self._user_config = {}
        self._user_config["notify_sonarr"] = False
        self._user_config["notify_radarr"] = False
        self._user_config["notify_lidarr"] = False
        self._user_config["category_sonarr"] = False
        self._user_config["category_radarr"] = False
        self._user_config["category_lidarr"] = False

        self._xml_config = tracker_config.TrackerXmlConfig()
        self._xml_config.tracker_info = {
            "shortName": tracker_name,
            "type": tracker_type,
        }
        self._xml_config.line_patterns = []
        self._xml_config.multiline_patterns = []
        self._xml_config.ignores = []
        self._xml_config.line_matched = []

    def insert_var(self, var_name, elements):
        self._xml_config.line_matched.append(Var(var_name, elements))


class AnnouncementTest(unittest.TestCase):
    # def setUp(self):
    #    announce_parser.multiline_matches = {}

    def test_single_line_pattern_no_match(self):
        tc_helper = TrackerConfigHelper()
        elements = [
            HelperXml(x)
            for x in [
                ["string", "value", "test_string"],
                ["var", "name", "var1"],
                ["varenc", "name", "var2"],
            ]
        ]
        tc_helper.insert_var("first_var", elements)
        tc_helper.insert_var("second_var", elements)
        variables = {"var1": "testvar1&", "var2": "testvar2&"}
        var = announcement.create_announcement(tc_helper, variables)
        self.assertEqual(var, None, "No match should return None")
        self.assertEqual(
            variables["first_var"],
            "test_stringtestvar1&testvar2%26",
            "Variable not correct",
        )


if __name__ == "__main__":
    unittest.main()
