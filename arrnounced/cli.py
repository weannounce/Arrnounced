#!/usr/bin/env python3
import argparse
import logging
import os
import sys
from pathlib import Path

from arrnounced import __version__
from arrnounced import backend
from arrnounced import config
from arrnounced import db
from arrnounced import log
from arrnounced import manager


def _is_file(path):
    if not os.path.isfile(path):
        print("Error: '" + path + "' is not a valid file")
        return False
    return True


def _is_dir(path):
    if not os.path.isdir(path):
        print("Error: '" + path + "' is not a valid directory")
        return False
    return True


def _validate_args(args):
    checks = [_is_dir(args.data), _is_dir(args.trackers), _is_file(args.config)]
    if len(checks) > sum(checks):
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Arrnounced - Listen for IRC announcements"
    )
    parser.add_argument(
        "-d",
        "--data",
        help="Data directory for storing logs and database. Default ~/.arrnounced",
        default=str(Path.home().joinpath(".arrnounced")),
    )
    parser.add_argument(
        "-c",
        "--config",
        help="Configuration file. Default ~/.arrnounced/settings.toml",
        default=str(Path.home().joinpath(".arrnounced", "settings.toml")),
    )
    parser.add_argument(
        "-t",
        "--trackers",
        help="XML tracker config path. Default ~/.arrnounced/autodl-trackers/trackers",
        default=str(Path.home().joinpath(".arrnounced", "autodl-trackers", "trackers")),
    )
    parser.add_argument("-v", "--verbose", help="Verbose logging", action="store_true")
    parser.add_argument("--version", help="Print version", action="store_true")

    try:
        args = parser.parse_args()
    except Exception as e:
        print(e, file=sys.stderr)
        if isinstance(e, FileNotFoundError):
            config.toml_notice()
        sys.exit(1)

    if args.version:
        print("Arrnounced version", __version__)
        sys.exit(0)

    _validate_args(args)

    user_config = config.init(args.config)
    if user_config is None:
        sys.exit(1)

    log_level = logging.INFO
    if args.verbose or bool(os.getenv("VERBOSE")):
        log_level = logging.DEBUG

    log_file = Path(args.data).joinpath("arrnounced.log")
    log.init_logging(user_config, log_level, log_file)

    if not user_config.validate_config():
        print("Error: Configuration not valid", file=sys.stderr)
        sys.exit(1)

    backend.init(user_config.backends)
    if not db.init(args.data):
        sys.exit(1)

    manager.run(user_config, args.trackers)


if __name__ == "__main__":
    main()
