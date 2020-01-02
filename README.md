# Arrnounced

Notify Sonarr/Radarr/Lidarr of tracker IRC announcements.

Built on the work of [sonarrAnnounced](https://github.com/l3uddz/sonarrAnnounced) with tracker configuration from [autodl-trackers](https://github.com/autodl-community/autodl-trackers) (used by [autodl-irssi](https://github.com/autodl-community/autodl-irssi))

## Requirements
1. Python 3.5.2 or newer. Only tested with 3.8 though.
2. requirements.txt modules

## Supported Trackers
All single line pattern trackers from [this repository](https://github.com/autodl-community/autodl-trackers/tree/master/trackers) are supported.

However, only a few of them are tested at the moment. There are likely issues. Feel free to report them.

[Multiline patterns](https://github.com/autodl-community/autodl-trackers/blob/cf392143eff916971d0627aa5827e4bc28bf8aad/trackers/AceHD.tracker#L47) are not supported yet.

# Installation

## Manual

1. `git clone https://github.com/weannounce/arrnounced.git`
2. `cd arrnounced`
3. `pip install --user -r requirements.txt`
4. `git clone https://github.com/autodl-community/autodl-trackers.git`
5. Create settings.cfg with example.cfg as guide and your [choice of trackers](https://github.com/autodl-community/autodl-trackers/tree/master/trackers)

Start with `./arrnounced.py`. Configuration files path as well as log and database location may be changed with command line arguments.

## Docker
TBA
