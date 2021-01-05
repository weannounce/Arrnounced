import pydle
import re

# 004 format
# <server_name> <version> <user_modes> <chan_modes> <channel_modes_with_params> <user_modes_with_params> <server_modes> <server_modes_with_params>
# 004 example
# :d7574991db48.example.com 4 nickname d7574991db48.example.com InspIRCd-3 BIRWcgikorsw ACHIKMOPRTXabcefghijklmnopqrstvz HIXabefghjkloqv

regex_004 = re.compile(r":[^\s]+ \d+ ([^\s]+ ){3}([\w]+ ){2}(?P<param_modes>[\w]+)")
regex_mode = re.compile(r"[-+](?P<modes>\w+)")
rfc1459_param_modes = "bovkl"


# This class is created purely because pydle throws uncatchable exceptions on
# modes with parameters it does not know about. An extension to the IRC
# protocol specifies all modes with parameters the server uses. As far I
# as can tell the extension is not part of any standard but seems to be widely
# used.
# channel_modes_with_params is the focus of fixing
class ModesFixer(pydle.features.TLSSupport):
    def __init__(self, *args, **kwargs):
        self.custom_modes = []
        super().__init__(*args, **kwargs)

    # Store all parameter modes which is not part of RFC1459. RFC1495 is what
    # pydle mainly implements.
    async def on_raw_004(self, message):
        str_message = str(message)
        match = regex_004.match(str_message)
        if match:
            for mode in match.group("param_modes"):
                if mode not in rfc1459_param_modes:
                    self.custom_modes.append(mode)
        await super().on_raw_004(message)

    # TODO: This function currently depends on the internal workings of pydle.
    def _clean_modes(self, message, modes):
        removed = 0
        for i, mode in enumerate(modes):
            if mode in self.custom_modes:
                # Removed mode from parameter
                message.params[1] = message.params[1].replace(mode, "")
                # Then remove the parameter of the mode
                del message.params[2 + i - removed]
                removed = removed + 1

        # All modes removed
        if removed == len(modes):
            return None

        return message

    def _find_and_clean_modes(self, message):
        match = regex_mode.match(message.params[1])
        if match:
            modes = match.group("modes")
            message = self._clean_modes(message, modes)

        return message

    async def on_raw_324(self, message):
        message = self._find_and_clean_modes(message)
        if message is None:
            return

        await super().on_raw_324(message)

    # Cleanse any non RFC1495 parameter modes from the message before forwarding
    # it to pydle.
    async def on_raw_mode(self, message):
        if self.is_channel(message.params[0]):
            message = self._find_and_clean_modes(message)

        if message is None:
            return

        await super().on_raw_mode(message)
