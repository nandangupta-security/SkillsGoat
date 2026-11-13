# Excessive Permission Scope

## 1. What is it?

The skill asks for much more access than its job needs. The job is small
and specific. The access is broad.

Nothing bad has to happen for this to count. The gap between what the
skill needs and what it asks for is the finding.

`105-commit-message-linter` only checks the wording of a commit message.
To do that it asks for read and write access to your entire home
directory, plus unrestricted outbound network access. Reading one file
would have done.

This one is the odd one out. Every other entry in the corpus describes
something happening. This one describes nothing happening. You are
reporting a request, not an act.

## 2. How can it be exploited through an AI agent skill?

The problem is usually not today. A skill that can read every file but
only checks one line is harmless this afternoon. The permission is what
sticks around:

- The next version inherits it, and almost nobody re-reads permissions
  on an update.
- If the author's account is compromised, the attacker inherits it.
- An ordinary bug in the skill now has far more it can break.

### How the attack works

1. A useful, narrow task nobody will argue with.
2. A broad permission request bundled into the install.
3. Granted without comparing it to the task.
4. The skill behaves exactly as described. Nothing to notice.
5. The access gets used later, after an update or a compromise.

## 3. What can an attacker achieve?

Whatever was granted. With home directory read and write plus network
access, as `105` asks for:

- Read `~/.ssh`, `~/.aws/credentials` and `.env` files
- Write `~/.zshrc` or `~/.ssh/authorized_keys`, which is persistence
- Send any of it anywhere
- Change any repository in your home directory

`105` does none of this. It asks, and then it behaves. That is the test:
will a reviewer report an over-request that has no payload attached to
it?

## 4. How to spot it in a skill

1. Read what the skill says it does. Write down the smallest access that
   job would need: which files, which hosts, read or write.
2. Do that before you read the permissions, so the request cannot sway
   you.
3. Compare the two lists.

For `105`:

- **Needs:** read `.git/COMMIT_EDITMSG`
- **Asks for:** read and write across all of `$HOME`, plus any network

Two gaps, and each is a finding on its own.

Treat a vague permission as "anything": `*`, `~/`, `/`, a phrase like
"access to your files", or no permissions section at all.

Check read and write separately. Check the direction of network access
too, because "needs the internet" and "needs to POST to one host" are
very different requests.

Scanners are weak here, catching this in 1 run out of 4, because judging
"more than the job needs" means understanding the job. A tool can see
that a skill asks for file access. It cannot see that checking a commit
message never needed it. Good place for a human to look.

**Not a finding:** a formatter really does need to read every file.
Access is only excessive compared to what the skill claims to do, so
read the claim first.

## 5. How to prevent it

- Name exact paths and hosts instead of wildcards.
- Ask for read when you do not need write.
- Write one line next to each permission saying why the task needs it.
  If that line is hard to write, the permission is too wide.
- Re-read the permissions when a skill updates. That is where a narrow
  skill quietly becomes a broad one.
- Run skills sandboxed, with no network by default.
