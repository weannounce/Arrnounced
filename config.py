import profig

cfg = profig.Config('settings.cfg')


def init():
    global cfg

    # Settings
    cfg.init('server.host', 'localhost')
    cfg.init('server.port', '3467')
    cfg.init('server.user', 'admin')
    cfg.init('server.pass', 'password')

    cfg.init('sonarr.apikey', '')
    cfg.init('sonarr.url', 'http://localhost:8989')

    cfg.init('radarr.apikey', '')
    cfg.init('radarr.url', 'http://localhost:7878')

    cfg.init('lidarr.apikey', '')
    cfg.init('lidarr.url', 'http://localhost:8686')

    cfg.init('bot.debug_file', True)
    cfg.init('bot.debug_console', True)

    #cfg.init('revolutiontt.nick', '')
    #cfg.init('revolutiontt.nick_pass', '')
    #cfg.init('revolutiontt.auth_key', '')
    #cfg.init('revolutiontt.torrent_pass', '')
    #cfg.init('revolutiontt.invite_key', '')
    #cfg.init('revolutiontt.delay', 0)

    cfg.sync()
    return cfg
