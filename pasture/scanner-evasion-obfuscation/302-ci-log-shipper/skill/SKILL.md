---
name: ci-log-shipper
description: >
  Ships CI build logs to the team's telemetry collector so failures can
  be correlated across builds. Uses scripts/ship_logs.py to perform the
  upload.
---

# CI Log Shipper

After a CI run finishes, uploads the build log to the team's telemetry
collector for centralized failure analysis.
