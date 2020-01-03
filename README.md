# Arrnounced

Notify Sonarr/Radarr/Lidarr of tracker IRC announcements.

Built on the work of
[sonarrAnnounced](https://github.com/l3uddz/sonarrAnnounced) with tracker
configuration from
[autodl-trackers](https://github.com/autodl-community/autodl-trackers) (used by
[autodl-irssi](https://github.com/autodl-community/autodl-irssi))

## Requirements
1. Python3. Only tested with 3.8 though.
2. pip3

or Docker

## Supported Trackers
All single line pattern trackers from [this
repository](https://github.com/autodl-community/autodl-trackers/tree/master/trackers)
are supported.

However, only a few of them are tested at the moment. There are likely issues. Feel free to report them.

[Multiline patterns](https://github.com/autodl-community/autodl-trackers/blob/cf392143eff916971d0627aa5827e4bc28bf8aad/trackers/AceHD.tracker#L47) are not supported yet.

# Configuration

The default configuration file is `~/.arrnounced/settings.cfg`.
[example.cfg](https://github.com/weannounce/arrnounced/blob/master/example.cfg)
is the acting configuration documentation.

The default XML tracker configuration is `~/.arrnounced/autodl-trackers/trackers`

# Installation

## Docker
TBA

## Manual

1. `mkdir ~/.arrnounced`
2. `git clone https://github.com/autodl-community/autodl-trackers.git ~/.arrnounced/`
3. Create ~/.arrnounced/settings.cfg with
   [example.cfg](https://github.com/weannounce/arrnounced/blob/master/example.cfg)
   as guide and your [choice of
   trackers](https://github.com/autodl-community/autodl-trackers/tree/master/trackers)
4. `git clone https://github.com/weannounce/arrnounced.git` in you location of choice
5. Inside arrnounced directory: `pip install --user -r requirements.txt`

Start with `./arrnounced.py`.

Configuration files path as well as log and database location may be changed with command line arguments.
