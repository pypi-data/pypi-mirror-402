#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys


def credentials_are_defined(options):
    required_keys = ["base_url", "access_key", "secret_key"]
    return all(key in options and options[key] is not None for key in required_keys)


def exit_if_credentials_invalid(options):
    if not credentials_are_defined(options):
        print("Credentials are invalid. Run `rhdl login` or set env variables.")
        sys.exit(1)
