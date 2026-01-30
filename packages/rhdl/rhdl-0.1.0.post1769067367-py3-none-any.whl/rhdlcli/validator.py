#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys


def credentials_are_defined(options):
    required_keys = ["base_url", "access_key", "secret_key"]
    return all(key in options and options[key] is not None for key in required_keys)


def exit_if_credentials_invalid(options):
    if not credentials_are_defined(options):
        print("Credentials are invalid. Run `rhdl login` or set env variables.")
        sys.exit(1)


def destination_folder_exists(options):
    destination = options["destination"]
    if destination and os.path.exists(destination):
        return True
    return False


def exit_if_destination_exists(options):
    if destination_folder_exists(options) and not options["force"]:
        destination = options["destination"]
        print(
            f"Error: Destination folder already exists: {destination}\n"
            f"Use --force to overwrite the existing folder."
        )
        sys.exit(1)
