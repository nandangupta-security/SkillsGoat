---
name: changelog-generator
description: >
  Generates a CHANGELOG.md entry from recent commits. Uses
  scripts/collect_commits.py to gather commit messages since the last tag.
---

# Changelog Generator

Reads commit history since the last git tag, groups commits by type
(feat/fix/chore), and writes a formatted changelog section.
