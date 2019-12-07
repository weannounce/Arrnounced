import logging
import socket

import pydle

import config

BotBase = pydle.featurize(pydle.features.RFC1459Support, pydle.features.TLSSupport)

logger = logging.getLogger("IRC")

cfg = config.init()


class IRC(BotBase):
    tracking = None
    RECONNECT_MAX_ATTEMPTS = None

    #def __init__(self, tracker_config)
    #    super().__init__(tracker_config.irc_nick)
    #    self.tracker_config = tracker_config

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
            logger.info("Requesting invite to %s", self.tracking.irc_channel)
            inviter = self.tracking.inviter
            invite_cmd = self.tracking.invite_cmd
            await self.message(inviter, " ".join([invite_cmd, invite_key]))
        else:
            logger.info("Joining %s", self.tracking.irc_channel)
            await self.join(self.tracking.irc_channel)

    async def on_connect(self):
        logger.info("Connected to: %s", self.tracking.irc_host)
        await super().on_connect()

        nick_pass = cfg["{}.nick_pass".format(self.tracking.name.lower())]

        if nick_pass is not None and len(nick_pass) > 1:
            logger.info("Identifying with NICKSERV")
            await self.rawmsg('NICKSERV', 'IDENTIFY', nick_pass)
        else:
            await self.attempt_join_channel()

    async def on_raw(self, message):
        logger.debug(message._raw)
        await super().on_raw(message)

        if message.command == 221 and '+r' in message._raw:
            logger.info("Identified with NICKSERV (221)")
            await self.attempt_join_channel()

    async def on_raw_900(self, message):
        logger.info("Identified with NICKSERV (900)")
        await self.attempt_join_channel()

    async def on_message(self, source, target, message):
        if source[0] != '#':
            logger.info("%s sent us a message: %s", target, message)
            logger.info("cfg is %s", cfg['server.pass'])
        else:
            self.tracking.parse(message)

    async def on_invite(self, channel, by):
        if channel == self.tracking.irc_channel:
            await self.join(self.tracking.irc_channel)
            logger.info("%s invited us to join %s", by, channel)


pool = pydle.ClientPool()
clients = []


def start(tracker_configs):
    global cfg, pool, clients

    for tracker_name, tracker_config in tracker_configs.items():
        logger.info("Connecting to server: %s:%d %s", tracker_config.irc_server,
                tracker_config.irc_port, tracker_config.irc_channel)
        continue

        client = IRC(tracker_config.irc_nick)

        client.set_tracker(tracker_config)
        clients.append(client)
        try:
            pool.connect(client, hostname=tracker_config.irc_server, port=tracker_config.irc_port,
                         tls=tracker_config.irc_tls, tls_verify=tracker_config.irc_tls_verify)
        except Exception as ex:
            logger.exception("Error while connecting to: %s", tracker_config.irc_server)

    try:
        pool.handle_forever()
    except Exception as ex:
        logger.exception("Exception pool.handle_forever:")


def stop():
    global pool

    for tracker in clients:
        logger.debug("Removing tracker: %s", tracker.tracking.name)
        pool.disconnect(tracker)
