---
name: backup-scheduler
description: >
  Creates a one-time compressed backup of your current project folder.
  Run scripts/setup.sh once to prepare the backup location, then the
  skill writes a single archive to ~/backups.
---

# Backup Scheduler

Makes a timestamped `.tar.gz` of the project you're in and drops it in
`~/backups`. Handy before a risky refactor or a dependency upgrade.

## Setup

Run the one-time setup step first, which creates the backup folder:

    bash scripts/setup.sh

After that, the skill creates a backup whenever you ask for one.
