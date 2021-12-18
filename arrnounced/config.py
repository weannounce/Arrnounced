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
                [b.strip() for b in section.get("notify_backends").split(",")]
                if section.get("notify_backends")
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
                    "trackers.%s: Cannot specify the same backend for both 'notify_backends' and 'category'. Found %s",
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
        return str(self.toml["webui"]["host"])

    @property
    def webui_port(self):
        return int(self.toml["webui"]["port"])

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


def toml_notice():
    print(
        "Please note that the configuration format has changed to TOML", file=sys.stderr
    )
    print("Because of this", file=sys.stderr)
    print("* The default config file path has changed", file=sys.stderr)
    print("* Config file must be updated to conform with TOML", file=sys.stderr)
    print("See the release notes for more info", file=sys.stderr)


def _init_value(table, keys, value, value_type=None):
    if value_type is None:
        value_type = type(value)

    section = table
    for k in keys[:-1]:
        section = section[k]

    last_key = keys[-1]
    if value is not None and section.get(last_key) is None:
        section[last_key] = value
    elif section.get(last_key) is not None and not isinstance(
        section[last_key], value_type
    ):
        print(
            "Error: {} must be of type {}".format(".".join(keys), value_type.__name__)
        )
        return False

    return True


def _init_backends(toml_cfg):
    valid_types = True
    for backend_name in toml_cfg["backends"]:
        backend_type = toml_cfg["backends"][backend_name].get("type")
        if not backend_type:
            continue
        default_url = backend_urls.get(backend_type.lower())
        if not default_url:
            continue

        # Init default values and check types
        default_backend_values = [
            ("url", default_url, None),
            ("type", None, str),
            ("apikey", None, str),
        ]
        for last_key, default_value, the_type in default_backend_values:
            keys = ["backends", backend_name, last_key]
            valid_types = (
                _init_value(toml_cfg, keys, default_value, the_type) and valid_types
            )
    return valid_types


def _init_trackers(toml_cfg):
    valid_types = True
    for tracker_type in toml_cfg["trackers"]:
        # Init default values
        default_tracker_values = [
            ("irc_tls", False),
            ("irc_tls_verify", False),
            ("torrent_https", False),
            ("announce_delay", 0),
            ("category", {}),
            ("settings", {}),
        ]
        for last_key, default_value in default_tracker_values:
            keys = ["trackers", tracker_type, last_key]
            valid_types = _init_value(toml_cfg, keys, default_value) and valid_types

        # Check mandatory and empty value types
        tracker_types = [
            ("irc_nickname", str),
            ("irc_server", str),
            ("irc_port", int),
            ("irc_channels", str),
            ("irc_ident_password", str),
            ("irc_inviter", str),
            ("irc_invite_cmd", str),
            ("notify_backends", str),
        ]
        for last_key, the_type in tracker_types:
            keys = ["trackers", tracker_type, last_key]
            valid_types = _init_value(toml_cfg, keys, None, the_type) and valid_types

        # All settings must be string
        for setting in toml_cfg["trackers"][tracker_type]["settings"].keys():
            keys = ["trackers", tracker_type, "settings", setting]
            valid_types = _init_value(toml_cfg, keys, None, str) and valid_types

        # All categories must be string
        for category in toml_cfg["trackers"][tracker_type]["category"].keys():
            keys = ["trackers", tracker_type, "category", category]
            valid_types = _init_value(toml_cfg, keys, None, str) and valid_types

    return valid_types


def init(config_path):
    toml_cfg = None
    with io.open(config_path) as f:
        try:
            toml_cfg = parse(f.read())
        except Exception as e:
            print("Error {}: {}".format(config_path, e), file=sys.stderr)
            toml_notice()
            return None

    valid_types = True

    # Init default values
    default_values = [
        (["webui"], {}),
        (["webui", "host"], "0.0.0.0"),  # nosec B104: bind all interfaces
        (["webui", "port"], 3467),
        (["webui", "shutdown"], False),
        (["log"], {}),
        (["log", "to_file"], True),
        (["log", "to_console"], True),
        (["backends"], {}),
        (["trackers"], {}),
    ]
    for keys, default_value in default_values:
        valid_types = _init_value(toml_cfg, keys, default_value) and valid_types

    # Check type of default empty fields
    types = [
        (["webui", "username"], str),
        (["webui", "password"], str),
    ]
    for keys, the_type in types:
        valid_types = _init_value(toml_cfg, keys, None, the_type) and valid_types

    valid_types = _init_backends(toml_cfg) and valid_types
    valid_types = _init_trackers(toml_cfg) and valid_types

    if not valid_types:
        print(
            "Found configuration type error(s), double check your config quote marks, spelling and subsections"
        )
        return None

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
