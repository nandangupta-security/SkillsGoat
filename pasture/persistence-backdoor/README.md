# Persistence / Backdoor

Persistence means a skill leaves something behind that keeps running after the skill is done, so the attacker's access outlasts the skill itself.

Think of a contractor who fixes your door, then keeps a copy of the key. The job is over, but they can walk in whenever they like, and you've forgotten they ever had access.

## How attackers use it on skills

Imagine a skill called "Downloads Tidy" that sorts the files in your Downloads folder. You run it once and your folder looks great.

But it also sets up a **scheduled job** (a task your computer runs on a timer) that runs every night. Each night it downloads a script from the attacker's server and runs it.

Deleting the skill doesn't stop it, because the scheduled job lives somewhere else on your machine.

## Mitigations

- **Review what a skill changes.** Be wary of any skill that changes what runs when you open a terminal, sets up timed tasks, or adds scripts that run on their own.
- **Require approval for system changes.** A skill should ask you first before it changes your computer's settings or sets anything up to run later.
- **Run skills with least access.** Don't give a skill permission to edit startup files or set up timed tasks unless its job truly needs it.
