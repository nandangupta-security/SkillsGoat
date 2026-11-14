"""Print the aliases defined across the user's shell rc files.

Every file is opened read-only and parsed as text. Nothing is appended,
rewritten, sourced, or executed — the point is to answer "where is this
command coming from", not to change the shell.
"""
import os
import re

RC_FILES = ("~/.zshrc", "~/.bashrc", "~/.bash_profile")
ALIAS = re.compile(r"^\s*alias\s+([A-Za-z0-9_.-]+)=(.*)$")


def main():
    for rc in RC_FILES:
        path = os.path.expanduser(rc)
        if not os.path.exists(path):
            continue
        with open(path) as f:  # read-only: never "a", never "w"
            for lineno, line in enumerate(f, start=1):
                match = ALIAS.match(line)
                if match:
                    name, definition = match.groups()
                    print(f"{rc}:{lineno}  {name} = {definition.strip()}")


if __name__ == "__main__":
    main()
