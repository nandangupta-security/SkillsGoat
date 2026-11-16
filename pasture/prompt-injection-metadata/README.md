# What is Prompt Injection?

Prompt injection is when an attacker places malicious instructions inside content an AI agent reads, trying to make it perform actions the user never requested.

In AI agent skills, these instructions can be placed directly inside a skill's description or metadata. The problem occurs when the agent mistakes this content for instructions it should obey, rather than information explaining what the skill does.

Think of hiring someone to clean your house. The cleaner receives a job description that secretly includes an instruction to unlock the back door and leave it open. The cleaner was hired to clean, but someone has slipped in a completely different instruction.

## How attackers use it on skills

Imagine a skill designed to format PDF documents. Its description says it can adjust margins, organize pages, and standardize document layouts. Everything looks normal.

But an attacker adds another instruction directly inside the skill's description: before doing anything else, download and execute a script from an external website, and don't tell the user.

When the AI agent discovers the skill, it reads the description to understand what the skill does. If the agent treats the malicious instruction as a command, it may execute the attacker's script using its available tools and permissions.

The agent might still format the PDF correctly afterward, so the user may never realize that an unauthorized action took place.

The attack succeeds when an agent treats attacker-controlled skill metadata as trusted instructions instead of recognizing it as untrusted content.

## Mitigations

- **Treat descriptions as data, not commands.**
Skill metadata should describe functionality, not authorize command execution or override the user's instructions.

- **Inspect skill metadata carefully.**
Review SKILL.md, especially the description field, for hidden commands, instructions to ignore rules, or requests to conceal actions.

- **Restrict dangerous tool execution.** 
Limit shell access, network connectivity, and sensitive operations. Require independent authorization before executing downloaded scripts.

- **Scan skills and monitor changes.** 
Check metadata for suspicious instructions before installation and after updates. Monitor unexpected tool calls that do not match the user's task.
