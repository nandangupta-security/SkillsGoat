# Scanner Evasion / Obfuscation

Obfuscation is when a harmful command is deliberately scrambled, so it never appears in one piece anywhere a person or a tool would look for it.

Nothing is being hidden for a good reason. The harmful part still runs exactly as the attacker intended. It is simply written as numbers, as scrambled text, or broken across separate files, and put back together one second before it is used.

A familiar example: grown-ups spelling out "i-c-e c-r-e-a-m" so the child in the room does not react. The word was never said out loud, but everyone who needed to understand it did.

## How attackers use it on skills

A skill can carry small scripts alongside its instructions. The attacker writes the dangerous command as a list of character codes, or as scrambled text, or splits it in half across two files that each look harmless on their own. The script rebuilds it while it runs, so the real command exists only for the instant it is used. Search every file for anything suspicious and you find **nothing at all** — and the skill still does exactly what the attacker wanted.

## Mitigations

- **Ask why it is hidden.** Honest code has no reason to scramble a command. The hiding is the finding, before you even know what it says.
- **Follow what gets run.** Wherever a skill runs a command, trace back where that text came from. Text that was assembled is a warning sign; text you can simply read is not.
- **Unscramble it yourself.** Decode it by hand and read what it says. Never run the script to find out.
- **Block outgoing traffic by default.** A hidden command that cannot reach the internet cannot send anything out.
