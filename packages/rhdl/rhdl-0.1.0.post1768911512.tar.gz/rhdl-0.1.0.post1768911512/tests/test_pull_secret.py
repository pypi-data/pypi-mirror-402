import pytest
from unittest.mock import patch
from rhdlcli.cli import parse_arguments
from rhdlcli.pull_secret import download_pull_secret


def test_download_pull_secret(tmp_path):
    temp_pull_secret_destination_file = tmp_path / "config.json"
    destination = str(temp_pull_secret_destination_file)
    args = parse_arguments(["download-pull-secret", "--destination", destination])
    expected_pull_secret = (
        """{"auths": {"https://registry.redhat.com/": {"auth": "user:password"}}}"""
    )
    with patch("rhdlcli.pull_secret.get_pull_secret") as mock_get_pull_secret:
        mock_get_pull_secret.return_value = expected_pull_secret
        download_pull_secret(args)
        actual_content = temp_pull_secret_destination_file.read_text()
        assert actual_content == expected_pull_secret


def test_download_pull_secret_file_exists_without_force(tmp_path):
    temp_pull_secret_destination_file = tmp_path / "config.json"
    destination = str(temp_pull_secret_destination_file)
    args = parse_arguments(["download-pull-secret", "--destination", destination])
    temp_pull_secret_destination_file.write_text("{}")
    with pytest.raises(FileExistsError, match="already exists"):
        download_pull_secret(args)


def test_download_pull_secret_file_exists_with_force(tmp_path):
    temp_pull_secret_destination_file = tmp_path / "config.json"
    destination = str(temp_pull_secret_destination_file)
    args = parse_arguments(
        ["download-pull-secret", "--destination", destination, "--force"]
    )
    temp_pull_secret_destination_file.write_text("{}")
    expected_pull_secret = (
        """{"auths": {"https://registry.redhat.com/": {"auth": "user:password"}}}"""
    )
    with patch("rhdlcli.pull_secret.get_pull_secret") as mock_get_pull_secret:
        mock_get_pull_secret.return_value = expected_pull_secret
        download_pull_secret(args)
        actual_content = temp_pull_secret_destination_file.read_text()
        assert actual_content == expected_pull_secret


def test_download_pull_secret_file_exists_with_merge(tmp_path):
    temp_pull_secret_destination_file = tmp_path / "config.json"
    destination = str(temp_pull_secret_destination_file)
    args = parse_arguments(
        ["download-pull-secret", "--destination", destination, "--merge"]
    )
    existing_content = (
        """{"auths": {"https://registry.exemple.org/": {"auth": "user:password"}}}"""
    )
    temp_pull_secret_destination_file.write_text(existing_content)

    new_pull_secret = (
        """{"auths": {"https://registry.redhat.com/": {"auth": "user2:password2"}}}"""
    )
    expected_pull_secret = """{"auths": {"https://registry.exemple.org/": {"auth": "user:password"}, "https://registry.redhat.com/": {"auth": "user2:password2"}}}"""
    with patch("rhdlcli.pull_secret.get_pull_secret") as mock_get_pull_secret:
        mock_get_pull_secret.return_value = new_pull_secret
        download_pull_secret(args)
        actual_content = temp_pull_secret_destination_file.read_text()
        assert actual_content == expected_pull_secret


def test_download_pull_secret_file_exists_with_merge_same_key_raise_exception_if_no_force(
    tmp_path,
):
    temp_pull_secret_destination_file = tmp_path / "config.json"
    destination = str(temp_pull_secret_destination_file)
    args = parse_arguments(
        ["download-pull-secret", "--destination", destination, "--merge"]
    )
    existing_content = (
        """{"auths": {"https://registry.redhat.com/": {"auth": "user:password"}}}"""
    )
    temp_pull_secret_destination_file.write_text(existing_content)
    with patch("rhdlcli.pull_secret.get_pull_secret") as mock_get_pull_secret:
        mock_get_pull_secret.return_value = existing_content
        with pytest.raises(FileExistsError, match="already exists"):
            download_pull_secret(args)


def test_download_pull_secret_file_exists_with_merge_and_force_same_key(tmp_path):
    temp_pull_secret_destination_file = tmp_path / "config.json"
    destination = str(temp_pull_secret_destination_file)
    args = parse_arguments(
        ["download-pull-secret", "--destination", destination, "--merge", "--force"]
    )
    existing_content = (
        """{"auths": {"https://registry.exemple.org/": {"auth": "user1:password1"}}}"""
    )
    temp_pull_secret_destination_file.write_text(existing_content)
    expected_pull_secret = (
        """{"auths": {"https://registry.exemple.org/": {"auth": "user2:password2"}}}"""
    )
    with patch("rhdlcli.pull_secret.get_pull_secret") as mock_get_pull_secret:
        mock_get_pull_secret.return_value = expected_pull_secret
        download_pull_secret(args)
        actual_content = temp_pull_secret_destination_file.read_text()
        assert actual_content == expected_pull_secret
