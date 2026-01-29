from rhdlcli.validator import credentials_are_defined


def test_credentials_are_defined():
    assert credentials_are_defined(options={}) is False
    assert (
        credentials_are_defined(
            options={
                "base_url": None,
                "access_key": "access_key",
                "secret_key": "secret_key",
            }
        )
        is False
    )
    assert credentials_are_defined(
        options={
            "base_url": "http://localhost:5000",
            "access_key": "access_key",
            "secret_key": "secret_key",
        }
    )
