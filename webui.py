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
from backend import notify_sonarr, notify_radarr
import utils

logger = logging.getLogger("WEB-UI")

app = Flask("Announced")
auth = HTTPBasicAuth()
cfg = config.init()
trackers = None


def run(loaded_trackers):
    global trackers
    trackers = loaded_trackers
    app.run(debug=False, host=cfg['webui.host'], port=int(cfg['webui.port']), use_reloader=False)


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
            download_url = found_tracker.get_real_torrent_link(torrent_id, torrent_name)
            # ask tracker for cookies
            cookies = found_tracker.get_cookies()

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
    if not username == cfg['webui.user']:
        return None
    else:
        return cfg['webui.pass']
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

                # TODO: pvr_name may be multiple PVRs in the form "Sonarr/Radarr"
                if pvr_name == "Sonarr":
                    approved = notify_sonarr(announcement.title, announcement.torrent, announcement.indexer)
                elif pvr_name == "Radarr":
                    approved = notify_radarr(announcement.title, announcement.torrent, announcement.indexer)
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
