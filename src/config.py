import logging
import profig

cfg = None
base_sections = ["webui", "log", "sonarr", "radarr", "lidarr"]
logger = logging.getLogger("CONFIG")


def init(config_path):
    global cfg
    global base_sections

    cfg = profig.Config(config_path)
    cfg.read()

    # Settings
    cfg.init("webui.host", "0.0.0.0")
    cfg.init("webui.port", 3467)
    cfg.init("webui.username", None, type=str)
    cfg.init("webui.password", None, type=str)

    cfg.init("log.to_file", True)
    cfg.init("log.to_console", True)

    cfg.init("sonarr.apikey", None, type=str)
    cfg.init("sonarr.url", "http://localhost:8989")

    cfg.init("radarr.apikey", None, type=str)
    cfg.init("radarr.url", "http://localhost:7878")

    cfg.init("lidarr.apikey", None, type=str)
    cfg.init("lidarr.url", "http://localhost:8686")

    for section in cfg.sections():
        if section.name in base_sections:
            continue
        # Init mandatory tracker values
        section.init("irc_nickname", None, type=str)
        section.init("irc_server", None, type=str)
        section.init("irc_port", None, type=int)
        section.init("irc_channels", None, type=str)

        # Init optional tracker values
        section.init("irc_tls", False)
        section.init("irc_tls_verify", False)
        section.init("irc_ident_password", None, type=str)
        section.init("irc_inviter", None, type=str)
        section.init("irc_invite_cmd", None, type=str)
        section.init("announce_delay", 0)
        section.init("notify_sonarr", False)
        section.init("notify_radarr", False)
        section.init("notify_lidarr", False)
        section.init("category_sonarr", None, type=str)
        section.init("category_radarr", None, type=str)
        section.init("category_lidarr", None, type=str)

    # for s in cfg.sections():
    #    print(s)
    return cfg


mandatory_tracker_fields = ["irc_nickname", "irc_server", "irc_port", "irc_channels"]


def validate_config():  # noqa: C901
    global cfg
    valid = True

    if not (
        cfg.get("sonarr.apikey") or cfg.get("radarr.apikey") or cfg.get("lidarr.apikey")
    ):
        logger.error("Must specify at least one backend (Sonarr/Radarr/Lidarr)")
        valid = False

    for section in cfg.sections():
        if section.name == "webui":
            if bool(section.get("username")) != bool(section.get("password")):
                logger.error(
                    "%s: Must set none or both 'username' and 'password'", section.name
                )
                valid = False
            continue
        elif section.name in base_sections:
            continue

        for mandatory in mandatory_tracker_fields:
            if not section.get(mandatory):
                logger.error("%s: Must set '%s'", section.name, mandatory)
                valid = False

        if bool(section.get("irc_inviter")) != bool(section.get("irc_invite_cmd")):
            logger.error(
                "%s: Must set both 'irc_inviter' and 'irc_invite_cmd'", section.name
            )
            valid = False

        if (
            section.get("notify_sonarr") or section.get("category_sonarr") is not None
        ) and cfg.get("sonarr.apikey") is None:
            logger.error(
                "%s: Must configure sonarr to use 'notify_sonarr' or 'category_sonarr'",
                section.name,
            )
            valid = False
        if (
            section.get("notify_radarr") or section.get("category_radarr") is not None
        ) and cfg.get("radarr.apikey") is None:
            logger.error(
                "%s: Must configure radarr to use 'notify_radarr' or 'category_radarr'",
                section.name,
            )
            valid = False
        if (
            section.get("notify_lidarr") or section.get("category_lidarr") is not None
        ) and cfg.get("lidarr.apikey") is None:
            logger.error(
                "%s: Must configure lidarr to use 'notify_lidarr' or 'category_lidarr'",
                section.name,
            )
            valid = False

        if section.get("notify_sonarr") and section.get("category_sonarr") is not None:
            logger.error(
                "%s: Cannot use both notify_sonarr and cateogry_sonarr", section.name
            )
            valid = False
        if section.get("notify_radarr") and section.get("category_radarr") is not None:
            logger.error(
                "%s: Cannot use both notify_radarr and cateogry_radarr", section.name
            )
            valid = False
        if section.get("notify_lidarr") and section.get("category_lidarr") is not None:
            logger.error(
                "%s: Cannot use both notify_lidarr and cateogry_lidarr", section.name
            )
            valid = False

    for section in cfg:
        if len(str(cfg[section])) == 0:
            logger.error(
                "%s: Empty value in configuration not allowed. Remove instead.", section
            )
            valid = False
    return valid


def sections():
    return cfg.sections()


def webui_host():
    return cfg["webui.host"]


def webui_port():
    return cfg["webui.port"]


def login_required():
    if cfg["webui.username"] is None:
        return False
    else:
        return True


def login(username, password):
    if cfg["webui.username"] is None:
        return True
    elif cfg["webui.username"] == username and cfg["webui.password"] == password:
        return True
    return False
