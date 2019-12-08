import profig
import logging

cfg = None
base_sections = [ "server", "bot", "sonarr", "radarr", "lidarr" ]
logger = logging.getLogger("CONFIG")

def init():
    global cfg
    global base_sections
    if cfg is not None:
        return cfg

    cfg = profig.Config('settings.cfg')
    cfg.read()

    # Settings
    cfg.init('server.host', 'localhost')
    cfg.init('server.port', '3467')
    cfg.init('server.user', 'admin')
    cfg.init('server.pass', 'password')

    cfg.init('bot.debug_file', True)
    cfg.init('bot.debug_console', True)

    cfg.init('sonarr.apikey', None, type=str)
    cfg.init('sonarr.url', 'http://localhost:8989')

    cfg.init('radarr.apikey', None, type=str)
    cfg.init('radarr.url', 'http://localhost:7878')

    cfg.init('lidarr.apikey', None, type=str)
    cfg.init('lidarr.url', 'http://localhost:8686')

    for section in cfg.sections():
        if section.name in base_sections:
            continue
        # Init mandatory tracker values
        section.init('nick', None, type=str)

        # Init optional tracker values
        section.init('irc_port', 6667)
        section.init('tls', False)
        section.init('tls_verify', False)
        section.init('nick_pass', None, type=str)
        section.init('inviter', None, type=str)
        section.init('invite_cmd', None, type=str)
        section.init('delay', 0)
        section.init('notify_sonarr', False)
        section.init('notify_radarr', False)
        section.init('notify_lidarr', False)


    #for s in cfg.sections():
    #    print(s)
    return cfg

server_fields = { "host": True, "port": True, "user": False, "pass": False }
mandatory_tracker_fields = [ "nick" ]

def validate_config():
    global cfg
    global tracker_fields
    valid = True

    sections = cfg.as_dict()
    if "server" in sections:
        for field, mandatory in server_fields.items():
            if mandatory and cfg.section("server")[field] is None:
                valid = False
            elif cfg.section("server")[field] is not None and len(cfg.section("server")[field]) == 0:
                valid = False
    else:
        valid = False

    if not (cfg.get("sonarr.apikey") or
            cfg.get("radarr.apikey") or
            cfg.get("lidarr.apikey")):
        logger.error("Must specify at least one backend (Sonarr/Radarr/Lidarr)")
        valid = False

    for section in cfg.sections():
        if section.name in base_sections:
            continue

        for mandatory in mandatory_tracker_fields:
            if not section.get(mandatory):
                logger.error("{}: Must set '{}'".format(section.name, mandatory))
                valid = False

        if bool(section.get("inviter")) != bool(section.get("invite_cmd")):
            logger.error("{}: Must set both 'inviter' and 'invite_cmd'".format(section.name))
            valid = False

    for section in cfg:
        if len(str(cfg[section])) == 0:
            logger.error("{}: Empty value in configuration not allowed".format(section))
            valid = False
    return valid
