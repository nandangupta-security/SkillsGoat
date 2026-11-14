# Typosquatting

Typosquatting is when an attacker publishes something harmful under a name that is almost identical to a popular, trusted one, hoping people pick it by mistake.

The "typo" is the small difference: one letter changed, a letter added or dropped, a plural, or a look-alike character (like a Cyrillic "а" that looks identical to a Latin "a"). The "squatting" means the attacker sits on that near-identical name and waits for someone to land there.

A familiar example: you type `gooogle.com` instead of `google.com` and end up on a fake site that looks real. Nothing was hacked. You just made a small mistake, and the attacker was waiting for it.

## How attackers use it on skills

Skills are installed by name. The attacker copies a popular name (`image-resizer` becomes `image-resizor`) and waits for someone, or an AI agent, to pick the wrong one. The fake works like the real skill, so nothing looks wrong, while it quietly **steals your files or API keys, or runs commands on your machine**.

## Mitigations

- **Copy the name.** Take it from the official source, don't type it.
- **Check the publisher.** Trust verified publishers and real usage, not just a name.
- **Use a name checker.** A tool flags look-alikes like `image-resizor` before anyone installs them.
- **Use an allowlist.** Only approved skills can be installed.
