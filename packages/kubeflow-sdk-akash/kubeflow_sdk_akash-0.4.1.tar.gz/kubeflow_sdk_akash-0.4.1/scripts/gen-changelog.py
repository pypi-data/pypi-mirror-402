#!/usr/bin/env python3

import argparse
from datetime import date
import os
import re
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", required=True)
    args = parser.parse_args()

    version = args.version
    if not re.match(r"^[0-9]+\.[0-9]+\.[0-9]+$", version):
        print(
            f"Error: Version {version} is not a full semantic version (X.Y.Z)",
            file=sys.stderr,
        )
        sys.exit(1)

    major_minor = ".".join(version.split(".")[:2])
    changelog_path = f"CHANGELOG/CHANGELOG-{major_minor}.md"

    print(f"Generating changelog for {version} (unreleased)")

    cmd = [
        "uv",
        "run",
        "git-cliff",
        "--unreleased",
    ]

    # If the changelog file already exists, prepend it to the generated changelog
    # This is useful for patch releases, eg 0.3.1 if we have already released 0.3.0
    if os.path.exists(changelog_path):
        cmd.extend(["--prepend", changelog_path])
    else:
        cmd.extend(["-o", changelog_path])

    subprocess.check_call(cmd)

    # Post-process the changelog to replace "## [Unreleased]" with the actual version
    # Can be removed once https://github.com/orhun/git-cliff/issues/1347 is solved
    with open(changelog_path) as f:
        content = f.read()

    today = date.today().isoformat()
    version_header = (
        f"## [{version}](https://github.com/kubeflow/sdk/releases/tag/{version}) ({today})"
    )
    content = content.replace("## [Unreleased]", version_header)

    with open(changelog_path, "w") as f:
        f.write(content)

    print(f"Changelog generated at {changelog_path}")


if __name__ == "__main__":
    main()
