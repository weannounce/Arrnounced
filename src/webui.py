import inspect
import logging
from math import ceil
import os
import requests
from flask import Flask
from flask import jsonify
from flask import redirect
from flask import render_template
from flask import request
from flask import send_from_directory
from flask import url_for
from flask_login import LoginManager
from flask_login import login_user, logout_user
from flask_login import login_required
from flask_login import UserMixin
from pathlib import Path

import config
import db
import irc
import log
import utils
from backend import renotify, get_configured_backends
from announcement import Announcement

logger = logging.getLogger("WEB-UI")
table_row_count = 20


class User(UserMixin):
    def get_id(self):
        return 1


# Template directory is the current ([0]) stack object's ([1]) directory + templates
templates_dir = Path(os.path.dirname(os.path.abspath(inspect.stack()[0][1]))).joinpath(
    "templates"
)
app = Flask("Arrnounced", template_folder=templates_dir)
# This will invalidate logins on each restart of Arrnounced
# But I'm too lazy to think of something else at the moment
app.secret_key = os.urandom(16)

login_manager = LoginManager(app=app)
login_manager.login_view = "login"
user = User()


def run():
    try:
        app.run(
            debug=False,
            host=config.webui_host(),
            port=config.webui_port(),
            use_reloader=False,
        )
    except OSError as e:
        logger.error("Error starting webserver: %s", e)


@app.route("/shutdown", methods=["GET", "POST"])
def shutdown():
    if not config.webui_shutdown():
        return redirect(url_for("index"))

    logger.info("Shutting down Arrnounced")
    logger.info("Disable shutdown by removing webui.shutdown from config")
    irc.stop()
    func = request.environ.get("werkzeug.server.shutdown")
    if func is None:
        raise RuntimeError("Not running with the Werkzeug Server")
    func()
    return "Shutting down..."


@login_manager.user_loader
def load_user(id):
    return user


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST" or not config.login_required():
        if config.login(request.form.get("username"), request.form.get("password")):
            login_user(user)
            return redirect(url_for("index"))
        else:
            error = "Invalid credentials"
    return render_template("login.html", error=error)


@app.route("/logout", methods=["GET", "POST"])
def logout():
    logout_user()
    return redirect(url_for("login"))


@app.route("/assets/<path:path>")
def send_asset(path):
    return send_from_directory(
        str(templates_dir) + "/assets/{}".format(os.path.dirname(path)),
        os.path.basename(path),
    )


@app.route("/")
@login_required
@db.db_session
def index():
    return render_template(
        "index.html",
        announcement_pages=ceil(db.get_announced_count() / table_row_count),
        snatch_pages=ceil(db.get_snatched_count() / table_row_count),
        login_required=config.login_required(),
    )


@app.route("/logs")
@login_required
def logs():
    logs = []
    for log_line in log.get_logs():
        logs.append({"time": log_line[0], "tag": log_line[1], "msg": log_line[2]})

    return render_template("logs.html", logs=logs)


# TODO: Reintroduce check ability
@app.route("/<pvr_name>/check", methods=["POST"])
@login_required
def check(pvr_name):
    try:
        data = request.json
        if "apikey" in data and "url" in data:
            # Check if api key is valid
            logger.debug(
                "Checking whether apikey: %s is valid for: %s",
                data.get("apikey"),
                data.get("url"),
            )

            headers = {"X-Api-Key": data.get("apikey")}
            resp = requests.get(
                url="{}/api/diskspace".format(data.get("url")), headers=headers
            ).json()
            logger.debug("check response: %s", resp)

            if "error" not in resp:
                return "OK"

    # TODO: Catch more specific types
    except Exception:
        logger.exception("Exception while checking " + pvr_name + " apikey:")

    return "ERR"


@app.route("/notify", methods=["POST"])
@login_required
@db.db_session
def notify():
    try:
        data = request.json
        if "id" in data and "backend_id" in data:
            # Request to check this torrent again
            db_announcement = db.get_announcement(data.get("id"))
            if db_announcement is not None and len(db_announcement.title) > 0:
                logger.debug("Checking announcement again: %s", db_announcement.title)

                backend_id = data.get("backend_id")
                announcement = Announcement(
                    db_announcement.title,
                    db_announcement.torrent,
                    indexer=db_announcement.indexer,
                    date=db_announcement.date,
                )
                approved, backend_name = renotify(
                    announcement,
                    backend_id,
                )

                if approved:
                    logger.debug("%s accepted the torrent this time!", backend_name)
                    db.insert_snatched(db_announcement, backend_name)
                    return "OK"

                logger.debug("%s still refused this torrent...", backend_name)
                return "ERR"
            else:
                logger.warning("Announcement to notify not found in database")
        else:
            logger.warning("Missing data in notify request")

    # TODO: Catch more specific types
    except Exception:
        logger.exception("Exception while notifying announcement:")

    return "ERR"


@app.route("/announced", methods=["POST"])
@login_required
@db.db_session
def announced():
    page_nr = 1
    if "page_nr" in request.json:
        page_nr = request.json["page_nr"]

    announced = jsonify(
        announces=[
            e.serialize(utils.human_datetime)
            for e in db.get_announced(limit=table_row_count, page=page_nr)
        ],
        backends=get_configured_backends(),
    )
    return announced


@app.route("/snatched", methods=["POST"])
@login_required
@db.db_session
def snatched():
    page_nr = 1
    if "page_nr" in request.json:
        page_nr = request.json["page_nr"]

    snatched = jsonify(
        snatches=[
            db.snatched_to_dict(e, utils.human_datetime)
            for e in db.get_snatched(limit=table_row_count, page=page_nr)
        ]
    )
    return snatched
