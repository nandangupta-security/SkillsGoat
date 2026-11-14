# Persistence / Backdoor

Persistence means a skill leaves something behind that keeps running after the skill is done, so the attacker's access outlasts the skill itself.

Think of a contractor who fixes your door, then keeps a copy of the key. The job is over, but they can walk in whenever they like, and you've forgotten they ever had access.

## How attackers use it on skills

The skill does something useful, such as improving your terminal prompt. While doing it, it quietly plants something that **starts by itself later**: a line in your **shell startup file** (a file that runs every time you open a terminal), a **scheduled job** (a task your computer runs on a timer), or a **git hook** (a script that runs automatically when you commit or switch branches). Now the attacker's code runs again and again without you doing anything. Deleting the skill doesn't remove it, because the changes live in other files on your machine.

## Mitigations

- **Review what a skill changes.** Be wary of any skill that edits startup files, schedules jobs or installs hooks.
- **Require approval for system changes.** A skill shouldn't write outside its own folder without asking you.
- **Audit the usual hiding places.** Check shell startup files, scheduled jobs and git hooks, especially after removing a skill.
- **Run skills with least access.** A skill that can't write to those places can't leave anything behind.
