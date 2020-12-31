# Arrnounced
Notify Sonarr/Radarr/Lidarr of tracker IRC announcements.

Built on the work of
[sonarrAnnounced](https://github.com/l3uddz/sonarrAnnounced) with tracker
configuration from
[autodl-trackers](https://github.com/autodl-community/autodl-trackers) (used by
[autodl-irssi](https://github.com/autodl-community/autodl-irssi))

## Features
* All trackers from
[autodl-trackers](https://github.com/autodl-community/autodl-trackers/tree/master/trackers)
are supported.
* Web UI to list announcements and accepted notifications
    * Ability to search among the announcements remains to be implemented though
* Notify based on announcement category
* Configurable delay between IRC announcement and notification

Only a few of the supported trackers are tested at the moment. Please report any issues you find.

# Setup

_Release v0.7 updated the configuration format. See the [release
notes](https://github.com/weannounce/arrnounced/releases/tag/v0.7) for more
information._

Docker or Python >=3.6 is required to run Arrnounced.

## Configuration
The default configuration path is `~/.arrnounced/settings.toml`.
[example.cfg](https://github.com/weannounce/arrnounced/blob/master/example.cfg)
is the acting configuration documentation.

The default XML tracker configuration path is `~/.arrnounced/autodl-trackers/trackers`

## Installation

### Docker
[Arrnounced on dockerhub](https://hub.docker.com/r/weannounce/arrnounced)

* You must provide `settings.toml` in `/config`. This is also where logs and the database will be stored.
* To access the web UI using bridged network the webui host in settings.toml must be `0.0.0.0`.
* As Arrnounced runs as a non-root user by default it is recommended to specify your own user to handle write access to `/config`.

```bash
# Default example
docker run -v /path/to/settings:/config \
           --user 1000 \
           -p 3467:3467 weannounce/arrnounced:latest
```

The docker image comes with a snapshot of XML tracker configurations located under `/trackers`. If you prefer your own version you can mount over it.

```bash
# Example with custom XML tracker configs and verbose logging
docker run -v /path/to/settings:/config \
           -v /path/to/autodl-trackers/trackers:/trackers \
           -e VERBOSE=Y \
           --user 1000 \
           -p 3467:3467 weannounce/arrnounced:latest
```

### Manual
1. `mkdir ~/.arrnounced`
2. `git clone https://github.com/autodl-community/autodl-trackers.git ~/.arrnounced/`
3. Create `~/.arrnounced/settings.toml` with
   [example.cfg](https://github.com/weannounce/arrnounced/blob/master/example.cfg)
   as guide and your [choice of
   trackers](https://github.com/autodl-community/autodl-trackers/tree/master/trackers)
4. `git clone https://github.com/weannounce/arrnounced.git` in you location of choice
5. Inside arrnounced directory: `pip install --user -r requirements.txt`.
   Preferably do this in a [virtual
   environment](https://docs.python.org/3/tutorial/venv.html) as to not end up
   with dependency conflicts.

Start with `<path to arrnounced>/src/arrnounced.py`.

Configuration files path as well as log and database location may be changed with command line arguments.

## Database design update
The database design was updated in [v0.3](https://github.com/weannounce/arrnounced/releases/tag/v0.3)
([ef931ee](https://github.com/weannounce/arrnounced/commit/ef931eef27348f82254d601f96d094a7b9f147bb)).
If you used Arrnounced prior to this or used its predecessor you have two options.
* Convert your old database using [convert_db.py](https://github.com/weannounce/arrnounced/blob/master/convert_db.py)
* Move the old database file for safe keeping and let Arrnounced create a new file.

The default path to the database is `~/.arrnounced/brain.db`
