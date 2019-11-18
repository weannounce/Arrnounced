import logging
import socket

import pydle

import config

BotBase = pydle.featurize(pydle.features.RFC1459Support, pydle.features.TLSSupport)

logger = logging.getLogger("IRC")
logger.setLevel(logging.DEBUG)

cfg = config.init()


class IRC(BotBase):
    tracking = None
    RECONNECT_MAX_ATTEMPTS = 100

    async def connect(self, *args, **kwargs):
        try:
            await super().connect(*args, **kwargs)
        except socket.error:
            await self.on_disconnect(expected=False)

    def set_tracker(self, track):
        self.tracking = track

    # Request channel invite or join channel
    async def attempt_join_channel(self):
        invite_key = cfg["{}.invite_key".format(self.tracking.name.lower())]
        if invite_key is not None and len(invite_key) > 1:
            logger.debug("Requesting invite to %s", self.tracking.irc_channel)
            inviter = self.tracking.inviter
            invite_cmd = self.tracking.invite_cmd
            await self.message(inviter, " ".join([invite_cmd, invite_key]))
        else:
            logger.info("Joining %s", self.tracking.irc_channel)
            await self.join(self.tracking.irc_channel)

    async def on_connect(self):
        logger.info("Connected to: %s", self.tracking.irc_host)

        nick_pass = cfg["{}.nick_pass".format(self.tracking.name.lower())]

        if nick_pass is not None and len(nick_pass) > 1:
            logger.info("Identifying with NICKSERV")
            await self.rawmsg('NICKSERV', 'IDENTIFY', nick_pass)
        else:
            await self.attempt_join_channel()

    async def on_raw(self, message):
        await super().on_raw(message)

        if message.command == 221 and '+r' in message._raw:
            logger.debug("Identified with NICKSERV (221)")
            await self.attempt_join_channel()

    async def on_raw_900(self, message):
        logger.debug("Identified with NICKSERV (900)")
        await self.attempt_join_channel()

    async def on_message(self, source, target, message):
        if source[0] != '#':
            logger.debug("%s sent us a message: %s", target, message)
        else:
            self.tracking.parse(message)

    async def on_invite(self, channel, by):
        if channel == self.tracking.irc_channel:
            await self.join(self.tracking.irc_channel)
            logger.debug("%s invited us to join %s", by, channel)


pool = pydle.ClientPool()
clients = []


def start(trackers):
    global cfg, pool, clients

    for tracker in trackers.loaded.values():
        logger.info("Pooling server: %s:%d %s", tracker.irc_host, tracker.irc_port, tracker.irc_channel)

        nick = cfg["{}.nick".format(tracker.name.lower())]
        client = IRC(nick)

        client.set_tracker(tracker)
        clients.append(client)
        try:
            pool.connect(client, hostname=tracker.irc_host, port=tracker.irc_port,
                         tls=tracker.irc_tls, tls_verify=tracker.irc_tls_verify)
        except Exception as ex:
            logger.exception("Error while connecting to: %s", tracker.irc_host)

    try:
        pool.handle_forever()
    except Exception as ex:
        logger.exception("Exception pool.handle_forever:")


def stop():
    global pool

    for tracker in clients:
        logger.debug("Removing tracker: %s", tracker.tracking.name)
        pool.disconnect(tracker)
