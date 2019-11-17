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

    # Trackers
    cfg.init('iptorrents.nick', '')
    cfg.init('iptorrents.nick_pass', '')
    cfg.init('iptorrents.auth_key', '')
    cfg.init('iptorrents.torrent_pass', '')
    cfg.init('iptorrents.invite_key', '')
    cfg.init('iptorrents.delay', 0)

    cfg.init('torrentleech.nick', '')
    cfg.init('torrentleech.nick_pass', '')
    cfg.init('torrentleech.auth_key', '')
    cfg.init('torrentleech.torrent_pass', '')
    cfg.init('torrentleech.invite_key', '')
    cfg.init('torrentleech.delay', 0)

    cfg.init('alpharatio.nick', '')
    cfg.init('alpharatio.nick_pass', '')
    cfg.init('alpharatio.auth_key', '')
    cfg.init('alpharatio.torrent_pass', '')
    cfg.init('alpharatio.invite_key', '')
    cfg.init('alpharatio.delay', 0)

    cfg.init('revolutiontt.nick', '')
    cfg.init('revolutiontt.nick_pass', '')
    cfg.init('revolutiontt.auth_key', '')
    cfg.init('revolutiontt.torrent_pass', '')
    cfg.init('revolutiontt.invite_key', '')
    cfg.init('revolutiontt.delay', 0)

    cfg.init('morethan.nick', '')
    cfg.init('morethan.nick_pass', '')
    cfg.init('morethan.auth_key', '')
    cfg.init('morethan.torrent_pass', '')
    cfg.init('morethan.delay', 0)

    cfg.init('btn.nick', '')
    cfg.init('btn.nick_pass', '')
    cfg.init('btn.auth_key', '')
    cfg.init('btn.torrent_pass', '')
    cfg.init('btn.delay', 0)

    cfg.init('nbl.nick', '')
    cfg.init('nbl.nick_pass', '')
    cfg.init('nbl.auth_key', '')
    cfg.init('nbl.torrent_pass', '')
    cfg.init('nbl.delay', 0)

    cfg.init('hdtorrents.nick', '')
    cfg.init('hdtorrents.nick_pass', '')
    cfg.init('hdtorrents.cookies', '')
    cfg.init('hdtorrents.delay', 0)

    cfg.init('xspeeds.nick', '')
    cfg.init('xspeeds.nick_pass', '')
    cfg.init('xspeeds.torrent_pass', '')
    cfg.init('xspeeds.delay', 0)

    cfg.init('flro.nick', '')
    cfg.init('flro.nick_pass', '')
    cfg.init('flro.torrent_pass', '')
    cfg.init('flro.delay', 0)

    cfg.init('red.nick', '')
    cfg.init('red.nick_pass', '')
    cfg.init('red.invite_key', '')
    cfg.init('red.auth_key', '')
    cfg.init('red.torrent_pass', '')
    cfg.init('red.delay', 0)

    cfg.sync()
    return cfg
