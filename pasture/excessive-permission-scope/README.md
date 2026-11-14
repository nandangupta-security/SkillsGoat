# Excessive Permission Scope

Excessive permission scope is when a skill asks for far more access than its job could possibly need.

Nothing bad has to happen for this to count. The gap between the small job and the large request is the problem, all by itself.

A familiar example: a plumber comes to fix the kitchen tap and asks for the keys to every room in the house. They may well fix the tap and go home. But you handed over the keys, and you have no idea who holds a copy now.

## How attackers use it on skills

A skill that does something small and dull — tidy a file, check some spelling — asks at install time to read and write every file you own and to send data anywhere on the internet. People say yes, because the job sounds harmless and the request arrives next to something they actually want. The skill then behaves exactly as promised, so nothing ever looks wrong. But the access stays granted, and the next update, or whoever steals the author's account, quietly inherits **all of it**.

## Mitigations

- **Decide what it needs first.** Write down the smallest access the job requires before you look at what is being asked for, so the request cannot talk you into it.
- **Name exact files and addresses.** "All your files" and "the internet" are not permissions, they are blank cheques.
- **Allow reading, not writing.** Most skills only ever need to look.
- **Check again on every update.** A narrow skill can quietly become a broad one, and almost nobody re-reads permissions the second time.
