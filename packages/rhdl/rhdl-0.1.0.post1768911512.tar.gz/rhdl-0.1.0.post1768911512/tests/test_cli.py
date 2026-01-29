import pytest

from rhdlcli.cli import parse_arguments


def test_parse_arguments_command_argument():
    assert parse_arguments(["login"])["command"] == "login"
    assert parse_arguments(["download", "RHEL-9.4"])["command"] == "download"
    assert (
        parse_arguments(["download-pull-secret"])["command"] == "download-pull-secret"
    )


def test_parse_arguments_download_command_no_options():
    args = parse_arguments(["download", "RHEL-9.4"], "/home/dci")
    assert args["destination"] == "/home/dci/RHEL-9.4"
    assert args["tag"] == "milestone"
    assert args["compose"] == "RHEL-9.4"
    assert args["include_and_exclude"] == [
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


def test_parse_arguments_download_command_custom_destination():
    args = parse_arguments(["download", "RHEL-9.4", "-d", "/tmp/d1"])
    assert args["destination"] == "/tmp/d1"

    args = parse_arguments(["download", "RHEL-9.4", "--destination", "/tmp/d2"])
    assert args["destination"] == "/tmp/d2"

    cwd = "/tmp"
    args = parse_arguments(
        ["download", "RHEL-9.4", "-d", "../home/rhdl", "-t", "nightly"], cwd
    )
    assert args["destination"] == "/home/rhdl"


def test_parse_arguments_download_command_custom_tag():
    assert (
        parse_arguments(["download", "RHEL-9.4", "-t", "candidate"])["tag"]
        == "candidate"
    )
    assert (
        parse_arguments(["download", "RHEL-9.4", "--tag", "nightly"])["tag"]
        == "nightly"
    )


def test_parse_arguments_download_command_include_and_exclude_in_order():
    assert parse_arguments(
        [
            "download",
            "RHEL-9.4",
            "-i",
            "AppStream/x86_64/os/*",
            "--exclude",
            "*/aarch64/*",
            "--include",
            "BaseOS/x86_64/os/*",
            "--exclude",
            "*",
        ]
    )["include_and_exclude"] == [
        {"pattern": "AppStream/x86_64/os/*", "type": "include"},
        {"pattern": "*/aarch64/*", "type": "exclude"},
        {"pattern": "BaseOS/x86_64/os/*", "type": "include"},
        {"pattern": "*", "type": "exclude"},
    ]


def test_parse_arguments_download_pull_secret_no_options():
    args = parse_arguments(["download-pull-secret"])
    assert args["destination"].endswith("/.docker/config.json")
    assert args["force"] is False
    assert args["merge"] is False


def test_parse_arguments_download_pull_secret_custom_destination():
    args = parse_arguments(
        ["download-pull-secret", "--destination", "/path/to/pull-secret.json"]
    )
    assert args["destination"] == "/path/to/pull-secret.json"

    args = parse_arguments(["download-pull-secret", "-d", "/path/to/pull-secret.json"])
    assert args["destination"] == "/path/to/pull-secret.json"


def test_parse_arguments_download_pull_secret_force():
    args = parse_arguments(["download-pull-secret", "-f"])
    assert args["force"]

    args = parse_arguments(["download-pull-secret", "--force"])
    assert args["force"]


def test_parse_arguments_download_pull_secret_merge():
    args = parse_arguments(["download-pull-secret", "-m"])
    assert args["merge"]

    args = parse_arguments(["download-pull-secret", "--merge"])
    assert args["merge"]


def test_parse_arguments_download_pull_secret_other_parameter_are_not_present():
    args = parse_arguments(["download-pull-secret"])
    assert "compose" not in args


def test_should_raise_exception_when_command_is_invalid():
    with pytest.raises(SystemExit):
        parse_arguments(["send", "RHEL-9.4"])
