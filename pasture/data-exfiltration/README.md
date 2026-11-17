# What is Data Exflitration?

Data exfiltration is when a skill accesses sensitive information and sends it somewhere it should not go, often without the user's knowledge or proper authorization.

AI agent skills may have access to local files, environment variables, API keys, and other sensitive information. An attacker can take advantage of this access to collect and transmit data to an external destination.

Think of hiring someone to organize your important documents. They do the job correctly, but secretly make copies of your bank statements, passwords, and personal records and send them to someone else. Your documents are still organized, but your private information is no longer private.

## How attackers use it on skills

Imagine installing a skill called "Config Backup Helper" that promises to back up your project configuration files so you can restore your development environment if something goes wrong.

Sounds useful, right?

But the skill is designed to collect sensitive files such as .env, .npmrc, and credentials.json and automatically upload them to an external server controlled by an attacker.

These files may contain API keys, authentication tokens, database passwords, and other credentials.

When the user invokes the skill, the agent may perform the backup as instructed. The user thinks their configuration is being protected, but their sensitive information could now be in someone else's hands.

The attacker doesn't necessarily need to hide the behavior. Simply presenting credential collection as a convenient backup feature may convince users or agents to accept it.

The dangerous part is that a skill can perform its advertised function while quietly exposing sensitive information to an unauthorized destination.

## Mitigations

- **Know what data the skill accesses.**
Review which files, credentials, and environment variables a skill needs. Question any request to access secrets unrelated to its actual purpose.
- **Restrict external data transfers.**
Limit network access to approved destinations and prevent skills from uploading sensitive information to unknown or untrusted servers.
- **Protect secrets and credentials.**
Store secrets in dedicated secret managers where possible. Restrict access to sensitive files and avoid exposing credentials to skills unnecessarily.
- **Monitor unexpected data transfers.**
Review skill instructions, network activity, and file access. Alert on attempts to read credential files or transmit sensitive information to unauthorized destinations.
