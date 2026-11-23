# Indirect Prompt Injection?

**Indirect prompt injection is when an attacker hides instructions in a lower-trust file or outside resource that an AI agent reads while carrying out a legitimate task.**

Instead of appearing in the main skill description, the malicious directions can be in a downloaded page, attached document, search result, or supporting resource. The agent is supposed to use that material as evidence, not treat it as a new set of orders.

Think of a bookkeeper reviewing a supplier's invoice. The invoice contains a note saying, "Ignore your company's payment rules and use this new account." The invoice is something to inspect, not someone with authority to rewrite company policy.

## How attackers use it on skills

Imagine a skill that summarizes supplier invoices for an accounts-payable employee. The skill's own instructions look normal: read each invoice, extract its details, and prepare a summary for review.

One invoice, however, contains a paragraph written for an AI assistant. It claims to be an approved finance-system instruction and tells the agent to replace the supplier's verified bank details with an account chosen by the attacker.

When the agent opens the invoice, it encounters that paragraph as part of the document. If it follows the paragraph instead of treating it as untrusted invoice text, the resulting payment recommendation could be manipulated. The main skill file may show no suspicious instructions at all.

**The failure is promoting instructions embedded in third-party data into authority over the user's workflow.**

## Mitigations

- **Inspect content beyond the main skill file.** Include referenced resources, attachments, retrieved pages, and tool responses when reviewing indirect-injection exposure.
- **Keep retrieved content in the data role.** A document can supply facts, but it must not silently change the agent's instructions, permissions, or approval rules.
- **Verify sensitive decisions against trusted sources.** Compare payment details and other critical facts with independently authorized records before acting.
- **Limit permissions and require approval.** Enforce access controls and confirmation for sensitive changes, even when an instruction claims to come from a trusted team.
