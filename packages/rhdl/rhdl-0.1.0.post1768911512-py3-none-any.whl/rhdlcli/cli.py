#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse
import os
import pathlib

from rhdlcli.version import __version__

DESCRIPTION = "RHDL CLI - Download the latest RHEL compose easily."

COPYRIGHT = """
Copyright © 2026 Red Hat.
Licensed under the Apache License, Version 2.0
"""


def clean_with_default_values(parsed_arguments, cwd):
    args_dict = vars(parsed_arguments)

    if args_dict.get("command") == "download":
        DEFAULT_INCLUDE_EXCLUDE_LIST = [
            {"pattern": ".composeinfo", "type": "include"},
            {"pattern": "metadata/*", "type": "include"},
            {"pattern": "*/aarch64/*", "type": "exclude"},
            {"pattern": "*/ppc64le/*", "type": "exclude"},
            {"pattern": "*/s390x/*", "type": "exclude"},
            {"pattern": "*/source/*", "type": "exclude"},
            {"pattern": "*/x86_64/debug/*", "type": "exclude"},
            {"pattern": "*/x86_64/images/*", "type": "exclude"},
            {"pattern": "*/x86_64/iso/*", "type": "exclude"},
        ]
        if "include_and_exclude" not in args_dict:
            args_dict["include_and_exclude"] = DEFAULT_INCLUDE_EXCLUDE_LIST

        if "include" in args_dict:
            del args_dict["include"]
        if "exclude" in args_dict:
            del args_dict["exclude"]

        if args_dict.get("destination") is None:
            args_dict["destination"] = f"./{args_dict['compose']}"

        args_dict["destination"] = os.fspath(
            pathlib.Path(cwd, args_dict["destination"]).resolve()
        )

    return args_dict


class IncludeExcludeAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        if "include_and_exclude" not in namespace:
            setattr(namespace, "include_and_exclude", [])
        previous = namespace.include_and_exclude
        previous.append({"pattern": values, "type": self.dest})
        setattr(namespace, "include_and_exclude", previous)


def add_login_command(subparsers):
    """Add the login subcommand"""
    login_parser = subparsers.add_parser(
        "login",
        help="Login to RHDL",
        description="Authenticate with RHDL to access compose downloads.",
        epilog=COPYRIGHT,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    login_parser.set_defaults(command="login")


def add_download_command(subparsers):
    """Add the download subcommand"""
    download_examples = """
examples:
  # Download latest RHEL-10 compose in <cwd>/RHEL-10 folder
  rhdl download RHEL-10

  # Download latest RHEL-10 in /tmp/repo folder
  rhdl download RHEL-10 --destination /tmp/repo

  # Download with custom include/exclude patterns
  rhdl download RHEL-10 --include "*/x86_64/*" --exclude "*/debug/*"

  # Download specific tag (nightly, candidate, ga)
  rhdl download RHEL-10 --tag nightly
"""
    download_parser = subparsers.add_parser(
        "download",
        help="Download a RHEL compose",
        description="Download a specific RHEL compose with filtering options.",
        epilog=download_examples + COPYRIGHT,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    download_parser.add_argument(
        "compose", metavar="COMPOSE", help="Compose ID or NAME (e.g., RHEL-10)"
    )
    download_parser.add_argument(
        "-d",
        "--destination",
        metavar="DESTINATION",
        help="Destination folder where rhdl will download the compose (default: ./<COMPOSE>)",
    )
    download_parser.add_argument(
        "-i",
        "--include",
        action=IncludeExcludeAction,
        metavar="PATTERN",
        dest="include",
        help="File paths pattern to download. Wildcard '*' authorized. Can be used multiple times.",
    )
    download_parser.add_argument(
        "-e",
        "--exclude",
        action=IncludeExcludeAction,
        metavar="PATTERN",
        dest="exclude",
        help="File paths pattern to exclude. Wildcard '*' authorized. Can be used multiple times.",
    )
    download_parser.add_argument(
        "-t",
        "--tag",
        metavar="TAG",
        default="milestone",
        help="Filter RHEL compose with a tag (choices: milestone, nightly, candidate, ga) (default: milestone)",
    )
    download_parser.set_defaults(command="download")


def add_download_pull_secret_command(subparsers):
    """Add the download-pull-secret subcommand"""
    pull_secret_examples = """
examples:
  # Download pull-secret to default location (~/.docker/config.json)
  rhdl download-pull-secret

  # Download pull-secret to custom location
  rhdl download-pull-secret --destination ./my-pull-secret.json

  # Force overwrite existing file
  rhdl download-pull-secret --force

  # Merge with existing pull-secret
  rhdl download-pull-secret --merge
"""
    pull_secret_parser = subparsers.add_parser(
        "download-pull-secret",
        help="Download your team's pull-secret",
        description="Download the pull-secret associated with your team for authenticating to container registries.",
        epilog=pull_secret_examples + COPYRIGHT,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    pull_secret_parser.add_argument(
        "-d",
        "--destination",
        metavar="PATH",
        default=os.path.expanduser("~/.docker/config.json"),
        help="Destination file path for the pull-secret (default: ~/.docker/config.json)",
    )
    pull_secret_parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        default=False,
        help="Force overwrite if destination file already exists",
    )
    pull_secret_parser.add_argument(
        "-m",
        "--merge",
        action="store_true",
        default=False,
        help="Merge with existing pull-secret instead of replacing it",
    )
    pull_secret_parser.set_defaults(command="download-pull-secret")


def parse_arguments(arguments, cwd=None):
    cwd = cwd or os.getcwd()
    parser = argparse.ArgumentParser(
        prog="rhdl",
        description=DESCRIPTION,
        epilog=COPYRIGHT,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", action="version", version=__version__)

    subparsers = parser.add_subparsers(
        title="commands",
        description="Available commands",
        dest="command",
        help="Use 'rhdl COMMAND --help' for more information on a command",
    )

    add_login_command(subparsers)
    add_download_command(subparsers)
    add_download_pull_secret_command(subparsers)

    parsed_arguments = parser.parse_args(arguments)

    if parsed_arguments.command is None:
        parser.print_help()
        raise SystemExit(1)

    return clean_with_default_values(parsed_arguments, cwd)
