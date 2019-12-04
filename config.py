import profig

cfg = None
base_sections = [ "server", "sonarr", "radarr", "lidarr", "bot" ]


def init():
    global cfg
    if cfg is not None:
        return cfg

    cfg = profig.Config('settings.cfg')
    cfg.read()

    # Settings
    cfg.init('server.host', 'localhost')
    cfg.init('server.port', '3467')
    cfg.init('server.user', 'admin')
    cfg.init('server.pass', 'password')

    cfg.init('sonarr.apikey', None, type=str)
    cfg.init('sonarr.url', 'http://localhost:8989')

    cfg.init('radarr.apikey', None, type=str)
    cfg.init('radarr.url', 'http://localhost:7878')

    cfg.init('lidarr.apikey', None, type=str)
    cfg.init('lidarr.url', 'http://localhost:8686')

    cfg.init('bot.debug_file', True)
    cfg.init('bot.debug_console', True)

    #cfg.init('revolutiontt.nick', '')
    #cfg.init('revolutiontt.nick_pass', '')
    #cfg.init('revolutiontt.auth_key', '')
    #cfg.init('revolutiontt.torrent_pass', '')
    #cfg.init('revolutiontt.invite_key', '')
    #cfg.init('revolutiontt.delay', 0)

    #cfg.sync()
    #print(cfg)
    #print(cfg["radarr.apikey"])
    #for s in cfg.sections():
    #    print(s)
    return cfg

server_fields = { "host": True, "port": True, "user": False, "pass": False }

def validate_config():
    global cfg
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
    return valid
