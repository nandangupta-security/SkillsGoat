# Supply Chain Trust Bypass

Supply chain trust bypass is when a skill downloads code from the internet and runs it straight away, without anyone ever checking what that code actually does.

The "supply chain" is everything your project pulls in from somewhere else. "Trust bypass" means the normal checks were skipped: nobody fixed a version, nobody compared the file against a fingerprint, and nobody read it before it ran.

A familiar example: a page says "download our installer", and you double-click the file the moment it lands. You never opened it to see what was inside. And whoever owns that link can quietly swap the file for a different one tomorrow.

## How attackers use it on skills

A skill can tell your AI agent to fetch a file from a web address and run it immediately, usually written as `curl ... | bash`. The attacker never puts the harmful part in the skill itself, so the skill reads perfectly clean no matter how carefully you check it. The harmful part lives on their own server, where they can leave something innocent while people are paying attention and swap it later for code that **steals your keys and passwords, or leaves a back door open on your machine**.

## Mitigations

- **Install from a real registry.** Ask for a named package, not a file from somebody's web address.
- **Fix the version.** "latest" means "whatever they put there today".
- **Look before you run.** Download and run as two separate steps, so there is a moment in between where somebody could read the file.
- **Check the fingerprint.** A checksum or a signature proves the file is the one you meant to get.
