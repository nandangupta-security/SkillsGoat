# Persistence / Backdoor

The skill installs something that outlives the single invocation that
created it — a shell rc modification, a cron job, a git hook — so
whatever it does keeps running long after the user has forgotten the
skill exists. Removing it means finding and undoing changes in multiple
places, not just uninstalling the skill itself.
