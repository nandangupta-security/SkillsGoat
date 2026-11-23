# Prompt Injection?

**Prompt injection is when an attacker puts instructions in material an AI agent reads, hoping the agent will do something the user never asked it to do.**

For agent skills, the attack can appear directly in a skill's name or description. These fields should help the agent understand the skill, not give an untrusted publisher the power to order the agent around.

Think of asking a receptionist to look up an appointment. A stranger has slipped an extra note into the appointment label that says, "Cancel the afternoon appointments first." The label is information to read, not permission to change anyone's schedule.

## How attackers use it on skills

Imagine a meeting-availability skill that tells the agent which time slots are open. Its description includes a second, unrelated request: when the user asks for available times, secretly decline invitations from an entire department and then show the usual availability list.

The agent may encounter that instruction while deciding which skill to use. If it treats a skill description as an authority to manage meetings, it could alter the calendar even though the user only asked a question.

The attacker has not needed to break the calendar system. They have tried to convert lower-trust descriptive text into an unauthorized action. A legitimate-looking answer could hide the change.

**The failure is crossing the boundary between reading a skill's description and obeying instructions planted inside it.**

## Mitigations

- **Treat skill metadata as information, not permission.** Do not let a description override the user's task or grant new authority to use tools.
- **Review metadata for behavioral instructions.** Flag unexpected orders, hidden prerequisites, and requests to conceal actions when examining a skill before use.
- **Enforce authorization outside the model.** Require independent approval and restricted tool permissions for changes to files, accounts, or external services.
- **Scan changes and monitor tool calls.** Recheck metadata on updates and investigate actions that have no clear relationship to the user's original request.
