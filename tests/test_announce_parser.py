import unittest

from arrnounced import announcement, announce_parser, tracker, tracker_xml_config, utils
from tracker_xml_config import Ignore
from unittest import mock


class HelperVar:
    def __init__(self, varType, name):
        self.varType = varType
        self.name = name


def multi_post_condition(func):
    def func_wrapper(self):
        func(self)
        self.assertEqual(len(announce_parser.multiline_matches["trackertype"]), 0)

    return func_wrapper


class TrackerHelper:
    def __init__(self):
        self.config = TrackerConfigHelper()


class TrackerConfigHelper(tracker.TrackerConfig):
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

        self._xml_config = tracker_xml_config.TrackerXmlConfig()
        self._xml_config.tracker_info = {
            "shortName": tracker_name,
            "type": tracker_type,
        }
        self._xml_config.line_patterns = []
        self._xml_config.multiline_patterns = []
        self._xml_config.ignores = []
        self._xml_config.line_matched = []

    def insert_regex(self, regex, regex_groups):
        self._xml_config.line_patterns.append(
            announcement.Extract(None, regex, regex_groups, False)
        )

    def insert_multi_regex(self, regex, regex_groups, optional=False):
        self._xml_config.multiline_patterns.append(
            announcement.Extract(None, regex, regex_groups, optional)
        )

    def insert_ignore(self, regex, expected):
        self._xml_config.ignores.append(Ignore(regex, expected))


class ParserTest(unittest.TestCase):
    def setUp(self):
        announce_parser.multiline_matches = {}

    def test_single_line_pattern_no_match(self):
        th = TrackerHelper()
        th.config.insert_regex(
            regex=r"This Test (.*) (.*)", regex_groups=["torrentName", "$group2"]
        )
        var = announce_parser.parse(th, "No matching message")
        self.assertEqual(var, None, "No match should return None")

    def test_single_line_pattern_with_match(self):
        th = TrackerHelper()
        th.config.insert_regex(
            regex=r"Test name: (.*) g2: (.*) g3: (.*)",
            regex_groups=["torrentName", "$g2", "$g3"],
        )

        # torrentName has extra whitespace added
        var = announce_parser.parse(
            th, "Test name:  the_name  g2: g2_text& g3: g3_text&"
        )

        self.assertEqual(len(var), 2 + len(utils.get_default_variables()))
        self.assertEqual(var["torrentName"], "the_name", "Name did not match")
        self.assertEqual(var["$g2"], "g2_text&", "g2 did not match")
        self.assertEqual(var["$g3"], "g3_text&", "g3 did not match")

    def test_single_line_pattern_with_category(self):
        th = TrackerHelper()
        th.config.insert_regex(
            regex=r"Test name: (.*) g2: (.*) category: (.*)",
            regex_groups=["torrentName", "$g2", "category"],
        )

        var = announce_parser.parse(
            th, "Test name: a_name g2: g2_text category: this_is_category"
        )

        self.assertEqual(len(var), 1 + len(utils.get_default_variables()))
        self.assertEqual(var["torrentName"], "a_name", "Name did not match")
        self.assertEqual(var["$g2"], "g2_text", "g2 did not match")
        self.assertEqual(var["category"], "this_is_category", "category did not match")

    def test_single_line_ignore_expected(self):
        th = TrackerHelper()
        th.config.insert_regex(
            regex=r"(.*) - (.*)",
            regex_groups=["torrentName", "$g2"],
        )
        th.config.insert_ignore(r"cond1 (.*)", True)
        th.config.insert_ignore(r"cond2 (.*)", True)

        var = announce_parser.parse(th, "cond1 something else")
        self.assertEqual(var, None, "Should return None when ignored match")

        var = announce_parser.parse(th, "cond2 something else")
        self.assertEqual(var, None, "Should return None when ignored match")

        var = announce_parser.parse(th, "a_name - a_group")
        self.assertEqual(len(var), 1 + len(utils.get_default_variables()))
        self.assertEqual(var["torrentName"], "a_name", "Name did not match")
        self.assertEqual(var["$g2"], "a_group", "g2 did not match")

    def test_single_line_ignore_unexpected(self):
        th = TrackerHelper()
        th.config.insert_regex(
            regex=r"(.*) / (.*)",
            regex_groups=["torrentName", "$g2"],
        )
        th.config.insert_ignore(r".*/.*", False)

        var = announce_parser.parse(th, "something else")
        self.assertEqual(var, None, "Should return None when ignored match")

        var = announce_parser.parse(th, "a_name / a_group")
        self.assertEqual(len(var), 1 + len(utils.get_default_variables()))
        self.assertEqual(var["torrentName"], "a_name", "Name did not match")
        self.assertEqual(var["$g2"], "a_group", "g2 did not match")

    def test_single_non_capture_group(self):
        th = TrackerHelper()
        th.config.insert_regex(
            regex=r"(.*) /(?: (.*))?",
            regex_groups=["torrentName", "$g2"],
        )

        var = announce_parser.parse(th, "name /")
        self.assertEqual(len(var), len(utils.get_default_variables()))
        self.assertEqual(var["torrentName"], "name", "Name did not match")

        var = announce_parser.parse(th, "name / group")
        self.assertEqual(len(var), 1 + len(utils.get_default_variables()))
        self.assertEqual(var["torrentName"], "name", "Name did not match")
        self.assertEqual(var["$g2"], "group", "g2 did not match")

    def test_single_empty_groups(self):
        th = TrackerHelper()
        th.config.insert_regex(
            regex=r"(.*) / (.*)",
            regex_groups=["torrentName", "$g2"],
        )

        var = announce_parser.parse(th, "  / the_group")
        self.assertEqual(len(var), 1 + len(utils.get_default_variables()))
        self.assertEqual(var["$g2"], "the_group", "$g2 did not match")

        var = announce_parser.parse(th, "a_name /  ")
        self.assertEqual(len(var), len(utils.get_default_variables()))
        self.assertEqual(var["torrentName"], "a_name", "$g2 did not match")

    def test_single_default_variables(self):
        th = TrackerHelper()
        th.config.insert_regex(
            regex=r"Test g1: (.*) g2: (.*) g3: (.*)",
            regex_groups=["$g1", "$g2", "$g3"],
        )

        var = announce_parser.parse(th, "Test g1:  g1_text  g2: g2_text& g3: g3_text&")

        self.assertEqual(len(var), 3 + len(utils.get_default_variables()))
        self.assertEqual(var["$g1"], "g1_text", "g1 did not match")
        self.assertEqual(var["$g2"], "g2_text&", "g2 did not match")
        self.assertEqual(var["$g3"], "g3_text&", "g3 did not match")

        for key in utils.get_default_variables():
            self.assertEqual(var[key], "", "default value did not match")

    def test_multi_line_pattern_no_match(self):
        th = TrackerHelper()
        th.config.insert_multi_regex(
            regex=r"Row1 name: (.*)", regex_groups=["torrentName"]
        )
        th.config.insert_multi_regex(regex=r"Row2 g2: (.*)", regex_groups=["$g2"])

        # torrentName has extra whitespace added
        var = announce_parser.parse(th, "something else")
        self.assertEqual(var, None, "No match should return None")

        self.assertEqual(len(announce_parser.multiline_matches), 0)

    @multi_post_condition
    def test_multi_line_pattern_simple(self):
        th = TrackerHelper()
        th.config.insert_multi_regex(
            regex=r"Row1 name: (.*)", regex_groups=["torrentName"]
        )
        th.config.insert_multi_regex(regex=r"Row2 g2: (.*)", regex_groups=["$g2"])
        th.config.insert_multi_regex(regex=r"Row3 g3: (.*)", regex_groups=["$g3"])

        var = announce_parser.parse(th, "Row2 g2: g2_error")
        self.assertEqual(var, None, "Should return None if matched rows not in order")

        # torrentName has extra whitespace added
        var = announce_parser.parse(th, "Row1 name:  the_name")
        self.assertEqual(var, None, "No match should return None")

        var = announce_parser.parse(th, "Row3 g3: g3_error")
        self.assertEqual(var, None, "Should return None if matched rows not in order")

        var = announce_parser.parse(th, "Row2 g2: g2_text")
        self.assertEqual(var, None, "Announcement is None")

        var = announce_parser.parse(th, "Row3 g3: g3_text")
        self.assertEqual(len(var), 2 + len(utils.get_default_variables()))
        self.assertEqual(var["torrentName"], "the_name", "Name did not match")
        self.assertEqual(var["$g2"], "g2_text", "g2 did not match")
        self.assertEqual(var["$g3"], "g3_text", "g3 did not match")

    @multi_post_condition
    def test_multi_line_pattern_two_in_parallel(self):
        th = TrackerHelper()
        th.config.insert_multi_regex(
            regex=r"Row1 name: (.*)", regex_groups=["torrentName"]
        )
        th.config.insert_multi_regex(regex=r"Row2 g2: (.*)", regex_groups=["$g2"])

        var = announce_parser.parse(th, "Row1 name: first_name")
        self.assertEqual(var, None, "No match should return None")
        var = announce_parser.parse(th, "Row1 name: second_name")
        self.assertEqual(var, None, "No match should return None")

        var = announce_parser.parse(th, "Row2 g2: first_g2")
        self.assertEqual(len(var), 1 + len(utils.get_default_variables()))
        self.assertEqual(var["torrentName"], "first_name", "Name did not match")
        self.assertEqual(var["$g2"], "first_g2", "g2 did not match")

        var = announce_parser.parse(th, "Row2 g2: second_g2")
        self.assertEqual(len(var), 1 + len(utils.get_default_variables()))
        self.assertEqual(var["torrentName"], "second_name", "Name did not match")
        self.assertEqual(var["$g2"], "second_g2", "g2 did not match")

    @multi_post_condition
    def test_multi_line_pattern_optional_in_middle(self):
        th = TrackerHelper()
        th.config.insert_multi_regex(
            regex=r"Row1 name: (.*)", regex_groups=["torrentName"]
        )
        th.config.insert_multi_regex(
            regex=r"Row2 g2: (.*)", regex_groups=["$g2"], optional=True
        )
        th.config.insert_multi_regex(regex=r"Row3 g3: (.*)", regex_groups=["$g3"])

        var = announce_parser.parse(th, "Row1 name: a_name")
        self.assertEqual(var, None, "No match should return None")

        var = announce_parser.parse(th, "Row3 g3: g3_text")
        self.assertEqual(len(var), 1 + len(utils.get_default_variables()))
        self.assertEqual(var["torrentName"], "a_name", "Name did not match")
        self.assertEqual(var["$g3"], "g3_text", "g2 did not match")

    @multi_post_condition
    def test_multi_line_pattern_optional_at_end(self):
        th = TrackerHelper()
        th.config.insert_multi_regex(
            regex=r"Row1 name: (.*)", regex_groups=["torrentName"]
        )
        th.config.insert_multi_regex(regex=r"Row2 g2: (.*)", regex_groups=["$g2"])
        th.config.insert_multi_regex(
            regex=r"Row3 g3: (.*)", regex_groups=["$g3"], optional=True
        )

        var = announce_parser.parse(th, "Row1 name: another_name")
        self.assertEqual(var, None, "No match should return None")

        var = announce_parser.parse(th, "Row2 g2: g2_text")
        self.assertEqual(len(var), 1 + len(utils.get_default_variables()))
        self.assertEqual(var["torrentName"], "another_name", "Name did not match")
        self.assertEqual(var["$g2"], "g2_text", "g2 did not match")

    @multi_post_condition
    def test_multi_line_pattern_optional_in_middle_and_end(self):
        th = TrackerHelper()
        th.config.insert_multi_regex(
            regex=r"Row1 name: (.*)", regex_groups=["torrentName"]
        )
        th.config.insert_multi_regex(
            regex=r"Row2 g2: (.*)", regex_groups=["$g2"], optional=True
        )
        th.config.insert_multi_regex(
            regex=r"Row3 g3: (.*)",
            regex_groups=["$g3"],
        )
        th.config.insert_multi_regex(
            regex=r"Row4 g4: (.*)", regex_groups=["$g4"], optional=True
        )

        var = announce_parser.parse(th, "Row1 name: another_name")
        self.assertEqual(var, None, "No match should return None")

        var = announce_parser.parse(th, "Row3 g3: g3_text")
        self.assertEqual(len(var), 1 + len(utils.get_default_variables()))
        self.assertEqual(var["torrentName"], "another_name", "Name did not match")
        self.assertEqual(var["$g3"], "g3_text", "g2 did not match")

    @multi_post_condition
    def test_multi_line_pattern_parse_optional(self):
        th = TrackerHelper()
        th.config.insert_multi_regex(
            regex=r"Row1 name: (.*)", regex_groups=["torrentName"]
        )
        th.config.insert_multi_regex(
            regex=r"Row2 g2: (.*)", regex_groups=["$g2"], optional=True
        )
        th.config.insert_multi_regex(
            regex=r"Row3 g3: (.*)",
            regex_groups=["$g3"],
        )
        th.config.insert_multi_regex(
            regex=r"Row4 g4: (.*)", regex_groups=["$g4"], optional=True
        )

        var = announce_parser.parse(th, "Row1 name: another_name")
        self.assertEqual(var, None, "No match should return None")

        var = announce_parser.parse(th, "Row2 g2: g2_text")
        self.assertEqual(var, None, "No match should return None")

        var = announce_parser.parse(th, "Row3 g3: g3_text")
        self.assertEqual(len(var), 2 + len(utils.get_default_variables()))
        self.assertEqual(var["torrentName"], "another_name", "Name did not match")
        self.assertEqual(var["$g2"], "g2_text", "g2 did not match")
        self.assertEqual(var["$g3"], "g3_text", "g2 did not match")

    @multi_post_condition
    def test_multi_line_pattern_parallel_optional(self):
        th = TrackerHelper()
        th.config.insert_multi_regex(
            regex=r"Row1 name: (.*)", regex_groups=["torrentName"]
        )
        th.config.insert_multi_regex(
            regex=r"Row2 g2: (.*)", regex_groups=["$g2"], optional=True
        )
        th.config.insert_multi_regex(
            regex=r"Row3 g3: (.*)",
            regex_groups=["$g3"],
        )
        th.config.insert_multi_regex(regex=r"Row4 g4: (.*)", regex_groups=["$g4"])

        var = announce_parser.parse(th, "Row1 name: a_name")
        self.assertEqual(var, None, "No match should return None")

        var = announce_parser.parse(th, "Row1 name: another_name")
        self.assertEqual(var, None, "No match should return None")

        var = announce_parser.parse(th, "Row3 g3: g3_text1")
        self.assertEqual(var, None, "No match should return None")

        var = announce_parser.parse(th, "Row2 g2: g2_text")
        self.assertEqual(var, None, "No match should return None")

        var = announce_parser.parse(th, "Row3 g3: g3_text2")
        self.assertEqual(var, None, "No match should return None")

        var = announce_parser.parse(th, "Row4 g4: g4_text1")
        self.assertEqual(len(var), 2 + len(utils.get_default_variables()))
        self.assertEqual(var["torrentName"], "a_name", "Name did not match")
        self.assertEqual(var["$g3"], "g3_text1", "g3 did not match")
        self.assertEqual(var["$g4"], "g4_text1", "g2 did not match")

        var = announce_parser.parse(th, "Row4 g4: g4_text2")
        self.assertEqual(len(var), 3 + len(utils.get_default_variables()))
        self.assertEqual(var["torrentName"], "another_name", "Name did not match")
        self.assertEqual(var["$g2"], "g2_text", "g2 did not match")
        self.assertEqual(var["$g3"], "g3_text2", "g3 did not match")
        self.assertEqual(var["$g4"], "g4_text2", "g4 did not match")

    @mock.patch("time.time", mock.MagicMock(side_effect=[0, 15]))
    @multi_post_condition
    def test_multi_line_pattern_announcement_completed_just_in_time(self):
        th = TrackerHelper()
        th.config.insert_multi_regex(
            regex=r"Row1 name: (.*)", regex_groups=["torrentName"]
        )
        th.config.insert_multi_regex(regex=r"Row2 g2: (.*)", regex_groups=["$g2"])

        var = announce_parser.parse(th, "Row1 name: a_name")
        self.assertEqual(var, None, "No match should return None")

        var = announce_parser.parse(th, "Row2 g2: g2_text")
        self.assertEqual(len(var), 1 + len(utils.get_default_variables()))
        self.assertEqual(var["torrentName"], "a_name", "Name did not match")
        self.assertEqual(var["$g2"], "g2_text", "g2 did not match")

    # First two mock values are for time comparisons
    # Second two values are for logger
    @mock.patch("time.time", mock.MagicMock(side_effect=[0, 15.1, 0, 0]))
    @multi_post_condition
    def test_multi_line_pattern_discard_too_old(self):
        th = TrackerHelper()
        th.config.insert_multi_regex(
            regex=r"Row1 name: (.*)", regex_groups=["torrentName"]
        )
        th.config.insert_multi_regex(regex=r"Row2 g2: (.*)", regex_groups=["$g2"])

        var = announce_parser.parse(th, "Row1 name: a_name")
        self.assertEqual(var, None, "No match should return None")

        var = announce_parser.parse(th, "Row2 g2: g2_text")
        self.assertEqual(
            var, None, "Announcement should be discarded for being too old"
        )

    # Mock value: (insert1), (check1, insert2), (check1, log warning, check2)
    @mock.patch("time.time", mock.MagicMock(side_effect=[0, 10, 10, 16, 16, 16]))
    @multi_post_condition
    def test_multi_line_pattern_parallell_first_too_old(self):
        th = TrackerHelper()
        th.config.insert_multi_regex(
            regex=r"Row1 name: (.*)", regex_groups=["torrentName"]
        )
        th.config.insert_multi_regex(regex=r"Row2 g2: (.*)", regex_groups=["$g2"])

        var = announce_parser.parse(th, "Row1 name: a_name")
        self.assertEqual(var, None, "No match should return None")

        var = announce_parser.parse(th, "Row1 name: two_name")
        self.assertEqual(var, None, "No match should return None")

        var = announce_parser.parse(th, "Row2 g2: g2_text1")
        self.assertEqual(len(var), 1 + len(utils.get_default_variables()))
        self.assertEqual(var["torrentName"], "two_name", "Name did not match")
        self.assertEqual(var["$g2"], "g2_text1", "g2 did not match")

    @multi_post_condition
    def test_multi_non_capture_group(self):
        th = TrackerHelper()
        th.config.insert_multi_regex(
            regex=r"Row1 name: (.*)", regex_groups=["torrentName"]
        )
        th.config.insert_multi_regex(regex=r"Row2 g2:(?: (.*))?", regex_groups=["$g2"])

        var = announce_parser.parse(th, "Row1 name: a_name")
        self.assertEqual(var, None, "First row in multi should return None")

        var = announce_parser.parse(th, "Row2 g2:")
        self.assertEqual(len(var), len(utils.get_default_variables()))
        self.assertEqual(var["torrentName"], "a_name", "Name did not match")

        var = announce_parser.parse(th, "Row1 name: a_name")
        self.assertEqual(var, None, "First row in multi should return None")

        var = announce_parser.parse(th, "Row2 g2: a_group")
        self.assertEqual(len(var), 1 + len(utils.get_default_variables()))
        self.assertEqual(var["torrentName"], "a_name", "Name did not match")
        self.assertEqual(var["$g2"], "a_group", "g2 did not match")

    @multi_post_condition
    def test_multi_default_variables(self):
        th = TrackerHelper()
        th.config.insert_multi_regex(regex=r"Row1 g1: (.*)", regex_groups=["$g1"])
        th.config.insert_multi_regex(regex=r"Row2 g2: (.*)", regex_groups=["$g2"])
        th.config.insert_multi_regex(regex=r"Row3 g3: (.*)", regex_groups=["$g3"])

        var = announce_parser.parse(th, "Row1 g1: g1_text")
        self.assertEqual(var, None, "No match should return None")
        var = announce_parser.parse(th, "Row2 g2: g2_text")
        self.assertEqual(var, None, "Announcement is None")
        var = announce_parser.parse(th, "Row3 g3: g3_text")

        self.assertEqual(len(var), 3 + len(utils.get_default_variables()))
        self.assertEqual(var["$g1"], "g1_text", "g1 did not match")
        self.assertEqual(var["$g2"], "g2_text", "g2 did not match")
        self.assertEqual(var["$g3"], "g3_text", "g3 did not match")

        for key in utils.get_default_variables():
            self.assertEqual(var[key], "", "default value did not match")


if __name__ == "__main__":
    unittest.main()
