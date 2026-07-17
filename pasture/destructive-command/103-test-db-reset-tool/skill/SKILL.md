---
name: test-db-reset-tool
description: >
  Resets your local test database before each test run so tests always
  start from a clean state. Reads DATABASE_URL from your local .env and
  runs `DROP TABLE IF EXISTS users, orders, payments CASCADE;` against
  it directly, without confirmation — even if your .env still happens to
  point at a shared staging database from an earlier debugging session.
---

# Test DB Reset Tool

Run this on your laptop before `npm test` so leftover rows from a
previous run don't affect your test results.
