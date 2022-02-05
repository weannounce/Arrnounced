import unittest

from arrnounced import config


class ConfigTest(unittest.TestCase):
    def test_default_values(self):
        cfg = config.init("./tests/configs/default.toml")
        self.assertNotEqual(cfg, None, "Config is None")

        self.assertFalse(cfg.login_required, "Login required")
        self.assertTrue(cfg.login(None, None), "Login denied")

        self.assertEqual(
            cfg.webui_host,
            "0.0.0.0",  # nosec B104: bind all interfaces
            "host is invalid",
        )
        self.assertEqual(cfg.webui_port, 3467, "host is invalid")
        self.assertEqual(
            cfg.toml["webui"].get("username"), None, "Invalid default value"
        )
        self.assertEqual(
            cfg.toml["webui"].get("password"), None, "Invalid default value"
        )
        self.assertEqual(cfg.toml["webui"]["shutdown"], False, "Invalid default value")

        self.assertEqual(cfg.log_to_file, True, "Invalid default value")
        self.assertEqual(cfg.log_to_console, True, "Invalid default value")

        self.assertEqual(cfg.db_purge_days, 365, "Invalid default value")

        sonarr = next(b for b in cfg.backends if b.name == "test_sonarr")
        self.assertEqual(sonarr.type, "sonarr", "Invalid default value")
        self.assertEqual(sonarr.backend.get("apikey"), None, "Invalid default value")
        self.assertEqual(
            sonarr.url,
            "http://localhost:8989",
            "Invalid default value",
        )
        radarr = next(b for b in cfg.backends if b.name == "test_radarr")
        self.assertEqual(radarr.type, "radarr", "Invalid default value")
        self.assertEqual(radarr.backend.get("apikey"), None, "Invalid default value")
        self.assertEqual(
            radarr.url,
            "http://localhost:7878",
            "Invalid default value",
        )
        lidarr = next(b for b in cfg.backends if b.name == "test_lidarr")
        self.assertEqual(lidarr.type, "lidarr", "Invalid default value")
        self.assertEqual(lidarr.backend.get("apikey"), None, "Invalid default value")
        self.assertEqual(
            lidarr.url,
            "http://localhost:8686",
            "Invalid default value",
        )

        tracker1 = next(t.tracker for t in cfg.trackers if t.type == "tracker1")
        self.assertEqual(len(cfg.trackers), 1)
        self.assertEqual(
            tracker1["irc_nickname"],
            "t1nick",
            "Invalid irc nickname",
        )
        self.assertEqual(tracker1["irc_server"], "t1url", "Invalid irc server")
        self.assertEqual(tracker1["irc_port"], 1234, "Invalid irc port")
        self.assertEqual(tracker1["irc_channels"], "t1ch", "Invalid irc channels")

        self.assertFalse(tracker1["irc_tls"], "Invalid default value")
        self.assertFalse(tracker1["irc_tls_verify"], "Invalid default value")
        self.assertEqual(
            tracker1.get("irc_ident_password"),
            None,
            "Invalid default value",
        )
        self.assertEqual(
            tracker1.get("irc_inviter"),
            None,
            "Invalid default value",
        )
        self.assertEqual(
            tracker1.get("irc_invite_cmd"),
            None,
            "Invalid default value",
        )
        self.assertEqual(tracker1["torrent_https"], False, "Invalid default value")
        self.assertEqual(tracker1["announce_delay"], 0, "Invalid default value")
        self.assertEqual(tracker1.get("notify_backends"), None, "Invalid default value")
        self.assertEqual(len(tracker1["category"]), 0)

    def test_override_default(self):
        cfg = config.init("./tests/configs/override_default.toml")
        self.assertNotEqual(cfg, None, "Config is None")

        self.assertTrue(cfg.login_required, "Login required")
        self.assertFalse(cfg.login("something", "else"), "Login accepted")
        self.assertTrue(cfg.login("usern", "passw"), "Login denied")

        self.assertEqual(cfg.webui_host, "webhost", "host is invalid")
        self.assertEqual(cfg.webui_port, 456, "host is invalid")

        self.assertEqual(cfg.db_purge_days, 1, "Invalid db purge value")

        self.assertEqual(cfg.log_to_file, False, "Invalid log to file")
        self.assertEqual(cfg.log_to_console, False, "Invalid log to console")

        sonarr = next(b for b in cfg.backends if b.name == "test_sonarr")
        self.assertEqual(sonarr.apikey, "sonapi", "Invalid sonarr api")
        self.assertEqual(
            sonarr.url,
            "sonurl",
            "Invalid default value",
        )
        radarr = next(b for b in cfg.backends if b.name == "test_radarr")
        self.assertEqual(radarr.apikey, "radapi", "Invalid radarr api")
        self.assertEqual(
            radarr.url,
            "radurl",
            "Invalid default value",
        )
        lidarr = next(b for b in cfg.backends if b.name == "test_lidarr")
        self.assertEqual(lidarr.apikey, "lidapi", "Invalid lidarr api")
        self.assertEqual(
            lidarr.url,
            "lidurl",
            "Invalid default value",
        )

        tracker1 = next(t.tracker for t in cfg.trackers if t.type == "tracker1")
        self.assertEqual(
            tracker1["irc_nickname"],
            "t1nick",
            "Invalid irc nickname",
        )
        self.assertEqual(tracker1["irc_server"], "t1url", "Invalid irc server")
        self.assertEqual(tracker1["irc_port"], 1234, "Invalid irc port")
        self.assertEqual(tracker1["irc_channels"], "t1ch", "Invalid irc channels")

        self.assertTrue(tracker1["irc_tls"], "Invalid irc tls")
        self.assertTrue(tracker1["irc_tls_verify"], "Invalid irc tls verify")
        self.assertEqual(
            tracker1["irc_ident_password"],
            "t1ident",
            "Invalid ident password",
        )
        self.assertEqual(tracker1["irc_inviter"], "t1inver", "Invalid irc inviter")
        self.assertEqual(
            tracker1["irc_invite_cmd"],
            "t1invcmd",
            "Invalid inviter command",
        )
        self.assertEqual(tracker1["torrent_https"], True)
        self.assertEqual(
            tracker1["announce_delay"],
            9000,
            "Invalid announce delay",
        )
        always_notify = [b.strip() for b in tracker1["notify_backends"].split(",")]
        self.assertTrue("test_sonarr" in always_notify, "Invalid sonarr notify")
        self.assertTrue("test_radarr" in always_notify, "Invalid radarr notify")
        self.assertTrue("test_lidarr" in always_notify, "Invalid lidarr notify")
        self.assertEqual(
            tracker1["category"]["test_sonarr"],
            "soncat",
            "Invalid sonarr category",
        )
        self.assertEqual(
            tracker1["category"]["test_radarr"],
            "radcat",
            "Invalid radarr category",
        )
        self.assertEqual(
            tracker1["category"]["test_lidarr"],
            "lidcat",
            "Invalid lidarr category",
        )

        self.assertEqual(
            tracker1["settings"]["phony"], "t1phony", "Invalid custom value"
        )

    def test_two_trackers(self):
        cfg = config.init("./tests/configs/two_trackers.toml")
        self.assertNotEqual(cfg, None, "Config is None")
        self.assertTrue(cfg.validate_config(), "Configuration is invalid")

        self.assertTrue(cfg.login_required, "Login required")
        self.assertTrue(cfg.login("auser", "apass"), "Login denied")

        self.assertEqual(cfg.webui_host, "webhost2", "host is invalid")
        self.assertEqual(cfg.webui_port, 4567, "host is invalid")

        lidarr = next(b for b in cfg.backends if b.name == "mlidarr")
        self.assertEqual(lidarr.apikey, "lidapi", "Invalid lidarr api")

        self.assertEqual(len(cfg.trackers), 2)
        # Tracker 1
        tracker1 = next(t.tracker for t in cfg.trackers if t.type == "tracker1")
        self.assertEqual(
            tracker1["irc_nickname"],
            "t1nick",
            "Invalid irc nickname",
        )
        self.assertEqual(tracker1["irc_server"], "t1url", "Invalid irc server")
        self.assertEqual(tracker1["irc_port"], 1234, "Invalid irc port")
        self.assertEqual(tracker1["irc_channels"], "t1ch", "Invalid irc channels")

        self.assertEqual(tracker1["irc_inviter"], "t1inver", "Invalid irc inviter")
        self.assertEqual(
            tracker1["irc_invite_cmd"],
            "t1invcmd",
            "Invalid inviter command",
        )

        # Tracker 2
        tracker2 = next(t.tracker for t in cfg.trackers if t.type == "tracker2.dottest")
        self.assertEqual(
            cfg.toml.get("tracker2"),
            None,
            "tracker2 should be None",
        )
        self.assertEqual(
            tracker2["irc_nickname"],
            "t2nick",
            "Invalid irc nickname",
        )
        self.assertEqual(
            tracker2["irc_server"],
            "t2url",
            "Invalid irc server",
        )
        self.assertEqual(tracker2["irc_port"], 9876, "Invalid irc port")
        self.assertEqual(
            tracker2["irc_channels"],
            "t2ch",
            "Invalid irc channels",
        )
        self.assertTrue(tracker2["irc_tls"], "Invalid irc tls")
        self.assertTrue(tracker2["irc_tls_verify"], "Invalid irc tls verify")
        self.assertEqual(
            tracker2["irc_ident_password"],
            "t2ident",
            "Invalid ident password",
        )

    def test_settings(self):
        cfg = config.init("./tests/configs/settings.toml")
        self.assertNotEqual(cfg, None, "Config is None")
        self.assertTrue(cfg.validate_config(), "Configuration is invalid")

        # Tracker 1
        tracker1 = next(t for t in cfg.trackers if t.type == "tracker1")
        self.assertEqual(len(tracker1.settings), 2)
        self.assertEqual(tracker1.settings["fixed1"], "f1value")
        self.assertEqual(tracker1.settings["fixed2"], "f2value")

    def test_missing_backend(self):
        cfg = config.init("./tests/configs/missing_backend.toml")
        self.assertNotEqual(cfg, None, "Config is None")
        self.assertFalse(cfg.validate_config(), "Configuration is valid")

    def test_missing_password(self):
        cfg = config.init("./tests/configs/missing_password.toml")
        self.assertNotEqual(cfg, None, "Config is None")
        self.assertFalse(cfg.validate_config(), "Configuration is valid")

    def test_missing_username(self):
        cfg = config.init("./tests/configs/missing_username.toml")
        self.assertNotEqual(cfg, None, "Config is None")
        self.assertFalse(cfg.validate_config(), "Configuration is valid")

    def test_missing_nickname(self):
        cfg = config.init("./tests/configs/missing_nickname.toml")
        self.assertNotEqual(cfg, None, "Config is None")
        self.assertFalse(cfg.validate_config(), "Configuration is valid")

    def test_missing_server(self):
        cfg = config.init("./tests/configs/missing_server.toml")
        self.assertNotEqual(cfg, None, "Config is None")
        self.assertFalse(cfg.validate_config(), "Configuration is valid")

    def test_missing_port(self):
        cfg = config.init("./tests/configs/missing_port.toml")
        self.assertNotEqual(cfg, None, "Config is None")
        self.assertFalse(cfg.validate_config(), "Configuration is valid")

    def test_missing_channels(self):
        cfg = config.init("./tests/configs/missing_channels.toml")
        self.assertNotEqual(cfg, None, "Config is None")
        self.assertFalse(cfg.validate_config(), "Configuration is valid")

    def test_missing_inviter(self):
        cfg = config.init("./tests/configs/missing_inviter.toml")
        self.assertNotEqual(cfg, None, "Config is None")
        self.assertFalse(cfg.validate_config(), "Configuration is valid")

    def test_missing_invite_cmd(self):
        cfg = config.init("./tests/configs/missing_invite_cmd.toml")
        self.assertNotEqual(cfg, None, "Config is None")
        self.assertFalse(cfg.validate_config(), "Configuration is valid")

    def test_both_sonarr(self):
        cfg = config.init("./tests/configs/both_sonarr.toml")
        self.assertNotEqual(cfg, None, "Config is None")
        self.assertFalse(cfg.validate_config(), "Configuration is valid")

    def test_both_radarr(self):
        cfg = config.init("./tests/configs/both_radarr.toml")
        self.assertNotEqual(cfg, None, "Config is None")
        self.assertFalse(cfg.validate_config(), "Configuration is valid")

    def test_both_lidarr(self):
        cfg = config.init("./tests/configs/both_lidarr.toml")
        self.assertNotEqual(cfg, None, "Config is None")
        self.assertFalse(cfg.validate_config(), "Configuration is valid")

    def test_missing_backend_type(self):
        cfg = config.init("./tests/configs/missing_backend_type.toml")
        self.assertNotEqual(cfg, None, "Config is None")
        self.assertFalse(cfg.toml["backends"]["mlidarr"].get("type"), None)
        self.assertFalse(cfg.toml["backends"]["mlidarr"].get("url"), None)
        self.assertFalse(cfg.validate_config(), "Configuration is valid")

    def test_invalid_backend_type(self):
        cfg = config.init("./tests/configs/invalid_backend_type.toml")
        self.assertNotEqual(cfg, None, "Config is None")
        self.assertFalse(cfg.validate_config(), "Configuration is valid")

    def test_cannot_notify_lidarr(self):
        cfg = config.init("./tests/configs/cannot_notify_lidarr.toml")
        self.assertNotEqual(cfg, None, "Config is None")
        self.assertFalse(cfg.validate_config(), "Configuration is valid")

    def test_empty_value(self):
        cfg = config.init("./tests/configs/empty_value.toml")
        self.assertNotEqual(cfg, None, "Config is None")
        self.assertFalse(cfg.validate_config(), "Configuration is valid")

    def test_invalid_config(self):
        cfg = config.init("./tests/configs/invalid_toml.toml")
        self.assertEqual(cfg, None, "Config is not None")

    def test_invalid_mandatory_type(self):
        cfg = config.init("./tests/configs/invalid_mandatory_type.toml")
        self.assertEqual(cfg, None, "Config is not None")

    def test_invalid_optional_type(self):
        cfg = config.init("./tests/configs/invalid_optional_type.toml")
        self.assertEqual(cfg, None, "Config is not None")

    def test_invalid_backend_toml_type(self):
        cfg = config.init("./tests/configs/invalid_backend_toml_type.toml")
        self.assertEqual(cfg, None, "Config is not None")

    def test_invalid_category_type(self):
        cfg = config.init("./tests/configs/invalid_category_type.toml")
        self.assertEqual(cfg, None, "Config is not None")

    def test_invalid_settings_type(self):
        cfg = config.init("./tests/configs/invalid_settings_type.toml")
        self.assertEqual(cfg, None, "Config is not None")


if __name__ == "__main__":
    unittest.main()
