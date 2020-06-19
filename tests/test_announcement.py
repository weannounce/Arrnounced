import unittest
from datetime import datetime

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


def get_time_passed(announce_time):
    return (datetime.now() - announce_time).total_seconds()


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

    def __setitem__(self, key, value):
        self._user_config[key] = value


class AnnouncementTest(unittest.TestCase):
    # def setUp(self):
    #    announce_parser.multiline_matches = {}

    def test_no_torrent_name(self):
        tc_helper = TrackerConfigHelper()
        elements1 = [
            HelperXml(x)
            for x in [
                ["string", "value", "test_string"],
                ["var", "name", "var1"],
                ["varenc", "name", "var2"],
            ]
        ]

        elements2 = [
            HelperXml(x)
            for x in [
                ["var", "name", "tc1"],
                ["string", "value", " "],
                ["varenc", "name", "tc2"],
            ]
        ]

        elements3 = [HelperXml(x) for x in [["string", "value", "a_category"]]]

        tc_helper["tc1"] = "config_text1%"
        tc_helper["tc2"] = "config_text2%"

        tc_helper.insert_var("first_var", elements1)
        tc_helper.insert_var("torrentUrl", elements2)
        tc_helper.insert_var("category", elements3)
        variables = {"var1": "testvar1&", "var2": "testvar2&"}
        var = announcement.create_announcement(tc_helper, variables)
        self.assertEqual(var, None, "No match should return None")
        self.assertEqual(
            variables["first_var"],
            "test_stringtestvar1&testvar2%26",
            "Variable not correct",
        )
        self.assertEqual(
            variables["torrentUrl"],
            "config_text1% config_text2%25",
            "Variable not correct",
        )

        self.assertEqual(
            variables["category"], "a_category", "Variable not correct",
        )

    def test_no_torrent_url(self):
        tc_helper = TrackerConfigHelper()
        elements1 = [
            HelperXml(x)
            for x in [
                ["string", "value", "test_string"],
                ["var", "name", "var1"],
                ["varenc", "name", "var2"],
            ]
        ]

        elements2 = [
            HelperXml(x)
            for x in [
                ["var", "name", "tc1"],
                ["string", "value", " "],
                ["varenc", "name", "tc2"],
            ]
        ]

        elements3 = [HelperXml(x) for x in [["string", "value", "a_category"]]]

        tc_helper["tc1"] = "config_text1%"
        tc_helper["tc2"] = "config_text2%"

        tc_helper.insert_var("torrentName", elements1)
        tc_helper.insert_var("second_var", elements2)
        tc_helper.insert_var("category", elements3)
        variables = {"var1": "testvar1&", "var2": "testvar2&"}
        var = announcement.create_announcement(tc_helper, variables)
        self.assertEqual(var, None, "No match should return None")
        self.assertEqual(
            variables["torrentName"],
            "test_stringtestvar1&testvar2%26",
            "Variable not correct",
        )
        self.assertEqual(
            variables["second_var"],
            "config_text1% config_text2%25",
            "Variable not correct",
        )

        self.assertEqual(
            variables["category"], "a_category", "Variable not correct",
        )

    def test_var_not_valid(self):
        tc_helper = TrackerConfigHelper()
        elements1 = [
            HelperXml(x)
            for x in [
                ["string", "value", "test_string"],
                ["var", "name", "var1"],
                ["varenc", "name", "var2"],
            ]
        ]

        elements2 = [
            HelperXml(x)
            for x in [
                ["var", "name", "tc1"],
                ["string", "value", " "],
                ["varenc", "name", "tc2"],
            ]
        ]

        tc_helper["tc1"] = "config_text1%"
        tc_helper["tc2"] = "config_text2%"

        tc_helper.insert_var("first_var", elements1)
        tc_helper.insert_var("second_var", elements2)
        variables = {"var1": "testvar1&", "var2": "testvar2&"}
        var = announcement.create_announcement(tc_helper, variables)
        self.assertEqual(var, None, "No match should return None")
        self.assertEqual(
            variables["first_var"],
            "test_stringtestvar1&testvar2%26",
            "Variable not correct",
        )
        self.assertEqual(
            variables["second_var"],
            "config_text1% config_text2%25",
            "Variable not correct",
        )

    def test_var_valid(self):
        tc_helper = TrackerConfigHelper()
        elements1 = [
            HelperXml(x)
            for x in [
                ["string", "value", "test_string"],
                ["var", "name", "var1"],
                ["varenc", "name", "tc1"],
            ]
        ]

        elements2 = [
            HelperXml(x)
            for x in [
                ["var", "name", "var2"],
                ["string", "value", " "],
                ["varenc", "name", "tc2"],
            ]
        ]

        tc_helper["tc1"] = "config_text1%"
        tc_helper["tc2"] = "config_text2%"

        tc_helper.insert_var("torrentName", elements1)
        tc_helper.insert_var("torrentUrl", elements2)
        variables = {"var1": "testvar1&", "var2": "testvar2&"}
        announce = announcement.create_announcement(tc_helper, variables)
        self.assertNotEqual(announce, None, "No match should return None")
        self.assertEqual(
            announce.title,
            "test_stringtestvar1&config_text1%25",
            "Title does not match",
        )
        self.assertEqual(
            announce.torrent_url, "testvar2& config_text2%25", "URL does not match"
        )
        self.assertEqual(announce.category, None, "Category should be None")
        self.assertEqual(announce.indexer, "trackername", "Category should be None")
        self.assertTrue(get_time_passed(announce.date) < 0.005, "Date is wrong")


if __name__ == "__main__":
    unittest.main()
