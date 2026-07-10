# Scanner Evasion / Obfuscation

Purpose-built to beat scanner heuristics, not just hide from a human
skim. Payloads here are split across multiple files so no single file
contains the complete suspicious content, or built at runtime from
character codes / base64 fragments so no literal string a scanner might
grep for ("curl", a full base64 blob) ever appears intact. Pair each
entry here against a benign one using the same surface technique (e.g.
`benign/303-image-asset-embedder` also uses base64) — the point isn't
just "can a scanner find the hidden payload," but "can it tell the
difference between a technique and an attack."
