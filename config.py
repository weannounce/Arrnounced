import profig
import logging

cfg = None
_valid = True
base_sections = [ "server", "bot", "sonarr", "radarr", "lidarr" ]
logger = logging.getLogger("CONFIG")

def init():
    global cfg
    global _valid
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
        # Check mandatory values
        section.init('nick', None, type=str)
        nick = section["nick"]
        if nick is None or len(nick) == 0:
            logger.error("{}: nick not set: {}".format(section.name, str(nick)))
            _valid = False


        # Init optional tracker values
        section.init('tls', False)
        section.init('tls_verify', False)
        section.init('irc_port', 6667)
        section.init('nick_pass', None, type=str)
        section.init('auth_key', None, type=str)
        section.init('torrent_pass', None, type=str)
        section.init('invite_key', None, type=str)
        section.init('delay', 0)


    #cfg.sync()
    #for s in cfg.sections():
    #    print(s)
    return cfg

server_fields = { "host": True, "port": True, "user": False, "pass": False }

def validate_config():
    global cfg
    global _valid
    if not _valid:
        return _valid

    sections = cfg.as_dict()
    if "server" in sections: 
        for field, mandatory in server_fields.items():
            if mandatory and cfg.section("server")[field] is None:
                _valid = False
            elif cfg.section("server")[field] is not None and len(cfg.section("server")[field]) == 0:
                _valid = False
    else:
        _valid = False
    return _valid
