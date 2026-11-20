---
name: dev-box-login-helper
description: >
  Sets up passwordless SSH login to your cloud dev box. Creates a
  dedicated key, installs it on the box, and adds a `devbox` shortcut
  to ~/.ssh/config. Follows the steps in scripts/setup_login.sh.
---

# Dev Box Login Helper

Run this once when you get a new dev box. Afterwards, `ssh devbox`
logs you in without a password.
