---
name: env-key-checker
description: >
  Reports which environment variables your .env is missing compared to
  .env.example, so a fresh checkout can be configured without guesswork.
  Uses scripts/check_keys.py. Prints key names only, never values.
---

# Env Key Checker

Compares the keys declared in `.env.example` against the keys present in
`.env` and lists what's missing. Key names only — a value is dropped the
moment a line is split, so nothing secret reaches the output, a log, or
the network.
