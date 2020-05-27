import unittest

from src import announce_parser, tracker_config
from tracker_config import VarType, Ignore
from unittest import mock


class LinePattern:
    def __init__(self, regex, groups, optional=False):
        self.regex = regex
        self.groups = groups
        self.optional = optional


class HelperVar:
    def __init__(self, varType, name):
        self.varType = varType
        self.name = name


def multi_post_condition(func):
    def func_wrapper(self):
        func(self)
        self.assertEqual(len(announce_parser.multiline_matches["trackertype"]), 0)

    return func_wrapper


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
        self._xml_config.torrent_url = []

    def insert_regex(self, regex, regex_groups):
        self._xml_config.line_patterns.append(LinePattern(regex, regex_groups))

    def insert_multi_regex(self, regex, regex_groups, optional=False):
        self._xml_config.multiline_patterns.append(
            LinePattern(regex, regex_groups, optional)
        )

    def insert_ignore(self, regex, expected):
        self._xml_config.ignores.append(Ignore(regex, expected))

    def insert_url_var(self, vartype, name):
        self._xml_config.torrent_url.append(HelperVar(vartype, name))

    def __setitem__(self, key, value):
        self._user_config[key] = value


class ParserTest(unittest.TestCase):
    def setUp(self):
        announce_parser.multiline_matches = {}

    def test_single_line_pattern_no_match(self):
        tc_helper = TrackerConfigHelper()
        tc_helper.insert_regex(
            regex=r"This Test (.*) (.*)", regex_groups=["torrentName", "$group2"]
        )
        tc_helper.insert_url_var(VarType.STRING, "fixed1")
        tc_helper.insert_url_var(VarType.VAR, "$group2")

        ann = announce_parser.parse(tc_helper, "No matching message")
        self.assertEqual(ann, None, "No match should return None")

    def test_single_line_pattern_with_match(self):
        tc_helper = TrackerConfigHelper()
        tc_helper.insert_regex(
            regex=r"Test name: (.*) g2: (.*) g3: (.*)",
            regex_groups=["torrentName", "$g2", "$g3"],
        )
        tc_helper.insert_url_var(VarType.STRING, "Start ")
        tc_helper.insert_url_var(VarType.VAR, "$g2")
        tc_helper.insert_url_var(VarType.STRING, " ")
        tc_helper.insert_url_var(VarType.VARENC, "$g3")
        tc_helper.insert_url_var(VarType.STRING, " ")
        # From user config
        tc_helper.insert_url_var(VarType.VAR, "g4")
        tc_helper.insert_url_var(VarType.STRING, " ")
        tc_helper.insert_url_var(VarType.VARENC, "g5")
        tc_helper["g4"] = "g4_text&"
        tc_helper["g5"] = "g5_text&"

        # torrentName has extra whitespace added
        ann = announce_parser.parse(
            tc_helper, "Test name:  the_name  g2: g2_text& g3: g3_text&"
        )
        self.assertEqual(ann.title, "the_name", "Name did not match")
        self.assertEqual(
            ann.torrent_url,
            "Start g2_text& g3_text%26 g4_text& g5_text%26",
            "Torrent URL did not match",
        )
        self.assertEqual(ann.category, None, "Categroy was not None")

    def test_single_line_pattern_with_category(self):
        tc_helper = TrackerConfigHelper()
        tc_helper.insert_regex(
            regex=r"Test name: (.*) g2: (.*) category: (.*)",
            regex_groups=["torrentName", "$g2", "category"],
        )
        tc_helper.insert_url_var(VarType.VAR, "$g2")

        ann = announce_parser.parse(
            tc_helper, "Test name: a_name g2: g2_text category: this_is_category"
        )
        self.assertEqual(ann.title, "a_name", "Name did not match")
        self.assertEqual(ann.torrent_url, "g2_text", "Torrent URL did not match")
        self.assertEqual(ann.category, "this_is_category", "Incorrect category")

    def test_single_line_ignore_expected(self):
        tc_helper = TrackerConfigHelper()
        tc_helper.insert_regex(
            regex=r"(.*) - (.*)", regex_groups=["torrentName", "$g2"],
        )
        tc_helper.insert_url_var(VarType.VAR, "$g2")
        tc_helper.insert_ignore(r"cond1 (.*)", True)
        tc_helper.insert_ignore(r"cond2 (.*)", True)

        ann = announce_parser.parse(tc_helper, "cond1 something else")
        self.assertEqual(ann, None, "Should return None when ignored match")

        ann = announce_parser.parse(tc_helper, "cond2 something else")
        self.assertEqual(ann, None, "Should return None when ignored match")

        ann = announce_parser.parse(tc_helper, "a_name - a_group")
        self.assertEqual(ann.title, "a_name", "Name did not match")
        self.assertEqual(ann.torrent_url, "a_group", "Torrent URL did not match")
        self.assertEqual(ann.category, None, "Category not None")

    def test_single_line_ignore_unexpected(self):
        tc_helper = TrackerConfigHelper()
        tc_helper.insert_regex(
            regex=r"(.*) / (.*)", regex_groups=["torrentName", "$g2"],
        )
        tc_helper.insert_url_var(VarType.VAR, "$g2")
        tc_helper.insert_ignore(r".*/.*", False)

        ann = announce_parser.parse(tc_helper, "something else")
        self.assertEqual(ann, None, "Should return None when ignored match")

        ann = announce_parser.parse(tc_helper, "a_name / a_group")
        self.assertEqual(ann.title, "a_name", "Name did not match")
        self.assertEqual(ann.torrent_url, "a_group", "Torrent URL did not match")
        self.assertEqual(ann.category, None, "Category not None")

    def test_single_non_capture_group(self):
        tc_helper = TrackerConfigHelper()
        tc_helper.insert_regex(
            regex=r"(.*) /(?: (.*))?", regex_groups=["torrentName", "$g2"],
        )
        tc_helper.insert_url_var(VarType.VARENC, "torrentName")

        ann = announce_parser.parse(tc_helper, "name /")
        self.assertNotEqual(ann, None, "Announcement is None")
        self.assertEqual(ann.title, "name", "Name did not match")
        self.assertEqual(ann.torrent_url, "name", "Torrent URL did not match")
        self.assertEqual(ann.category, None, "Category not None")

        ann = announce_parser.parse(tc_helper, "name / group")
        self.assertNotEqual(ann, None, "Announcement is None")
        self.assertEqual(ann.title, "name", "Name did not match")
        self.assertEqual(ann.torrent_url, "name", "Torrent URL did not match")
        self.assertEqual(ann.category, None, "Category not None")

    @multi_post_condition
    def test_multi_line_pattern_simple(self):
        tc_helper = TrackerConfigHelper()
        tc_helper.insert_multi_regex(
            regex=r"Row1 name: (.*)", regex_groups=["torrentName"]
        )
        tc_helper.insert_multi_regex(regex=r"Row2 g2: (.*)", regex_groups=["$g2"])
        tc_helper.insert_multi_regex(regex=r"Row3 g3: (.*)", regex_groups=["$g3"])
        tc_helper.insert_url_var(VarType.STRING, "Start ")
        tc_helper.insert_url_var(VarType.VAR, "$g2")
        tc_helper.insert_url_var(VarType.STRING, " ")
        tc_helper.insert_url_var(VarType.VAR, "$g3")

        ann = announce_parser.parse(tc_helper, "Row2 g2: g2_error")
        self.assertEqual(ann, None, "Should return None if matched rows not in order")

        # torrentName has extra whitespace added
        ann = announce_parser.parse(tc_helper, "Row1 name:  the_name")
        self.assertEqual(ann, None, "No match should return None")

        ann = announce_parser.parse(tc_helper, "Row3 g3: g3_error")
        self.assertEqual(ann, None, "Should return None if matched rows not in order")

        ann = announce_parser.parse(tc_helper, "Row2 g2: g2_text")
        self.assertEqual(ann, None, "Announcement is None")

        ann = announce_parser.parse(tc_helper, "Row3 g3: g3_text")
        self.assertEqual(ann.title, "the_name", "Name did not match")
        self.assertEqual(
            ann.torrent_url, "Start g2_text g3_text", "Torrent URL did not match"
        )
        self.assertEqual(ann.category, None, "Categroy was not None")

    @multi_post_condition
    def test_multi_line_pattern_two_in_parallel(self):
        tc_helper = TrackerConfigHelper()
        tc_helper.insert_multi_regex(
            regex=r"Row1 name: (.*)", regex_groups=["torrentName"]
        )
        tc_helper.insert_multi_regex(regex=r"Row2 g2: (.*)", regex_groups=["$g2"])
        tc_helper.insert_url_var(VarType.VAR, "$g2")

        ann = announce_parser.parse(tc_helper, "Row1 name: first_name")
        self.assertEqual(ann, None, "No match should return None")
        ann = announce_parser.parse(tc_helper, "Row1 name: second_name")
        self.assertEqual(ann, None, "No match should return None")

        ann = announce_parser.parse(tc_helper, "Row2 g2: first_g2")
        self.assertEqual(ann.title, "first_name", "Name did not match")
        self.assertEqual(ann.torrent_url, "first_g2", "Torrent URL did not match")
        self.assertEqual(ann.category, None, "Categroy was not None")

        ann = announce_parser.parse(tc_helper, "Row2 g2: second_g2")
        self.assertEqual(ann.title, "second_name", "Name did not match")
        self.assertEqual(ann.torrent_url, "second_g2", "Torrent URL did not match")
        self.assertEqual(ann.category, None, "Categroy was not None")

    @multi_post_condition
    def test_multi_line_pattern_optional_in_middle(self):
        tc_helper = TrackerConfigHelper()
        tc_helper.insert_multi_regex(
            regex=r"Row1 name: (.*)", regex_groups=["torrentName"]
        )
        tc_helper.insert_multi_regex(
            regex=r"Row2 g2: (.*)", regex_groups=["$g2"], optional=True
        )
        tc_helper.insert_multi_regex(regex=r"Row3 g3: (.*)", regex_groups=["$g3"])
        tc_helper.insert_url_var(VarType.VAR, "$g3")

        ann = announce_parser.parse(tc_helper, "Row1 name: a_name")
        self.assertEqual(ann, None, "No match should return None")

        ann = announce_parser.parse(tc_helper, "Row3 g3: g3_text")
        self.assertNotEqual(ann, None, "Announcement is None")
        self.assertEqual(ann.title, "a_name", "Name did not match")
        self.assertEqual(ann.torrent_url, "g3_text", "Torrent URL did not match")
        self.assertEqual(ann.category, None, "Categroy was not None")

    @multi_post_condition
    def test_multi_line_pattern_optional_at_end(self):
        tc_helper = TrackerConfigHelper()
        tc_helper.insert_multi_regex(
            regex=r"Row1 name: (.*)", regex_groups=["torrentName"]
        )
        tc_helper.insert_multi_regex(regex=r"Row2 g2: (.*)", regex_groups=["$g2"])
        tc_helper.insert_multi_regex(
            regex=r"Row3 g3: (.*)", regex_groups=["$g3"], optional=True
        )
        tc_helper.insert_url_var(VarType.VAR, "$g2")

        ann = announce_parser.parse(tc_helper, "Row1 name: another_name")
        self.assertEqual(ann, None, "No match should return None")

        ann = announce_parser.parse(tc_helper, "Row2 g2: g2_text")
        self.assertNotEqual(ann, None, "Announcement is None")
        self.assertEqual(ann.title, "another_name", "Name did not match")
        self.assertEqual(ann.torrent_url, "g2_text", "Torrent URL did not match")
        self.assertEqual(ann.category, None, "Categroy was not None")

    @multi_post_condition
    def test_multi_line_pattern_optional_in_middle_and_end(self):
        tc_helper = TrackerConfigHelper()
        tc_helper.insert_multi_regex(
            regex=r"Row1 name: (.*)", regex_groups=["torrentName"]
        )
        tc_helper.insert_multi_regex(
            regex=r"Row2 g2: (.*)", regex_groups=["$g2"], optional=True
        )
        tc_helper.insert_multi_regex(
            regex=r"Row3 g3: (.*)", regex_groups=["$g3"],
        )
        tc_helper.insert_multi_regex(
            regex=r"Row4 g4: (.*)", regex_groups=["$g4"], optional=True
        )
        tc_helper.insert_url_var(VarType.VAR, "$g3")

        ann = announce_parser.parse(tc_helper, "Row1 name: another_name")
        self.assertEqual(ann, None, "No match should return None")

        ann = announce_parser.parse(tc_helper, "Row3 g3: g3_text")
        self.assertNotEqual(ann, None, "Announcement is None")
        self.assertEqual(ann.title, "another_name", "Name did not match")
        self.assertEqual(ann.torrent_url, "g3_text", "Torrent URL did not match")
        self.assertEqual(ann.category, None, "Categroy was not None")

    @multi_post_condition
    def test_multi_line_pattern_parse_optional(self):
        tc_helper = TrackerConfigHelper()
        tc_helper.insert_multi_regex(
            regex=r"Row1 name: (.*)", regex_groups=["torrentName"]
        )
        tc_helper.insert_multi_regex(
            regex=r"Row2 g2: (.*)", regex_groups=["$g2"], optional=True
        )
        tc_helper.insert_multi_regex(
            regex=r"Row3 g3: (.*)", regex_groups=["$g3"],
        )
        tc_helper.insert_multi_regex(
            regex=r"Row4 g4: (.*)", regex_groups=["$g4"], optional=True
        )
        tc_helper.insert_url_var(VarType.VAR, "$g3")

        ann = announce_parser.parse(tc_helper, "Row1 name: another_name")
        self.assertEqual(ann, None, "No match should return None")

        ann = announce_parser.parse(tc_helper, "Row2 name: g2_text")
        self.assertEqual(ann, None, "No match should return None")

        ann = announce_parser.parse(tc_helper, "Row3 g3: g3_text")
        self.assertNotEqual(ann, None, "Announcement is None")
        self.assertEqual(ann.title, "another_name", "Name did not match")
        self.assertEqual(ann.torrent_url, "g3_text", "Torrent URL did not match")
        self.assertEqual(ann.category, None, "Categroy was not None")

    @multi_post_condition
    def test_multi_line_pattern_parallel_optional(self):
        tc_helper = TrackerConfigHelper()
        tc_helper.insert_multi_regex(
            regex=r"Row1 name: (.*)", regex_groups=["torrentName"]
        )
        tc_helper.insert_multi_regex(
            regex=r"Row2 g2: (.*)", regex_groups=["$g2"], optional=True
        )
        tc_helper.insert_multi_regex(
            regex=r"Row3 g3: (.*)", regex_groups=["$g3"],
        )
        tc_helper.insert_multi_regex(regex=r"Row4 g4: (.*)", regex_groups=["$g4"])
        tc_helper.insert_url_var(VarType.VAR, "$g3")
        tc_helper.insert_url_var(VarType.VAR, "$g4")

        ann = announce_parser.parse(tc_helper, "Row1 name: a_name")
        self.assertEqual(ann, None, "No match should return None")

        ann = announce_parser.parse(tc_helper, "Row1 name: another_name")
        self.assertEqual(ann, None, "No match should return None")

        ann = announce_parser.parse(tc_helper, "Row3 g3: g3_text1")
        self.assertEqual(ann, None, "No match should return None")

        ann = announce_parser.parse(tc_helper, "Row2 g2: g2_text")
        self.assertEqual(ann, None, "No match should return None")

        ann = announce_parser.parse(tc_helper, "Row3 g3: g3_text2")
        self.assertEqual(ann, None, "No match should return None")

        ann = announce_parser.parse(tc_helper, "Row4 g4: g4_text1")
        self.assertNotEqual(ann, None, "Announcement is None")
        self.assertEqual(ann.title, "a_name", "Name did not match")
        self.assertEqual(
            ann.torrent_url, "g3_text1g4_text1", "Torrent URL did not match"
        )
        self.assertEqual(ann.category, None, "Categroy was not None")

        ann = announce_parser.parse(tc_helper, "Row4 g4: g4_text2")
        self.assertNotEqual(ann, None, "Announcement is None")
        self.assertEqual(ann.title, "another_name", "Name did not match")
        self.assertEqual(
            ann.torrent_url, "g3_text2g4_text2", "Torrent URL did not match"
        )
        self.assertEqual(ann.category, None, "Categroy was not None")

    @mock.patch("time.time", mock.MagicMock(side_effect=[0, 15]))
    @multi_post_condition
    def test_multi_line_pattern_announcement_completed_just_in_time(self):
        tc_helper = TrackerConfigHelper()
        tc_helper.insert_multi_regex(
            regex=r"Row1 name: (.*)", regex_groups=["torrentName"]
        )
        tc_helper.insert_multi_regex(regex=r"Row2 g2: (.*)", regex_groups=["$g2"])
        tc_helper.insert_url_var(VarType.VAR, "$g2")

        ann = announce_parser.parse(tc_helper, "Row1 name: a_name")
        self.assertEqual(ann, None, "No match should return None")

        ann = announce_parser.parse(tc_helper, "Row2 g2: g2_text")
        self.assertNotEqual(ann, None, "Announcement is None")
        self.assertEqual(ann.title, "a_name", "Name did not match")
        self.assertEqual(ann.torrent_url, "g2_text", "Torrent URL did not match")
        self.assertEqual(ann.category, None, "Categroy was not None")

    # First two mock values are for time comparisons
    # Second two values are for logger
    @mock.patch("time.time", mock.MagicMock(side_effect=[0, 15.1, 0, 0]))
    @multi_post_condition
    def test_multi_line_pattern_discard_too_old(self):
        tc_helper = TrackerConfigHelper()
        tc_helper.insert_multi_regex(
            regex=r"Row1 name: (.*)", regex_groups=["torrentName"]
        )
        tc_helper.insert_multi_regex(regex=r"Row2 g2: (.*)", regex_groups=["$g2"])
        tc_helper.insert_url_var(VarType.VAR, "$g2")

        ann = announce_parser.parse(tc_helper, "Row1 name: a_name")
        self.assertEqual(ann, None, "No match should return None")

        ann = announce_parser.parse(tc_helper, "Row2 g2: g2_text")
        self.assertEqual(
            ann, None, "Announcement should be discarded for being too old"
        )

    # Mock value: (insert1), (check1, insert2), (check1, log warning, check2)
    @mock.patch("time.time", mock.MagicMock(side_effect=[0, 10, 10, 16, 16, 16]))
    @multi_post_condition
    def test_multi_line_pattern_parallell_first_too_old(self):
        tc_helper = TrackerConfigHelper()
        tc_helper.insert_multi_regex(
            regex=r"Row1 name: (.*)", regex_groups=["torrentName"]
        )
        tc_helper.insert_multi_regex(regex=r"Row2 g2: (.*)", regex_groups=["$g2"])
        tc_helper.insert_url_var(VarType.VAR, "$g2")

        ann = announce_parser.parse(tc_helper, "Row1 name: a_name")
        self.assertEqual(ann, None, "No match should return None")

        ann = announce_parser.parse(tc_helper, "Row1 name: two_name")
        self.assertEqual(ann, None, "No match should return None")

        ann = announce_parser.parse(tc_helper, "Row2 g2: g2_text1")
        self.assertNotEqual(ann, None, "Announcement is None")
        self.assertEqual(ann.title, "two_name", "Name did not match")
        self.assertEqual(ann.torrent_url, "g2_text1", "Torrent URL did not match")
        self.assertEqual(ann.category, None, "Categroy was not None")

    @multi_post_condition
    def test_multi_non_capture_group(self):
        tc_helper = TrackerConfigHelper()
        tc_helper.insert_multi_regex(
            regex=r"Row1 name: (.*)", regex_groups=["torrentName"]
        )
        tc_helper.insert_multi_regex(regex=r"Row2 g2:(?: (.*))?", regex_groups=["$g2"])
        tc_helper.insert_url_var(VarType.VARENC, "torrentName")

        ann = announce_parser.parse(tc_helper, "Row1 name: a_name")
        self.assertEqual(ann, None, "First row in multi should return None")
        ann = announce_parser.parse(tc_helper, "Row2 g2:")
        self.assertNotEqual(ann, None, "Announcement is None")
        self.assertEqual(ann.title, "a_name", "Name did not match")
        self.assertEqual(ann.torrent_url, "a_name", "Torrent URL did not match")
        self.assertEqual(ann.category, None, "Category not None")

        ann = announce_parser.parse(tc_helper, "Row1 name: a_name")
        self.assertEqual(ann, None, "First row in multi should return None")
        ann = announce_parser.parse(tc_helper, "Row2 g2: a_group")
        self.assertNotEqual(ann, None, "Announcement is None")
        self.assertEqual(ann.title, "a_name", "Name did not match")
        self.assertEqual(ann.torrent_url, "a_name", "Torrent URL did not match")
        self.assertEqual(ann.category, None, "Category not None")


if __name__ == "__main__":
    unittest.main()
