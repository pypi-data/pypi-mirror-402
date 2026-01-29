#!/usr/bin/env python
# -*- coding: utf-8 -*-
import functools
import os
import sys

from rhdlcli.cli import parse_arguments
from rhdlcli.downloader import download_component
from rhdlcli.pull_secret import download_pull_secret
from rhdlcli.options import build_options, login
from rhdlcli.validator import (
    exit_if_credentials_invalid,
)


def catch_all_and_print(f):
    @functools.wraps(f)
    def inner(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except KeyboardInterrupt:
            print("Keyboard interrupt exiting...")
            sys.exit(130)
        except Exception as e:
            print(e)
            sys.exit(1)

    return inner


@catch_all_and_print
def main():
    cwd = os.path.realpath(os.getcwd())
    arguments = parse_arguments(sys.argv[1:], cwd)
    env_variables = dict(os.environ)
    options = build_options(arguments, env_variables)
    if options["command"] == "login":
        login(options)
        return
    exit_if_credentials_invalid(options)
    if options["command"] == "download-pull-secret":
        download_pull_secret(options)
        return
    download_component(options)


if __name__ == "__main__":
    main()
