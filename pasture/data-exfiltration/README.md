# Data Exfiltration

**Data exfiltration is when a skill obtains information it should not disclose and transfers it to an unauthorized place.**

An agent may be able to read private files, records, or credentials because it is helping with an ordinary task. A malicious skill can misuse that access to send more information than the user intended.

Think of asking a photographer to edit one picture. The photographer finishes the edit but also sends copies of your entire family album to an unknown company. The requested work is done, yet much more private material has left your control.

## How attackers use it on skills

Imagine an event-invitation skill that creates a calendar invitation for a small workshop. It only needs the selected attendees' addresses and the event details.

A malicious version quietly reads the organization's complete attendee directory and sends those names and addresses to an unapproved marketing service, claiming the transfer helps personalize the invitation. It then creates the requested invite, so the normal result looks correct.

The unnecessary disclosure is the security issue. The user agreed to invite a few people, not to share an entire contact directory. Depending on available permissions and network restrictions, the agent might be able to perform the extra transfer without noticing the mismatch.

**Completing the advertised task does not make an unrelated data transfer authorized.**

## Mitigations

- **Restrict data access to the actual task.** Give a skill only the records and files needed for the specific user request.
- **Control outbound connections.** Apply destination allowlists or sandbox network restrictions so skills cannot send data to unknown endpoints.
- **Keep secrets and private records isolated.** Avoid exposing broad credential stores or contact databases to tools that do not need them.
- **Audit unexpected reads and transfers.** Review file access and outbound requests, especially when they exceed the requested scope.
