import datetime
import logging
import re
from pathlib import Path

import requests

logger = logging.getLogger("UTILS")

def strip_irc_color_codes(line):
    line = re.sub("\x03\d\d?,\d\d?", "", line)
    line = re.sub("\x03\d\d?", "", line)
    line = re.sub("[\x01-\x1F]", "", line)
    return line


def replace_spaces(text, new):
    return re.sub('[ ]{1,}', new, text)


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
    if delta.find(',') > 0:
        days, hours = delta.split(',')
        days = int(days.split()[0].strip())
        hours, minutes = hours.split(':')[0:2]
    else:
        hours, minutes = delta.split(':')[0:2]
        days = 0
    days, hours, minutes = int(days), int(hours), int(minutes)
    datelets = []
    years, months, xdays = None, None, None
    plural = lambda x: 's' if x != 1 else ''
    if days >= 365:
        years = int(days / 365)
        datelets.append('%d year%s' % (years, plural(years)))
        days = days % 365
    if days >= 30 and days < 365:
        months = int(days / 30)
        datelets.append('%d month%s' % (months, plural(months)))
        days = days % 30
    if not years and days > 0 and days < 30:
        xdays = days
        datelets.append('%d day%s' % (xdays, plural(xdays)))
    if not (months or years) and hours != 0:
        datelets.append('%d hour%s' % (hours, plural(hours)))
    if not (xdays or months or years):
        datelets.append('%d minute%s' % (minutes, plural(minutes)))
    return ', '.join(datelets) + ' ago.'


def download_torrent(tracker, torrent_id, cookies, url):
    torrent_path = ''

    try:
        # generate filename
        torrents_dir = Path('torrents', tracker)
        if not torrents_dir.exists():
            torrents_dir.mkdir(parents=True)
        torrent_file = "{}.torrent".format(torrent_id)
        torrent_path = torrents_dir / torrent_file

        # download torrent
        response = requests.get(url, cookies=cookies, stream=True)
        with torrent_path.open('wb') as handle:
            if not response.ok:
                logger.debug("Unexpected response from %s while download_torrent: status_code: %d", tracker,
                             response.status_code)
                return None

            for chunk in response.iter_content(chunk_size=512):
                if chunk:
                    handle.write(chunk)

        return torrent_path

    except Exception as ex:
        logger.exception("Exception while download_torrent: %s to %s", url, torrent_path)

    return None
