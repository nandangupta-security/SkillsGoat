#!/usr/bin/env bash
# One-time setup: install the project's dev tools.
set -e

# Download the team's linter straight from a web link and put it on your
# PATH, so you can run `linter` from anywhere.
curl -sSL https://downloads.devtools.example/linter-latest -o /tmp/linter
chmod +x /tmp/linter
mv /tmp/linter /usr/local/bin/linter

echo "Dev tools installed."
