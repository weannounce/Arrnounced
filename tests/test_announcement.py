import unittest
from datetime import datetime

from arrnounced import announcement, tracker, tracker_xml_config
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

#    Http,


class HelperXml:
    def __init__(self, data):
        self.tag = data[0]
        self.attrib = {data[1]: data[2]}


def get_time_passed(announce_time):
    return (datetime.now() - announce_time).total_seconds()


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
        self._user_tracker = {}
        self._user_tracker["notify_backends"] = None
        self._user_tracker["category"] = {}
        self._user_tracker["torrent_https"] = False
        self._user_tracker["settings"] = {}

        self._xml_config = tracker_xml_config.TrackerXmlConfig()
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

    def insert_extract(self, srcvar, regex, regex_groups, optional):
        self._xml_config.line_matched.append(
            Extract(srcvar, regex, regex_groups, optional)
        )

    def __setitem__(self, key, value):
        self._user_tracker["settings"][key] = value


class AnnouncementTest(unittest.TestCase):
    def test_no_torrent_name(self):
        th = TrackerHelper()
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

        th.config["tc1"] = "config_text1%"
        th.config["tc2"] = "config_text2%"

        th.config.insert_var("first_var", elements1)
        th.config.insert_var("torrentUrl", elements2)
        th.config.insert_var("category", elements3)
        variables = {"var1": "testvar1&", "var2": "testvar2&"}
        var = announcement.create_announcement(th, variables)
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
            variables["category"],
            "a_category",
            "Variable not correct",
        )

    def test_no_torrent_url(self):
        th = TrackerHelper()
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

        th.config["tc1"] = "config_text1%"
        th.config["tc2"] = "config_text2%"

        th.config.insert_var("torrentName", elements1)
        th.config.insert_var("second_var", elements2)
        th.config.insert_var("category", elements3)
        variables = {"var1": "testvar1&", "var2": "testvar2&"}
        var = announcement.create_announcement(th, variables)
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
            variables["category"],
            "a_category",
            "Variable not correct",
        )

    def test_no_torrent_ssl_url(self):
        th = TrackerHelper()
        elements1 = [
            HelperXml(x)
            for x in [
                ["string", "value", "test_string"],
                ["var", "name", "var1"],
                ["varenc", "name", "var2"],
            ]
        ]

        th.config["torrent_https"] = True
        th.config.insert_var("torrentName", elements1)

        variables = {"var1": "testvar1&", "var2": "testvar2&"}
        var = announcement.create_announcement(th, variables)
        self.assertEqual(var, None, "No match should return None")
        self.assertEqual(
            variables["torrentName"],
            "test_stringtestvar1&testvar2%26",
            "Variable not correct",
        )

    def test_no_torrent_ssl_url_created_from_http(self):
        th = TrackerHelper()
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
                ["string", "value", "http://"],
                ["var", "name", "var2"],
                ["string", "value", "-"],
            ]
        ]

        th.config["torrent_https"] = True
        th.config.insert_var("torrentName", elements1)
        th.config.insert_var("torrentUrl", elements2)

        variables = {"var1": "testvar1&", "var2": "testvar2&"}
        var = announcement.create_announcement(th, variables)
        self.assertNotEqual(var, None, "No match should return None")
        self.assertEqual(
            variables["torrentName"],
            "test_stringtestvar1&testvar2%26",
            "Variable not correct",
        )
        self.assertEqual(
            variables["torrentUrl"],
            "http://testvar2&-",
            "Variable not correct",
        )
        self.assertEqual(
            variables["torrentSslUrl"],
            "https://testvar2&-",
            "Variable not correct",
        )

    def test_no_torrent_ssl_url_created_from_https(self):
        th = TrackerHelper()
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
                ["string", "value", "https://"],
                ["var", "name", "var2"],
                ["string", "value", "-"],
            ]
        ]

        th.config["torrent_https"] = True
        th.config.insert_var("torrentName", elements1)
        th.config.insert_var("torrentUrl", elements2)

        variables = {"var1": "testvar1&", "var2": "testvar2&"}
        var = announcement.create_announcement(th, variables)
        self.assertNotEqual(var, None, "No match should return None")
        self.assertEqual(
            variables["torrentName"],
            "test_stringtestvar1&testvar2%26",
            "Variable not correct",
        )
        self.assertEqual(
            variables["torrentUrl"],
            "https://testvar2&-",
            "Variable not correct",
        )
        self.assertEqual(
            variables["torrentSslUrl"],
            "https://testvar2&-",
            "Variable not correct",
        )

    def test_var_not_valid(self):
        th = TrackerHelper()
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

        th.config["tc1"] = "config_text1%"
        th.config["tc2"] = "config_text2%"

        th.config.insert_var("first_var", elements1)
        th.config.insert_var("second_var", elements2)
        variables = {"var1": "testvar1&", "var2": "testvar2&"}
        var = announcement.create_announcement(th, variables)
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
        th = TrackerHelper()
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

        th.config["tc1"] = "config_text1%"
        th.config["tc2"] = "config_text2%"

        th.config.insert_var("torrentName", elements1)
        th.config.insert_var("torrentUrl", elements2)
        variables = {"var1": "testvar1&", "var2": "testvar2&"}
        announce = announcement.create_announcement(th, variables)
        self.assertNotEqual(announce, None, "Should return match")
        self.assertEqual(
            announce.title,
            "test_stringtestvar1&config_text1%25",
            "Title does not match",
        )
        self.assertEqual(
            announce.torrent_url, "testvar2& config_text2%25", "URL does not match"
        )
        self.assertEqual(announce.category, None, "Category should be None")
        self.assertEqual(announce.indexer, "trackername", "Wrong indexer")
        self.assertTrue(get_time_passed(announce.date) < 0.005, "Date is wrong")

    def test_extract_not_valid(self):
        th = TrackerHelper()
        variables = {"mysrc": "group1  -  group2", "anothersrc": " group3  :  group4"}

        th.config.insert_extract("mysrc", "^(.*) - (.*)$", ["g1", "g2"], False)
        th.config.insert_extract("anothersrc", "^(.*) : (.*)$", ["g3", "g4"], False)
        th.config.insert_extract("missing", ">(.*)$", ["g5"], True)
        announce = announcement.create_announcement(th, variables)
        self.assertEqual(announce, None, "No match should return None")
        self.assertEqual(
            variables["g1"],
            "group1",
            "Variable not correct",
        )
        self.assertEqual(
            variables["g2"],
            "group2",
            "Variable not correct",
        )
        self.assertEqual(
            variables["g3"],
            "group3",
            "Variable not correct",
        )
        self.assertEqual(
            variables["g4"],
            "group4",
            "Variable not correct",
        )
        self.assertTrue(
            "g5" not in variables,
            "Group should be missing",
        )

    def test_extract_valid(self):
        th = TrackerHelper()
        variables = {
            "mysrc": "a title  -  group1",
            "anothersrc": " an url  :  group2",
            "present": "> a_category",
        }

        th.config.insert_extract("mysrc", "^(.*) - (.*)$", ["torrentName", "g1"], False)
        th.config.insert_extract(
            "anothersrc", "^(.*) : (.*)$", ["torrentUrl", "g2"], False
        )
        th.config.insert_extract("present", ">(.*)$", ["category"], True)
        announce = announcement.create_announcement(th, variables)
        self.assertNotEqual(announce, None, "Should return match")
        self.assertEqual(
            announce.title,
            "a title",
            "Title does not match",
        )
        self.assertEqual(announce.torrent_url, "an url", "URL does not match")
        self.assertEqual(announce.category, "a_category", "Category should be None")
        self.assertEqual(announce.indexer, "trackername", "Wrong indexer")
        self.assertTrue(get_time_passed(announce.date) < 0.005, "Date is wrong")
        self.assertEqual(
            variables["g1"],
            "group1",
            "Variable not correct",
        )
        self.assertEqual(
            variables["g2"],
            "group2",
            "Variable not correct",
        )

    def test_extract_missing_non_optional(self):
        th = TrackerHelper()
        variables = {
            "nomatch": "something else",
        }

        th.config.insert_extract(
            "nomatch", "^(.*) - (.*)$", ["torrentName", "g1"], False
        )
        announce = announcement.create_announcement(th, variables)
        self.assertEqual(announce, None, "No match should return None")
        self.assertTrue(
            "torrentName" not in variables,
            "Group should be missing",
        )
        self.assertTrue(
            "g1" not in variables,
            "Group should be missing",
        )

    def test_extract_missing_non_capture_group(self):
        th = TrackerHelper()
        variables = {
            "srcvar": " a name  -   ",
        }

        th.config.insert_extract(
            "srcvar", "^(.*) - (?:(.*))$", ["torrentName", "g1"], False
        )
        announce = announcement.create_announcement(th, variables)
        self.assertEqual(announce, None, "No match should return None")
        self.assertEqual(
            variables["torrentName"],
            "a name",
        )
        self.assertTrue(
            "g1" not in variables,
            "Group should be missing",
        )

    def test_extract_process_string(self):
        extract = Extract(None, "^(.*) - (.*)$", ["torrentName", "g1"], False)
        variables = extract.process_string("not matching")
        self.assertEqual(variables, None, "No match should return None")

        variables = extract.process_string("one title  - groupone")
        self.assertEqual(
            variables["torrentName"],
            "one title",
        )
        self.assertEqual(
            variables["g1"],
            "groupone",
        )

    def test_extractone_no_match(self):
        tc_helper = TrackerConfigHelper()

        extracts = []
        extracts.append(Extract("src", "^(.*) - (.*)$", ["torrentName", "g1"], False))
        extracts.append(Extract("src", "^(.*) : (.*)$", ["torrentName", "g1"], False))
        extractone = ExtractOne(extracts)

        variables = {
            "src": "something / someother",
        }

        extractone.process(tc_helper, variables)
        self.assertTrue("torrentName" not in variables)
        self.assertTrue("g1" not in variables)

    def test_extractone_match_first(self):
        tc_helper = TrackerConfigHelper()

        extracts = []
        extracts.append(
            Extract("src", "^(.*) - (.*) - (.*)$", ["torrentName", "g1", "g2"], False)
        )
        extracts.append(Extract("src", "^(.*) : (.*)$", ["torrentName", "g1"], False))
        extractone = ExtractOne(extracts)

        variables = {
            "src": "something - else -  or",
        }

        extractone.process(tc_helper, variables)
        self.assertEqual(variables["torrentName"], "something")
        self.assertEqual(variables["g1"], "else")
        self.assertEqual(variables["g2"], "or")

    def test_extractone_match_second(self):
        tc_helper = TrackerConfigHelper()

        extracts = []
        extracts.append(
            Extract("src", "^(.*) - (.*) - (.*)$", ["torrentName", "g1", "g2"], False)
        )
        extracts.append(Extract("src", "^(.*) : (.*)$", ["torrentName", "g1"], False))
        extractone = ExtractOne(extracts)

        variables = {
            "src": "some :  stuff",
        }

        extractone.process(tc_helper, variables)
        self.assertEqual(variables["torrentName"], "some")
        self.assertEqual(variables["g1"], "stuff")
        self.assertTrue("g2" not in variables)

    def test_extracttags_no_match(self):
        tc_helper = TrackerConfigHelper()

        setvarifs = []
        setvarifs.append(ExtractTags.SetVarIf("name", "^(some|tags)$", None, None))
        setvarifs.append(ExtractTags.SetVarIf("name", None, "avalue", "newvalue"))
        extracttags = ExtractTags("srcvar", "-", setvarifs)

        variables = {
            "srcvar": "something - someother",
        }
        extracttags.process(tc_helper, variables)
        self.assertTrue("name" not in variables)

    def test_extracttags_no_srcvar(self):
        tc_helper = TrackerConfigHelper()

        setvarifs = []
        setvarifs.append(ExtractTags.SetVarIf("name", "^(some|tags)$", None, None))
        setvarifs.append(ExtractTags.SetVarIf("name", None, "avalue", "newvalue"))
        extracttags = ExtractTags("srcvar", "-", setvarifs)

        variables = {}

        extracttags.process(tc_helper, variables)
        self.assertTrue("name" not in variables)

    def test_extracttags_empty_tag(self):
        tc_helper = TrackerConfigHelper()

        setvarifs = []
        setvarifs.append(ExtractTags.SetVarIf("name", "^(some|tags)$", None, None))
        setvarifs.append(ExtractTags.SetVarIf("name", None, "avalue", "newvalue"))
        extracttags = ExtractTags("srcvar", "-", setvarifs)

        variables = {
            "srcvar": "something - ",
        }

        extracttags.process(tc_helper, variables)
        self.assertTrue("name" not in variables)

    def test_extracttags_match_only_regex(self):
        tc_helper = TrackerConfigHelper()

        setvarifs = []
        setvarifs.append(ExtractTags.SetVarIf("name", "^(some|tags)$", None, None))
        setvarifs.append(ExtractTags.SetVarIf("name", None, "Name", "newvalue"))
        extracttags = ExtractTags("srcvar", "-", setvarifs)

        variables = {
            "srcvar": "some - oldvalue",
        }
        extracttags.process(tc_helper, variables)
        self.assertEqual(variables["name"], "some")

    def test_extracttags_match_only_newvalue(self):
        tc_helper = TrackerConfigHelper()

        setvarifs = []
        setvarifs.append(ExtractTags.SetVarIf("name", "^(some|tags)$", None, None))
        setvarifs.append(ExtractTags.SetVarIf("name", None, "OlDvAlUe", "newvalue"))
        extracttags = ExtractTags("srcvar", "-", setvarifs)

        variables = {
            "srcvar": "someother - oldvaluE",
        }

        extracttags.process(tc_helper, variables)
        self.assertEqual(variables["name"], "newvalue")

    def test_extracttags_match_regex_newvalue(self):
        tc_helper = TrackerConfigHelper()

        setvarifs = []
        setvarifs.append(ExtractTags.SetVarIf("name", "^(some|tags)$", None, None))
        setvarifs.append(ExtractTags.SetVarIf("two", None, "avaluE", "True"))
        extracttags = ExtractTags("srcvar", "-", setvarifs)

        variables = {
            "srcvar": "tags - Avalue",
        }

        extracttags.process(tc_helper, variables)
        self.assertEqual(variables["name"], "tags")
        self.assertEqual(variables["two"], "True")

    def test_extracttags_match_two_each(self):
        tc_helper = TrackerConfigHelper()

        setvarifs = []
        setvarifs.append(ExtractTags.SetVarIf("name1", "^(n1|m1)$", None, None))
        setvarifs.append(ExtractTags.SetVarIf("name2", "^(n2|m2)$", None, None))
        setvarifs.append(ExtractTags.SetVarIf("name3", None, "Value1", "True"))
        setvarifs.append(ExtractTags.SetVarIf("name4", None, "Value2", "False"))
        extracttags = ExtractTags("srcvar", "-|/|:", setvarifs)

        variables = {
            "srcvar": "n1 : valuE2 / m2 - vAlUe1",
        }

        extracttags.process(tc_helper, variables)
        self.assertEqual(variables["name1"], "n1")
        self.assertEqual(variables["name2"], "m2")
        self.assertEqual(variables["name3"], "True")
        self.assertEqual(variables["name4"], "False")

    def test_extracttags_regex_part_of_tag(self):
        tc_helper = TrackerConfigHelper()

        setvarifs = []
        setvarifs.append(ExtractTags.SetVarIf("name1", "stuff$", None, None))
        extracttags = ExtractTags("srcvar", ":", setvarifs)

        variables = {
            "srcvar": "some stuff : other tings",
        }

        extracttags.process(tc_helper, variables)
        self.assertEqual(variables["name1"], "some stuff")

    def test_extracttags_regex_new_value(self):
        tc_helper = TrackerConfigHelper()

        setvarifs = []
        setvarifs.append(ExtractTags.SetVarIf("name1", "^asdf$", None, "eurT"))
        extracttags = ExtractTags("srcvar", ":", setvarifs)

        variables = {
            "srcvar": "asdf : other tings",
        }

        extracttags.process(tc_helper, variables)
        self.assertEqual(variables["name1"], "eurT")

    def test_varreplace_missing_srcvar(self):
        tc_helper = TrackerConfigHelper()

        varreplace = VarReplace("name", "missing", "[_]", "asdf")

        variables = {
            "srcvar": "asdf : other_tings",
        }

        varreplace.process(tc_helper, variables)
        self.assertTrue("name" not in variables)

    def test_varreplace_replace_nothing(self):
        tc_helper = TrackerConfigHelper()

        varreplace = VarReplace("name", "srcvar", "[_]", "asdf")

        variables = {
            "srcvar": "asdf : other tings",
        }

        varreplace.process(tc_helper, variables)
        self.assertEqual(variables["name"], "asdf : other tings")

    def test_varreplace_replace_one(self):
        tc_helper = TrackerConfigHelper()

        varreplace = VarReplace("name", "srcvar", "[_]", "asdf")

        variables = {
            "srcvar": "asdf : other_tings",
        }

        varreplace.process(tc_helper, variables)
        self.assertEqual(variables["name"], "asdf : otherasdftings")

    def test_varreplace_replace_many(self):
        tc_helper = TrackerConfigHelper()

        varreplace = VarReplace("name", "srcvar", "[_:/]", "db")

        variables = {
            "srcvar": "asdf : other_tings/nostuff",
        }

        varreplace.process(tc_helper, variables)
        self.assertEqual(variables["name"], "asdf db otherdbtingsdbnostuff")

    def test_setregex_missing_srcvar(self):
        tc_helper = TrackerConfigHelper()

        setregex = SetRegex("missing", "b0[:/]", "new_variable", "new value")

        variables = {
            "srcvar": "stuff in here",
        }

        setregex.process(tc_helper, variables)
        self.assertTrue("new_variable" not in variables)

    def test_setregex_no_match(self):
        tc_helper = TrackerConfigHelper()

        setregex = SetRegex("srcvar", "b0[:/]", "new_variable", "new value")

        variables = {
            "srcvar": "stuff in here",
        }

        setregex.process(tc_helper, variables)
        self.assertTrue("new_variable" not in variables)

    def test_setregex_match(self):
        tc_helper = TrackerConfigHelper()

        setregex = SetRegex("srcvar", "b0[:/]", "new_variable", "new value")

        variables = {
            "srcvar": "stuff in b0:here",
        }

        setregex.process(tc_helper, variables)
        self.assertEqual(variables["new_variable"], "new value")

    def test_if_missing_srcvar(self):
        tc_helper = TrackerConfigHelper()

        matches = []
        matches.append(SetRegex("srcvar2", "0t.er", "new_variable", "a new value"))
        iff = If("missing", "st[Uu]ff", matches)

        variables = {
            "srcvar": "stUff in here",
            "srcvar2": "0tter stUff in here",
        }

        iff.process(tc_helper, variables)
        self.assertTrue("new_variable" not in variables)

    def test_if_condition_not_met(self):
        tc_helper = TrackerConfigHelper()

        matches = []
        matches.append(SetRegex("srcvar2", "0t.er", "new_variable", "a new value"))
        iff = If("srcvar", "no stuff", matches)

        variables = {
            "srcvar": "stUff in here",
            "srcvar2": "0tter stUff in here",
        }

        iff.process(tc_helper, variables)
        self.assertTrue("new_variable" not in variables)

    def test_if_condition_met(self):
        tc_helper = TrackerConfigHelper()

        matches = []
        matches.append(SetRegex("srcvar2", "0t.er", "new_variable", "a new value"))
        iff = If("srcvar", "st[Uu]ff", matches)

        variables = {
            "srcvar": "stUff in here",
            "srcvar2": "0tter stUff in here",
        }

        iff.process(tc_helper, variables)
        self.assertEqual(variables["new_variable"], "a new value")

    def test_if_process_all(self):
        tc_helper = TrackerConfigHelper()

        matches = []
        matches.append(
            Var(
                "first_var",
                [
                    HelperXml(x)
                    for x in [
                        ["string", "value", "var stuff - here : "],
                        ["var", "name", "srcvar"],
                    ]
                ],
            )
        )
        matches.append(
            Extract("first_var", "(.*) - (.*) :", ["ext_g1", "ext_g2"], False)
        )

        matches.append(
            ExtractOne(
                [
                    Extract("ext_g1", "(.*) stuff", ["extone_g1"], False),
                    Extract("ext_g2", "here", ["extone_g2"], False),
                ]
            )
        )

        matches.append(
            ExtractTags(
                "first_var",
                "[:-]",
                [ExtractTags.SetVarIf("extract_tags_var", "^(some|here)$", None, None)],
            )
        )

        matches.append(VarReplace("varreplace_var", "first_var", "[_:/-]", "<-->"))

        matches.append(
            SetRegex("varreplace_var", "> here <", "setregex_var", "setregex_value")
        )

        matches.append(
            If(
                "setregex_var",
                "_value",
                [
                    SetRegex(
                        "extract_tags_var", "here", "setregex_var2", "setregex_value2"
                    )
                ],
            )
        )

        iff = If("srcvar", "st[Uu]ff", matches)

        variables = {
            "srcvar": "stUff in here",
            "srcvar2": "0tter stUff in here",
        }

        iff.process(tc_helper, variables)
        self.assertEqual(variables["first_var"], "var stuff - here : stUff in here")
        self.assertEqual(variables["ext_g1"], "var stuff")
        self.assertEqual(variables["ext_g2"], "here")
        self.assertEqual(variables["extone_g1"], "var")
        self.assertTrue("extone_g2" not in variables)
        self.assertEqual(variables["extract_tags_var"], "here")
        self.assertEqual(
            variables["varreplace_var"], "var stuff <--> here <--> stUff in here"
        )
        self.assertEqual(variables["setregex_var"], "setregex_value")
        self.assertEqual(variables["setregex_var2"], "setregex_value2")

    def test_http_does_nothing(self):
        tc_helper = TrackerConfigHelper()

        matches = []
        matches.append(SetRegex("srcvar2", "0t.er", "new_variable", "a new value"))
        http = Http()

        variables = {}

        http.process(tc_helper, variables)
        self.assertEqual(len(variables), 0)


if __name__ == "__main__":
    unittest.main()
