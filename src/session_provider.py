from aiohttp import ClientSession, ClientError, ContentTypeError
import logging

logger = logging.getLogger("SESSION")


class SessionProvider:
    session = None

    @classmethod
    def get_session(cls):
        if not cls.session:
            cls.session = ClientSession(raise_for_status=True)
        return cls.session

    @classmethod
    async def close_session(cls):
        if cls.session:
            await cls.session.close()

    @staticmethod
    async def post(url, headers, json):
        try:
            async with SessionProvider.get_session().post(
                url,
                headers=headers,
                json=json,
            ) as http_response:
                return await http_response.json()
        except OSError:
            logger.exception("OS error when pushing release to %s", url)
        except ContentTypeError:
            logger.exception("Invalid JSON response from %s", url)
        except ClientError:
            logger.exception("Client error pushing release to %s", url)

        return None
