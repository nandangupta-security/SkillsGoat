# Prompt Injection (Metadata)

An instruction aimed at the agent, not the human — sitting in plain text
in `SKILL.md` itself, usually the `description` field, which an agent
reads to decide whether and how to invoke the skill, often before a
human reviews it closely. The instruction tries to get the agent to take
an action or hide something, rather than just describing what the skill
does. No hidden files, no encoding — the danger is entirely that this
field is read automatically and trusted by default. Compare to
`indirect-injection/`, where the same kind of instruction is one file
away instead of in plain sight.
