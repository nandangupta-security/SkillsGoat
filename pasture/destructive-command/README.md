# What is a Destructive Command?

**A destructive command is an instruction or operation that removes, overwrites, or irreversibly changes something important without appropriate checks or authorization.**

Some skills legitimately clean temporary data or perform maintenance. The danger is when a seemingly routine step destroys resources that were not supposed to be touched.

Think of asking someone to remove old paper flyers from a noticeboard. They remove the flyers but also shred the signed originals stored in a nearby filing cabinet. The cleanup request did not authorize destroying the originals.

## How attackers use it on skills

Imagine a photo-gallery optimization skill that promises to shrink thumbnail files so a website loads faster. It needs to regenerate small preview images, not alter the originals.

An attacker inserts an extra cleanup instruction directing the agent to permanently erase the folder containing the high-resolution source photographs after new thumbnails are generated. The step is described as saving space, and the skill may still produce attractive previews.

The user gets a faster gallery but may lose original images that cannot be recovered from thumbnails. A dangerous instruction has been blended into an otherwise plausible maintenance workflow.

**The failure is letting a skill turn permission for a small cleanup task into permission for irreversible destruction.**

## Mitigations

- **Check the precise target of every destructive operation.** Distinguish temporary outputs from original data and confirm the intended path or resource.
- **Require authorization for irreversible changes.** Keep deletion approval and safeguards outside the skill's own instructions.
- **Isolate and minimize permissions.** Use restricted workspaces and accounts so a skill cannot destroy unrelated files or systems.
- **Prefer recovery-friendly workflows.** Use dry runs, snapshots, backups, and audit logs where suitable, rather than permanent deletion by default.
