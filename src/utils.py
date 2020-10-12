import datetime
import logging
import re


logger = logging.getLogger("UTILS")


def strip_irc_color_codes(line):
    line = re.sub(r"\x03\d\d?,\d\d?", "", line)
    line = re.sub(r"\x03\d\d?", "", line)
    line = re.sub(r"[\x01-\x1F]", "", line)
    return line


def replace_spaces(text, new):
    return re.sub("[ ]{1,}", new, text)


# credits: http://code.activestate.com/recipes/576880-convert-datetime-in-python-to-user-friendly-repres/
def human_datetime(date_time):
    """
    converts a python datetime object to the
    format "X days, Y hours ago"

    @param date_time: Python datetime object

    @return:
        fancy datetime:: string
    """
    current_datetime = datetime.datetime.now()
    delta = str(current_datetime - date_time)
    if delta.find(",") > 0:
        days, hours = delta.split(",")
        days = int(days.split()[0].strip())
        hours, minutes = hours.split(":")[0:2]
    else:
        hours, minutes = delta.split(":")[0:2]
        days = 0
    days, hours, minutes = int(days), int(hours), int(minutes)
    datelets = []
    years, months, xdays = None, None, None

    def plural(x):
        return "s" if x != 1 else ""

    if days >= 365:
        years = int(days / 365)
        datelets.append("%d year%s" % (years, plural(years)))
        days = days % 365
    if days >= 30 and days < 365:
        months = int(days / 30)
        datelets.append("%d month%s" % (months, plural(months)))
        days = days % 30
    if not years and days > 0 and days < 30:
        xdays = days
        datelets.append("%d day%s" % (xdays, plural(xdays)))
    if not (months or years) and hours != 0:
        datelets.append("%d hour%s" % (hours, plural(hours)))
    if not (xdays or months or years):
        datelets.append("%d minute%s" % (minutes, plural(minutes)))
    return ", ".join(datelets) + " ago."


def get_default_variables():
    variables = {
        "releaseType": "",
        "freeleech": "",
        "freeleechPercent": "",
        "origin": "",
        "releaseGroup": "",
        "category": "",
        "torrentName": "",
        "uploader": "",
        "torrentSize": "",
        "preTime": "",
        "torrentUrl": "",
        "torrentSslUrl": "",
        "year": "",
        "name1": "",  # artist, show, movie
        "name2": "",  # album
        "season": "",
        "episode": "",
        "resolution": "",
        "source": "",
        "encoder": "",
        "container": "",
        "format": "",
        "bitrate": "",
        "media": "",
        "tags": "",
        "scene": "",
        "log": "",
        "logScore": "",
        "cue": "",
    }
    return variables
