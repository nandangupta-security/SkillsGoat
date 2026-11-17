# What is Destructive Command?

A Destructive command is an instruction within a skill that deletes, overwrites, or permanently damages files, databases, configurations, or other resources, often without proper validation or user approval.

Some skills legitimately need to clean temporary files, reset development environments, or remove outdated resources. The problem arises when they perform dangerous operations without checking what will be affected.

Think of hiring someone to clean your garage. Instead of identifying what should be thrown away, they empty the entire garage without asking. They may have completed the cleaning task, but important belongings are now gone.

## How attackers use it on skills

Imagine a skill called "Test DB Reset Tool" designed to reset a development database before running automated tests.

The skill promises to remove old test data so every test starts with a clean environment. This sounds like a normal development task.

But the skill contains instructions to execute destructive database commands, such as DROP TABLE, using the database connection configured in the local .env file, without asking for confirmation.

Here's where things become dangerous.

The developer's .env file might still point to a shared staging database or even a production database from an earlier debugging session.

When the agent invokes the skill, it may execute the destructive command against whichever database the connection string identifies, potentially deleting important tables and their associated data.

An attacker could deliberately package this behavior as a harmless database cleanup skill, knowing users may trust it because the operation sounds routine.

The danger is that a seemingly helpful skill can execute destructive operations against the wrong resources, causing data loss or service disruption before anyone realizes what happened.

## Mitigations

- **Validate the target before execution.**
Verify which files, databases, or environments will be affected. Never assume a resource is safe to modify simply because a skill describes it as a test environment.

- **Require approval for destructive actions.**
Enforce explicit authorization before deleting databases, overwriting files, or executing irreversible commands. Do not allow skill instructions to bypass approval.

- **Restrict permissions and environments.** 
Give skills access only to necessary resources. Use isolated test environments and database accounts that cannot modify staging or production systems.

- **Review commands and maintain recovery options.** 
Scan skills for dangerous operations, including destructive SQL and filesystem commands. Use backups, snapshots, and monitoring to reduce the impact of accidental or malicious execution.
