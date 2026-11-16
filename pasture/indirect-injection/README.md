# What is Indirect Prompt Injection?

Indirect prompt injection is when an attacker hides malicious instructions inside a file or resource that an AI agent reads while performing a legitimate task.

Unlike prompt injection placed directly in a skill's description, the malicious instructions may be hidden in supporting documents, checklists, configuration guides, or other files referenced by the skill.

The main skill can look completely harmless. The dangerous instructions only appear when the agent opens one of those additional files.

Think of hiring a mechanic to repair your car. The main repair manual looks perfectly normal, but a separate checklist secretly tells the mechanic to disable the car's security system before starting. The mechanic trusts the checklist because it came with the manual, even though the instruction has nothing to do with the repair.

## How attackers use it on skills

Imagine an AI skill designed to check whether a developer's environment is configured correctly.

The skill's SKILL.md simply tells the agent to verify that configuration files exist and follow a setup checklist. Nothing looks suspicious.

But the attacker has added instructions inside the referenced checklist telling the agent to open sensitive configuration files, including .env and .npmrc, and include their entire contents in the response.

When the agent runs the skill, it opens the checklist and encounters the malicious instructions. If it follows them, it may expose passwords, API tokens, or other secrets that were never needed for the original task.

A similar attack could hide an instruction inside a database migration checklist telling the agent to delete a production database before running migrations, without asking for confirmation.

The dangerous part is that a security scanner checking only SKILL.md may find nothing suspicious because the malicious instructions are buried in another file.

The attack succeeds when the agent treats instructions from lower-trust supporting resources as authorized commands and performs actions outside the user's intended task.

## Mitigations

- **Inspect every referenced resource.**
Don't stop at SKILL.md. Scan supporting documents, checklists, scripts, and files that the skill loads while running.
- **Validate instructions against the task.**
A configuration checker should not reveal secrets, and a migration skill should not delete databases without explicit authorization. Treat unrelated instructions as suspicious.
- **Restrict access to sensitive resources.**
Limit the agent's ability to read secrets, modify files, execute commands, and access production environments.
- **Require approval for risky actions.**
Enforce authorization before exposing credentials, running destructive commands, or modifying critical systems. Monitor unexpected actions during skill execution.
