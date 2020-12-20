import logging
import io
import sys
from tomlkit import parse


backend_urls = {
    "sonarr": "http://localhost:8989",
    "radarr": "http://localhost:7878",
    "lidarr": "http://localhost:8686",
}
mandatory_tracker_fields = ["irc_nickname", "irc_server", "irc_port", "irc_channels"]
logger = logging.getLogger("CONFIG")


class UserConfig:
    def __init__(self, toml):
        self.toml = toml

    def validate_config(self):  # noqa: C901
        valid = True

        if bool(self.toml["webui"].get("username")) != bool(
            self.toml["webui"].get("password")
        ):
            logger.error("webui: Must set none or both 'username' and 'password'")
            valid = False

        if len(self.toml["backends"]) == 0:
            logger.error("Must specify at least one backend (Sonarr/Radarr/Lidarr)")
            valid = False

        for section_name, section in self.toml["backends"].items():
            if (
                not section.get("type")
                or section.get("type").lower() not in backend_urls
            ):
                logger.error(
                    "backends.%s: Must specify type, one of sonarr, radarr, lidarr",
                    section_name,
                )
                valid = False
            if not section.get("apikey"):
                logger.error("backends.%s: Must specify apikey", section_name)
                valid = False

        for section_name, section in self.toml["trackers"].items():
            for mandatory in mandatory_tracker_fields:
                if not section.get(mandatory):
                    logger.error("trackers.%s: Must set '%s'", section_name, mandatory)
                    valid = False

            if bool(section.get("irc_inviter")) != bool(section.get("irc_invite_cmd")):
                logger.error(
                    "trackers.%s: Must set both 'irc_inviter' and 'irc_invite_cmd'",
                    section_name,
                )
                valid = False

            always_backends = (
                [b.strip() for b in section.get("notify").split(",")]
                if section.get("notify")
                else []
            )
            category_backends = list(section.get("category").keys())

            for b in always_backends + category_backends:
                if b not in self.toml["backends"]:
                    logger.error(
                        "trackers.%s: No backend named '%s' found", section_name, b
                    )
                    valid = False

            backend_duplicates = [b for b in always_backends if b in category_backends]
            if len(backend_duplicates) != 0:
                logger.error(
                    "trackers.%s: Cannot specify the same backend for both 'notify' and 'category'. Found %s",
                    section_name,
                    ",".join(backend_duplicates),
                )
                valid = False

        valid = _check_empty_values(self.toml, []) and valid
        return valid

    class UserBackend:
        def __init__(self, name, user_backend):
            self.name = name
            self.backend = user_backend

        @property
        def type(self):
            return self.backend["type"].lower()

        @property
        def apikey(self):
            return self.backend["apikey"]

        @property
        def url(self):
            return self.backend.get("url")

    @property
    def backends(self):
        return [UserConfig.UserBackend(n, b) for n, b in self.toml["backends"].items()]

    class UserTracker:
        def __init__(self, tracker_type, user_tracker):
            self.type = tracker_type
            self.tracker = user_tracker

        @property
        def settings(self):
            return self.tracker["settings"]

    @property
    def trackers(self):
        return [
            UserConfig.UserTracker(ttype, t)
            for ttype, t in self.toml["trackers"].items()
        ]

    @property
    def log_to_console(self):
        return self.toml["log"]["to_console"]

    @property
    def log_to_file(self):
        return self.toml["log"]["to_file"]

    @property
    def webui_host(self):
        return self.toml["webui"]["host"]

    @property
    def webui_port(self):
        return self.toml["webui"]["port"]

    @property
    def webui_shutdown(self):
        return self.toml["webui"]["shutdown"]

    @property
    def login_required(self):
        return self.toml["webui"].get("username") is not None

    def login(self, username, password):
        if self.toml["webui"].get("username") is None:
            return True
        elif (
            self.toml["webui"].get("username") == username
            and self.toml["webui"].get("password") == password
        ):
            return True
        return False


def _init_value(table, key, value):
    if table.get(key) is None:
        table[key] = value


def toml_notice():
    print(
        "Please note that the configuration format has changed to TOML", file=sys.stderr
    )
    print("Because of this", file=sys.stderr)
    print("* The default config file path has changed", file=sys.stderr)
    print("* Config file must be updated to conform with TOML", file=sys.stderr)
    print("See the release notes for more info", file=sys.stderr)


def init(config_path):
    toml_cfg = None
    with io.open(config_path) as f:
        try:
            toml_cfg = parse(f.read())
        except Exception as e:
            print("Error {}: {}".format(config_path, e), file=sys.stderr)
            toml_notice()
            return None

    # TODO: Check types
    # Settings
    _init_value(toml_cfg, "webui", {})
    _init_value(toml_cfg["webui"], "host", "0.0.0.0")
    _init_value(toml_cfg["webui"], "port", 3467)
    _init_value(toml_cfg["webui"], "shutdown", False)

    _init_value(toml_cfg, "log", {})
    _init_value(toml_cfg["log"], "to_file", True)
    _init_value(toml_cfg["log"], "to_console", True)

    _init_value(toml_cfg, "backends", {})
    for backend_name in toml_cfg["backends"]:
        backend_type = toml_cfg["backends"][backend_name].get("type")
        if not backend_type:
            continue
        default_url = backend_urls.get(backend_type.lower())
        if not default_url:
            continue
        _init_value(toml_cfg["backends"][backend_name], "url", default_url)

    _init_value(toml_cfg, "trackers", {})
    for tracker_type in toml_cfg["trackers"]:
        # Init optional tracker values
        _init_value(toml_cfg["trackers"][tracker_type], "irc_tls", False)
        _init_value(toml_cfg["trackers"][tracker_type], "irc_tls_verify", False)
        _init_value(toml_cfg["trackers"][tracker_type], "torrent_https", False)
        _init_value(toml_cfg["trackers"][tracker_type], "announce_delay", 0)
        _init_value(toml_cfg["trackers"][tracker_type], "category", {})
        _init_value(toml_cfg["trackers"][tracker_type], "settings", {})

    # for k, v in toml_cfg.items():
    #    print(k + ": " + str(v))
    return UserConfig(toml_cfg)


def _check_empty_values(section, prior_sections):
    valid = True
    for key, value in section.items():
        if type(value) is dict:
            valid = _check_empty_values(value, prior_sections + [key]) and valid
        elif len(str(value)) == 0:
            logger.error(
                "%s.%s: Empty value in configuration not allowed. Remove instead.",
                ".".join(prior_sections),
                key,
            )
            valid = False
    return valid
