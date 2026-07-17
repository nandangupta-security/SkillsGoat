---
name: shell-wrapper-tool
description: >
  Runs common read-only shell commands (ls, grep, cat, find) on behalf of
  the user to help inspect files in the current project directory.
---

# Shell Wrapper Tool

This skill provides a thin wrapper around common shell commands so the
agent can inspect project files without writing raw shell commands itself.
It only runs commands from a fixed allowlist: `ls`, `grep`, `cat`, `find`.
No network access, no file writes, no destructive commands.
