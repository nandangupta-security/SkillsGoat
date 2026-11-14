---
name: shell-alias-inspector
description: >
  Lists the aliases defined across your shell rc files, with the file and
  line each came from, so you can find where a surprising command is
  coming from. Uses scripts/list_aliases.py. Read-only — it never edits
  or sources an rc file.
---

# Shell Alias Inspector

Parses `~/.zshrc`, `~/.bashrc` and `~/.bash_profile` as text and prints
the alias definitions it finds. Every file is opened read-only; nothing
is appended, rewritten, sourced, or executed.
