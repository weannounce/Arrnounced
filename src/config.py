import logging
import io
import sys
from tomlkit import parse


toml_cfg = None
base_sections = ["webui", "log", "sonarr", "radarr", "lidarr"]
logger = logging.getLogger("CONFIG")


def _init_value(table, key, value):
    if table.get(key) is None:
        table[key] = value


def init(config_path):
    global toml_cfg
    global base_sections

    with io.open(config_path) as f:
        try:
            toml_cfg = parse(f.read())
        except Exception as e:
            print("Error {}: {}".format(config_path, e), file=sys.stderr)
            return toml_cfg

    # Settings
    _init_value(toml_cfg, "webui", {})
    _init_value(toml_cfg["webui"], "host", "0.0.0.0")
    _init_value(toml_cfg["webui"], "port", 3467)
    # _init_value(toml_cfg["webui"], "username", None)
    # _init_value(toml_cfg["webui"], "password", None)
    _init_value(toml_cfg["webui"], "shutdown", False)

    _init_value(toml_cfg, "log", {})
    _init_value(toml_cfg["log"], "to_file", True)
    _init_value(toml_cfg["log"], "to_console", True)

    _init_value(toml_cfg, "sonarr", {})
    # _init_value(toml_cfg["sonarr"], "apikey", None)
    _init_value(toml_cfg["sonarr"], "url", "http://localhost:8989")

    _init_value(toml_cfg, "radarr", {})
    # _init_value(toml_cfg["radarr"], "apikey", None)
    _init_value(toml_cfg["radarr"], "url", "http://localhost:7878")

    _init_value(toml_cfg, "lidarr", {})
    # _init_value(toml_cfg["lidarr"], "apikey", None)
    _init_value(toml_cfg["lidarr"], "url", "http://localhost:8686")

    for section in toml_cfg.keys():
        if section in base_sections:
            continue
        # Init mandatory tracker values
        # _init_value(toml_cfg[section], "irc_nickname", None)
        # _init_value(toml_cfg[section], "irc_server", None)
        # _init_value(toml_cfg[section], "irc_port", None)
        # _init_value(toml_cfg[section], "irc_channels", None)

        # Init optional tracker values
        _init_value(toml_cfg[section], "irc_tls", False)
        _init_value(toml_cfg[section], "irc_tls_verify", False)
        # _init_value(toml_cfg[section], "irc_ident_password", None)
        # _init_value(toml_cfg[section], "irc_inviter", None)
        # _init_value(toml_cfg[section], "irc_invite_cmd", None)
        _init_value(toml_cfg[section], "torrent_https", False)
        _init_value(toml_cfg[section], "announce_delay", 0)
        _init_value(toml_cfg[section], "notify_sonarr", False)
        _init_value(toml_cfg[section], "notify_radarr", False)
        _init_value(toml_cfg[section], "notify_lidarr", False)
        # _init_value(toml_cfg[section], "category_sonarr", None, type=str)
        # _init_value(toml_cfg[section], "category_radarr", None, type=str)
        # _init_value(toml_cfg[section], "category_lidarr", None, type=str)

    # for k, v in toml_cfg.items():
    #    print(k + ": " + str(v))
    return toml_cfg


mandatory_tracker_fields = ["irc_nickname", "irc_server", "irc_port", "irc_channels"]


def validate_config():  # noqa: C901
    global toml_cfg
    valid = True

    if not (
        toml_cfg["sonarr"].get("apikey") is not None
        or toml_cfg["radarr"].get("apikey") is not None
        or toml_cfg["lidarr"].get("apikey") is not None
    ):
        logger.error("Must specify at least one backend (Sonarr/Radarr/Lidarr)")
        valid = False

    for section_name, section in toml_cfg.items():
        if section_name == "webui":
            if bool(section.get("username")) != bool(section.get("password")):
                logger.error(
                    "%s: Must set none or both 'username' and 'password'", section_name
                )
                valid = False
            continue
        elif section_name in base_sections:
            continue

        for mandatory in mandatory_tracker_fields:
            if not section.get(mandatory):
                logger.error("%s: Must set '%s'", section_name, mandatory)
                valid = False

        if bool(section.get("irc_inviter")) != bool(section.get("irc_invite_cmd")):
            logger.error(
                "%s: Must set both 'irc_inviter' and 'irc_invite_cmd'", section_name
            )
            valid = False

        if (
            section.get("notify_sonarr") or section.get("category_sonarr") is not None
        ) and toml_cfg["sonarr"].get("apikey") is None:
            logger.error(
                "%s: Must configure sonarr to use 'notify_sonarr' or 'category_sonarr'",
                section_name,
            )
            valid = False
        if (
            section.get("notify_radarr") or section.get("category_radarr") is not None
        ) and toml_cfg["radarr"].get("apikey") is None:
            logger.error(
                "%s: Must configure radarr to use 'notify_radarr' or 'category_radarr'",
                section_name,
            )
            valid = False
        if (
            section.get("notify_lidarr") or section.get("category_lidarr") is not None
        ) and toml_cfg["lidarr"].get("apikey") is None:
            logger.error(
                "%s: Must configure lidarr to use 'notify_lidarr' or 'category_lidarr'",
                section_name,
            )
            valid = False

        if section.get("notify_sonarr") and section.get("category_sonarr") is not None:
            logger.error(
                "%s: Cannot use both notify_sonarr and cateogry_sonarr", section_name
            )
            valid = False
        if section.get("notify_radarr") and section.get("category_radarr") is not None:
            logger.error(
                "%s: Cannot use both notify_radarr and cateogry_radarr", section_name
            )
            valid = False
        if section.get("notify_lidarr") and section.get("category_lidarr") is not None:
            logger.error(
                "%s: Cannot use both notify_lidarr and cateogry_lidarr", section_name
            )
            valid = False

    valid = _check_empty_values(toml_cfg, []) and valid
    return valid


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


def sections():
    return toml_cfg.keys()


def webui_host():
    return toml_cfg["webui"]["host"]


def webui_port():
    return toml_cfg["webui"]["port"]


def webui_shutdown():
    return toml_cfg["webui"]["shutdown"]


def login_required():
    if toml_cfg["webui"].get("username") is None:
        return False
    else:
        return True


def login(username, password):
    if toml_cfg["webui"].get("username") is None:
        return True
    elif (
        toml_cfg["webui"].get("username") == username
        and toml_cfg["webui"].get("password") == password
    ):
        return True
    return False
