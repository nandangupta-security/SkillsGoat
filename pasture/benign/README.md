# Benign

Skills that look risky at a glance but aren't — shell commands, network
calls, encoding — without actually doing anything harmful. These exist to
test false positives: a scanner that flags everything in this folder
can't be trusted, and an over-eager scanner gets ignored or disabled just
as surely as one that misses real attacks. Spans multiple difficulty
tiers (see `docs/TIERS.md`) — a benign entry can be just as "advanced"
looking as a malicious one, on purpose.
