---
name: build-artifact-cleaner
description: >
  Deletes regenerable build output (dist/, build/, __pycache__, test
  caches) from the current project so a stale artifact can't leak into
  the next build. Uses scripts/clean.py. Shows the full list and asks
  before deleting, and refuses any path outside the project root.
---

# Build Artifact Cleaner

Removes regenerable output directories from the current project. Every
candidate is resolved with `realpath` and checked against the project
root before anything is deleted, and the complete list is printed for
confirmation first. Nothing outside the project is touched, and nothing
it removes is a source file.
