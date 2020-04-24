import unittest

from src import config


class ConfigTest(unittest.TestCase):
    def setUp(self):
        config.cfg = None

    def test_default_values(self):
        cfg = config.init("./tests/configs/default.cfg")
        self.assertNotEqual(cfg, None, "Config is None")

        self.assertFalse(config.login_required(), "Login required")
        self.assertTrue(config.login(None, None), "Login denied")

        section_names = [s.name for s in config.sections()]
        self.assertTrue("webui" in section_names, "webui in config sections")
        self.assertTrue("tracker1" in section_names, "tracker1 not in config sections")
        self.assertTrue("other" not in section_names, "tracker1 not in config sections")

        self.assertEqual(config.webui_host(), "0.0.0.0", "host is invalid")
        self.assertEqual(config.webui_port(), 3467, "host is invalid")

        self.assertEqual(config.cfg["webui.username"], None, "Invalid default value")
        self.assertEqual(config.cfg["webui.password"], None, "Invalid default value")

        self.assertEqual(config.cfg["log.to_file"], True, "Invalid default value")
        self.assertEqual(config.cfg["log.to_console"], True, "Invalid default value")

        self.assertEqual(config.cfg["sonarr.apikey"], None, "Invalid default value")
        self.assertEqual(
            config.cfg["sonarr.url"], "http://localhost:8989", "Invalid default value"
        )
        self.assertEqual(config.cfg["radarr.apikey"], None, "Invalid default value")
        self.assertEqual(
            config.cfg["radarr.url"], "http://localhost:7878", "Invalid default value"
        )
        self.assertEqual(config.cfg["lidarr.apikey"], None, "Invalid default value")
        self.assertEqual(
            config.cfg["lidarr.url"], "http://localhost:8686", "Invalid default value"
        )

        self.assertEqual(
            config.cfg["tracker1.irc_nickname"], "t1nick", "Invalid irc nickname"
        )
        self.assertEqual(
            config.cfg["tracker1.irc_server"], "t1url", "Invalid irc server"
        )
        self.assertEqual(config.cfg["tracker1.irc_port"], 1234, "Invalid irc port")
        self.assertEqual(
            config.cfg["tracker1.irc_channels"], "t1ch", "Invalid irc channels"
        )

        self.assertFalse(config.cfg["tracker1.irc_tls"], "Invalid default value")
        self.assertFalse(config.cfg["tracker1.irc_tls_verify"], "Invalid default value")
        self.assertEqual(
            config.cfg["tracker1.irc_ident_password"], None, "Invalid default value"
        )
        self.assertEqual(
            config.cfg["tracker1.irc_inviter"], None, "Invalid default value"
        )
        self.assertEqual(
            config.cfg["tracker1.irc_invite_cmd"], None, "Invalid default value"
        )
        self.assertEqual(
            config.cfg["tracker1.announce_delay"], 0, "Invalid default value"
        )
        self.assertFalse(config.cfg["tracker1.notify_sonarr"], "Invalid default value")
        self.assertFalse(config.cfg["tracker1.notify_radarr"], "Invalid default value")
        self.assertFalse(config.cfg["tracker1.notify_lidarr"], "Invalid default value")
        self.assertEqual(
            config.cfg["tracker1.category_sonarr"], None, "Invalid default value"
        )
        self.assertEqual(
            config.cfg["tracker1.category_radarr"], None, "Invalid default value"
        )
        self.assertEqual(
            config.cfg["tracker1.category_lidarr"], None, "Invalid default value"
        )

    def test_override_default(self):
        cfg = config.init("./tests/configs/override_default.cfg")
        self.assertNotEqual(cfg, None, "Config is None")

        self.assertTrue(config.login_required(), "Login required")
        self.assertFalse(config.login("something", "else"), "Login accepted")
        self.assertTrue(config.login("usern", "passw"), "Login denied")

        self.assertEqual(config.webui_host(), "webhost", "host is invalid")
        self.assertEqual(config.webui_port(), 456, "host is invalid")

        self.assertEqual(config.cfg["log.to_file"], False, "Invalid log to file")
        self.assertEqual(config.cfg["log.to_console"], False, "Invalid log to console")

        self.assertEqual(config.cfg["sonarr.apikey"], "sonapi", "Invalid sonarr api")
        self.assertEqual(config.cfg["sonarr.url"], "sonurl", "Invalid sonarr url")
        self.assertEqual(config.cfg["radarr.apikey"], "radapi", "Invalid radarr api")
        self.assertEqual(config.cfg["radarr.url"], "radurl", "Invalid default value")
        self.assertEqual(config.cfg["lidarr.apikey"], "lidapi", "Invalid lidarr api")
        self.assertEqual(config.cfg["lidarr.url"], "lidurl", "Invalid default value")

        self.assertEqual(
            config.cfg["tracker1.irc_nickname"], "t1nick", "Invalid irc nickname"
        )
        self.assertEqual(
            config.cfg["tracker1.irc_server"], "t1url", "Invalid irc server"
        )
        self.assertEqual(config.cfg["tracker1.irc_port"], 1234, "Invalid irc port")
        self.assertEqual(
            config.cfg["tracker1.irc_channels"], "t1ch", "Invalid irc channels"
        )

        self.assertTrue(config.cfg["tracker1.irc_tls"], "Invalid irc tls")
        self.assertTrue(config.cfg["tracker1.irc_tls_verify"], "Invalid irc tls verify")
        self.assertEqual(
            config.cfg["tracker1.irc_ident_password"],
            "t1ident",
            "Invalid ident password",
        )
        self.assertEqual(
            config.cfg["tracker1.irc_inviter"], "t1inver", "Invalid irc inviter"
        )
        self.assertEqual(
            config.cfg["tracker1.irc_invite_cmd"], "t1invcmd", "Invalid inviter command"
        )
        self.assertEqual(
            config.cfg["tracker1.announce_delay"], 9000, "Invalid announce delay"
        )
        self.assertTrue(config.cfg["tracker1.notify_sonarr"], "Invalid sonarr notify")
        self.assertTrue(config.cfg["tracker1.notify_radarr"], "Invalid radarr notify")
        self.assertTrue(config.cfg["tracker1.notify_lidarr"], "Invalid lidarr notify")
        self.assertEqual(
            config.cfg["tracker1.category_sonarr"], "soncat", "Invalid sonarr category"
        )
        self.assertEqual(
            config.cfg["tracker1.category_radarr"], "radcat", "Invalid radarr category"
        )
        self.assertEqual(
            config.cfg["tracker1.category_lidarr"], "lidcat", "Invalid lidarr category"
        )

        self.assertEqual(
            config.cfg["tracker1.phony"], "t1phony", "Invalid custom value"
        )

    def test_two_trackers(self):
        cfg = config.init("./tests/configs/two_trackers.cfg")
        self.assertNotEqual(cfg, None, "Config is None")
        self.assertTrue(config.validate_config(), "Configuration is invalid")

        self.assertTrue(config.login_required(), "Login required")
        self.assertTrue(config.login("auser", "apass"), "Login denied")

        self.assertEqual(config.webui_host(), "webhost2", "host is invalid")
        self.assertEqual(config.webui_port(), 4567, "host is invalid")

        self.assertEqual(config.cfg["lidarr.apikey"], "lidapi", "Invalid lidarr api")

        # Tracker 1
        self.assertEqual(
            config.cfg["tracker1.irc_nickname"], "t1nick", "Invalid irc nickname"
        )
        self.assertEqual(
            config.cfg["tracker1.irc_server"], "t1url", "Invalid irc server"
        )
        self.assertEqual(config.cfg["tracker1.irc_port"], 1234, "Invalid irc port")
        self.assertEqual(
            config.cfg["tracker1.irc_channels"], "t1ch", "Invalid irc channels"
        )

        self.assertEqual(
            config.cfg["tracker1.irc_inviter"], "t1inver", "Invalid irc inviter"
        )
        self.assertEqual(
            config.cfg["tracker1.irc_invite_cmd"], "t1invcmd", "Invalid inviter command"
        )

        # Tracker 2
        self.assertEqual(
            config.cfg["tracker2.irc_nickname"], "t2nick", "Invalid irc nickname"
        )
        self.assertEqual(
            config.cfg["tracker2.irc_server"], "t2url", "Invalid irc server"
        )
        self.assertEqual(config.cfg["tracker2.irc_port"], 9876, "Invalid irc port")
        self.assertEqual(
            config.cfg["tracker2.irc_channels"], "t2ch", "Invalid irc channels"
        )
        self.assertTrue(config.cfg["tracker2.irc_tls"], "Invalid irc tls")
        self.assertTrue(config.cfg["tracker2.irc_tls_verify"], "Invalid irc tls verify")
        self.assertEqual(
            config.cfg["tracker2.irc_ident_password"],
            "t2ident",
            "Invalid ident password",
        )

    def test_missing_backend(self):
        cfg = config.init("./tests/configs/missing_backend.cfg")
        self.assertNotEqual(cfg, None, "Config is None")
        self.assertFalse(config.validate_config(), "Configuration is valid")

    def test_missing_password(self):
        cfg = config.init("./tests/configs/missing_password.cfg")
        self.assertNotEqual(cfg, None, "Config is None")
        self.assertFalse(config.validate_config(), "Configuration is valid")

    def test_missing_username(self):
        cfg = config.init("./tests/configs/missing_username.cfg")
        self.assertNotEqual(cfg, None, "Config is None")
        self.assertFalse(config.validate_config(), "Configuration is valid")

    def test_missing_nickname(self):
        cfg = config.init("./tests/configs/missing_nickname.cfg")
        self.assertNotEqual(cfg, None, "Config is None")
        self.assertFalse(config.validate_config(), "Configuration is valid")

    def test_missing_server(self):
        cfg = config.init("./tests/configs/missing_server.cfg")
        self.assertNotEqual(cfg, None, "Config is None")
        self.assertFalse(config.validate_config(), "Configuration is valid")

    def test_missing_port(self):
        cfg = config.init("./tests/configs/missing_port.cfg")
        self.assertNotEqual(cfg, None, "Config is None")
        self.assertFalse(config.validate_config(), "Configuration is valid")

    def test_missing_channels(self):
        cfg = config.init("./tests/configs/missing_channels.cfg")
        self.assertNotEqual(cfg, None, "Config is None")
        self.assertFalse(config.validate_config(), "Configuration is valid")

    def test_missing_inviter(self):
        cfg = config.init("./tests/configs/missing_inviter.cfg")
        self.assertNotEqual(cfg, None, "Config is None")
        self.assertFalse(config.validate_config(), "Configuration is valid")

    def test_missing_invite_cmd(self):
        cfg = config.init("./tests/configs/missing_invite_cmd.cfg")
        self.assertNotEqual(cfg, None, "Config is None")
        self.assertFalse(config.validate_config(), "Configuration is valid")

    def test_both_sonarr(self):
        cfg = config.init("./tests/configs/both_sonarr.cfg")
        self.assertNotEqual(cfg, None, "Config is None")
        self.assertFalse(config.validate_config(), "Configuration is valid")

    def test_both_radarr(self):
        cfg = config.init("./tests/configs/both_radarr.cfg")
        self.assertNotEqual(cfg, None, "Config is None")
        self.assertFalse(config.validate_config(), "Configuration is valid")

    def test_both_lidarr(self):
        cfg = config.init("./tests/configs/both_lidarr.cfg")
        self.assertNotEqual(cfg, None, "Config is None")
        self.assertFalse(config.validate_config(), "Configuration is valid")

    def test_cannot_notify_sonarr(self):
        cfg = config.init("./tests/configs/cannot_notify_sonarr.cfg")
        self.assertNotEqual(cfg, None, "Config is None")
        self.assertFalse(config.validate_config(), "Configuration is valid")

    def test_cannot_notify_radarr(self):
        cfg = config.init("./tests/configs/cannot_notify_radarr.cfg")
        self.assertNotEqual(cfg, None, "Config is None")
        self.assertFalse(config.validate_config(), "Configuration is valid")

    def test_cannot_notify_lidarr(self):
        cfg = config.init("./tests/configs/cannot_notify_lidarr.cfg")
        self.assertNotEqual(cfg, None, "Config is None")
        self.assertFalse(config.validate_config(), "Configuration is valid")

    def test_empty_value(self):
        cfg = config.init("./tests/configs/empty_value.cfg")
        self.assertNotEqual(cfg, None, "Config is None")
        self.assertFalse(config.validate_config(), "Configuration is valid")


if __name__ == "__main__":
    unittest.main()
