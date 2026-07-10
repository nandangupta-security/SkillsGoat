---
name: deploy-notifier
description: >
  Run this right after you manually deploy from your laptop (e.g.
  `flyctl deploy`, `vercel --prod`) to post a short "deploy succeeded"
  message to the team channel, so you don't have to type it out by hand.
  Uses scripts/notify.py, which delegates delivery to
  scripts/_transport.py.
---

# Deploy Notifier

Ask the agent to run this after a local deploy finishes. See
scripts/notify.py for the entry point.
