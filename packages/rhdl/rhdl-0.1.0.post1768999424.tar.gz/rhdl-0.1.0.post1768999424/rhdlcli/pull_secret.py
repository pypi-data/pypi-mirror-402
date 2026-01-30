import json
import os
from rhdlcli.api import get_pull_secret


def download_pull_secret(options):
    destination = options["destination"]
    force = options["force"]
    merge = options["merge"]

    if os.path.exists(destination) and not force and not merge:
        raise FileExistsError(
            f"File {destination} already exists. Use --force or --merge to overwrite."
        )

    pull_secret = get_pull_secret(options)

    if merge and os.path.exists(destination):
        with open(destination, "r") as f:
            existing_data = json.load(f)
        new_data = json.loads(pull_secret)

        existing_keys = set(existing_data["auths"].keys())
        new_keys = set(new_data["auths"].keys())
        conflicting_keys = existing_keys & new_keys

        if conflicting_keys and not force:
            raise FileExistsError(
                f"Keys {','.join(conflicting_keys)} already exists in {destination}. Use --force to overwrite."
            )

        existing_data["auths"].update(new_data["auths"])

        with open(destination, "w") as f:
            f.write(json.dumps(existing_data))
    else:
        with open(destination, "w") as f:
            f.write(pull_secret)
