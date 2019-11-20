import logging
import os
import re
from urllib.parse import urlparse

import requests
from flask import Flask
from flask import abort
from flask import render_template
from flask import request
from flask import send_file
from flask import send_from_directory
from flask_httpauth import HTTPBasicAuth

import config
import db
from backend import sonarr_wanted, radarr_wanted
import utils

logger = logging.getLogger("WEB-UI")
logger.setLevel(logging.DEBUG)

app = Flask("Announced")
auth = HTTPBasicAuth()
cfg = config.init()
trackers = None


def run(loaded_trackers):
    global trackers
    trackers = loaded_trackers
    app.run(debug=False, host=cfg['server.host'], port=int(cfg['server.port']), use_reloader=False)


def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()


# mitm tracker torrent route
@app.route('/mitm/<tracker>/<torrent_id>/<torrent_name>')
def serve_torrent(tracker, torrent_id, torrent_name):
    global trackers
    found_tracker = None

    logger.debug("Requested MITM: %s (%s) from tracker: %s", torrent_name, torrent_id, tracker)
    try:
        found_tracker = trackers.get_tracker(tracker)
        if found_tracker is not None:
            # ask tracker for torrent url
            download_url = found_tracker['plugin'].get_real_torrent_link(torrent_id, torrent_name)
            # ask tracker for cookies
            cookies = found_tracker['plugin'].get_cookies()

            if download_url is not None and cookies is not None:
                # download torrent
                torrent_path = utils.download_torrent(tracker, torrent_id, cookies, download_url)
                if torrent_path is not None:
                    # serve torrent
                    logger.debug("Serving torrent: %s", torrent_path)
                    return send_file(filename_or_fp=torrent_path.__str__())

    except AttributeError:
        logger.debug("Tracker was not configured correctly for MITM torrent requests! "
                     "Required methods: get_real_torrent_link() and get_cookies()")
    except Exception as ex:
        logger.exception("Unexpected exception occurred at serve_torrent:")

    return abort(404)


# panel routes
@auth.get_password
def get_pw(username):
    if not username == cfg['server.user']:
        return None
    else:
        return cfg['server.pass']
    return None


@app.route('/assets/<path:path>')
@auth.login_required
def send_asset(path):
    return send_from_directory("templates/assets/{}".format(os.path.dirname(path)), os.path.basename(path))


@app.route("/")
@auth.login_required
@db.db_session
def index():
    return render_template('index.html', snatched=db.Snatched.select().order_by(db.desc(db.Snatched.date)).limit(20),
                           announced=db.Announced.select().order_by(db.desc(db.Announced.date)).limit(20))


@app.route("/trackers", methods=['GET', 'POST'])
@auth.login_required
def trackers():
    if request.method == 'POST':
        if 'iptorrents_torrentpass' in request.form:
            cfg['iptorrents.torrent_pass'] = request.form['iptorrents_torrentpass']
            cfg['iptorrents.nick'] = request.form['iptorrents_nick']
            cfg['iptorrents.nick_pass'] = request.form['iptorrents_nickpassword']
            cfg['iptorrents.delay'] = request.form['iptorrents_delay']
            logger.debug("saved iptorrents settings")

        if 'morethan_torrentpass' in request.form:
            cfg['morethan.auth_key'] = request.form['morethan_authkey']
            cfg['morethan.torrent_pass'] = request.form['morethan_torrentpass']
            cfg['morethan.nick'] = request.form['morethan_nick']
            cfg['morethan.nick_pass'] = request.form['morethan_nickpassword']
            cfg['morethan.delay'] = request.form['morethan_delay']
            logger.debug("saved morethan settings")

        if 'btn_torrentpass' in request.form:
            cfg['btn.auth_key'] = request.form['btn_authkey']
            cfg['btn.torrent_pass'] = request.form['btn_torrentpass']
            cfg['btn.nick'] = request.form['btn_nick']
            cfg['btn.nick_pass'] = request.form['btn_nickpassword']
            cfg['btn.delay'] = request.form['btn_delay']
            logger.debug("saved btn settings")

        if 'nbl_torrentpass' in request.form:
            cfg['nbl.auth_key'] = request.form['nbl_authkey']
            cfg['nbl.torrent_pass'] = request.form['nbl_torrentpass']
            cfg['nbl.nick'] = request.form['nbl_nick']
            cfg['nbl.nick_pass'] = request.form['nbl_nickpassword']
            cfg['nbl.delay'] = request.form['nbl_delay']
            logger.debug("saved nbl settings")

        if 'hdtorrents_cookies' in request.form:
            cfg['hdtorrents.cookies'] = request.form['hdtorrents_cookies']
            cfg['hdtorrents.nick'] = request.form['hdtorrents_nick']
            cfg['hdtorrents.nick_pass'] = request.form['hdtorrents_nickpassword']
            cfg['hdtorrents.delay'] = request.form['hdtorrents_delay']
            logger.debug("saved hdtorrents settings")

        if 'xspeeds_torrentpass' in request.form:
            cfg['xspeeds.torrent_pass'] = request.form['xspeeds_torrentpass']
            cfg['xspeeds.nick'] = request.form['xspeeds_nick']
            cfg['xspeeds.nick_pass'] = request.form['xspeeds_nickpassword']
            cfg['xspeeds.delay'] = request.form['xspeeds_delay']
            logger.debug("saved xspeeds settings")

        if 'flro_torrentpass' in request.form:
            cfg['flro.torrent_pass'] = request.form['flro_torrentpass']
            cfg['flro.nick'] = request.form['flro_nick']
            cfg['flro.nick_pass'] = request.form['flro_nickpassword']
            cfg['flro.delay'] = request.form['flro_delay']
            logger.debug("saved filelist settings")

        if 'torrentleech_torrentpass' in request.form:
            cfg['torrentleech.torrent_pass'] = request.form['torrentleech_torrentpass']
            cfg['torrentleech.nick'] = request.form['torrentleech_nick']
            cfg['torrentleech.nick_pass'] = request.form['torrentleech_nickpassword']
            cfg['torrentleech.delay'] = request.form['torrentleech_delay']
            logger.debug("saved torrentleech settings")

        if 'alpharatio_torrentpass' in request.form:
            cfg['alpharatio.torrent_pass'] = request.form['alpharatio_torrentpass']
            cfg['alpharatio.nick'] = request.form['alpharatio_nick']
            cfg['alpharatio.nick_pass'] = request.form['alpharatio_nickpassword']
            cfg['alpharatio.delay'] = request.form['alpharatio_delay']
            logger.debug("saved alpharatio settings")

        if 'revolutiontt_torrentpass' in request.form:
            cfg['revolutiontt.torrent_pass'] = request.form['revolutiontt_torrentpass']
            cfg['revolutiontt.nick'] = request.form['revolutiontt_nick']
            cfg['revolutiontt.nick_pass'] = request.form['revolutiontt_nickpassword']
            cfg['revolutiontt.delay'] = request.form['revolutiontt_delay']
            logger.debug("saved revolutiontt settings")

        cfg.sync()

    return render_template('trackers.html')


@app.route("/logs")
@auth.login_required
def logs():
    logs = []
    with open('status.log') as f:
        for line in f:
            log_parts = re.search('(^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})\s-\s(\S+)\s+-\s(.+)', line)
            if log_parts:
                logs.append({'time': log_parts.group(1),
                             'tag': log_parts.group(2),
                             'msg': log_parts.group(3)})

    return render_template('logs.html', logs=logs)


@app.route("/settings", methods=['GET', 'POST'])
@auth.login_required
def settings():
    if request.method == 'POST':
        cfg['server.host'] = request.form['server_host']
        cfg['server.port'] = request.form['server_port']
        cfg['server.user'] = request.form['server_user']
        cfg['server.pass'] = request.form['server_pass']

        cfg['sonarr.url'] = request.form['sonarr_url']
        cfg['sonarr.apikey'] = request.form['sonarr_apikey']

        cfg['radarr.url'] = request.form['radarr_url']
        cfg['radarr.apikey'] = request.form['radarr_apikey']

        if 'debug_file' in request.form:
            cfg['bot.debug_file'] = True
        else:
            cfg['bot.debug_file'] = False

        if 'debug_console' in request.form:
            cfg['bot.debug_console'] = True
        else:
            cfg['bot.debug_console'] = False

        cfg.sync()
        logger.debug("Saved settings: %s", request.form)

    return render_template('settings.html')


@app.route("/<pvr_name>/check", methods=['POST'])
@auth.login_required
def check(pvr_name):
    try:
        data = request.json
        if 'apikey' in data and 'url' in data:
            # Check if api key is valid
            logger.debug("Checking whether apikey: %s is valid for: %s", data.get('apikey'), data.get('url'))

            headers = {'X-Api-Key': data.get('apikey')}
            resp = requests.get(url="{}/api/diskspace".format(data.get('url')), headers=headers).json()
            logger.debug("check response: %s", resp)

            if 'error' not in resp:
                return 'OK'

    except Exception as ex:
        logger.exception("Exception while checking " + pvr_name + " apikey:")

    return 'ERR'


@app.route("/<pvr_name>/notify", methods=['POST'])
@auth.login_required
@db.db_session
def notify(pvr_name):
    try:
        data = request.json
        if 'id' in data:
            # Request to check this torrent again
            announcement = db.Announced.get(id=data.get('id'))
            if announcement is not None and len(announcement.title) > 0:
                logger.debug("Checking announcement again: %s", announcement.title)

                if pvr_name == "Sonarr":
                    approved = sonarr_wanted(announcement.title, announcement.torrent, announcement.indexer)
                elif pvr_name == "Radarr":
                    approved = radarr_wanted(announcement.title, announcement.torrent, announcement.indexer)
                if approved:
                    logger.debug(pvr_name + " accepted the torrent this time!")
                    return "OK"
                else:
                    logger.debug(pvr_name + " still refused this torrent...")
                    return "ERR"

    except Exception as ex:
        logger.exception("Exception while notifying " + pvr_name + " announcement:")

    return "ERR"


@app.context_processor
def inject_conf_in_all_templates():
    global cfg
    return dict(conf=cfg)


@app.context_processor
def utility_processor():
    def format_timestamp(timestamp):
        formatted = utils.human_datetime(timestamp)
        return formatted

    def correct_download(link):
        formatted = link
        if 'localhost' in link:
            parts = urlparse(request.url)
            if parts.hostname is not None:
                formatted = formatted.replace('localhost', parts.hostname)

        return formatted

    return dict(format_timestamp=format_timestamp, correct_download=correct_download)
