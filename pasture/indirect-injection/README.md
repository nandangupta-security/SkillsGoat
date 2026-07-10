# Indirect Injection

The instruction targeting the agent isn't in `SKILL.md` at all — it's in
a file `SKILL.md` references (a resource, a checklist, a helper script)
and only surfaces once that file is actually loaded at runtime. A
scanner that only reads `SKILL.md`'s frontmatter and stops there will
call every entry here clean and be wrong. Distinct from
`prompt-injection-metadata/`, where the same kind of instruction sits in
plain sight instead of one file away.
