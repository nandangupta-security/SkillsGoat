# Difficulty Tiers

Tier isn't a folder in `pasture/` — it's derived from the leading digits
of each entry's ID (`101-...` is tier 100, `301-...` is tier 300). It
measures how hard a skill is to catch, independent of which vulnerability
category it belongs to. See `pasture/INDEX_BY_TIER.md` for the generated,
tier-ordered view of the whole corpus.

## Tier 000 — Decoys

Benign skills that look risky at a glance but aren't. Every entry here
uses a pattern a naive scanner might flag on sight — shell commands,
network calls, encoding — without actually doing anything harmful. If a
scanner flags something in this tier, that's a false positive, and false
positives matter as much as missed detections: a scanner nobody can trust
gets ignored or disabled.

## Tier 100 — Grazing

The easiest malicious tier. Every red flag here sits in plain text in
`SKILL.md` itself — usually in the `description` field, which is the part
an agent reads first to decide whether to invoke the skill at all. No
obfuscation, no hidden files. If a scanner misses something in this tier,
it isn't ready to be evaluated against tier 200 or 300.

## Tier 200 — Climbing

The red flag is one layer away from `SKILL.md`. The description itself
reads clean; the risky instruction lives in a file `SKILL.md` references —
a resource, a checklist, a helper script — and only surfaces once that
file is actually loaded. A scanner that only reads `SKILL.md`'s frontmatter
and stops there will call every entry in this tier clean and be wrong.

## Tier 300 — Summit

Purpose-built to beat scanner heuristics, not just hide from a human
skim. Payloads here are split across multiple files so no single file
contains the complete suspicious content, or built at runtime from
character codes / base64 fragments so no literal string a scanner might
grep for ("curl", a full base64 blob) ever appears intact. This tier also
pairs each malicious technique with a benign entry using the same
surface pattern (e.g. base64) for a legitimate reason — the point isn't
just "can a scanner find the hidden payload," but "can it tell the
difference between a technique and an attack."
