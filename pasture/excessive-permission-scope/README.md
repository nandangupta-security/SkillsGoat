# Excessive Permission Scope

The skill's stated task is narrow, but it requests or uses access far
broader than that task needs — filesystem-wide read/write for something
that only needs one file, unrestricted network access for something
that's purely local. Nothing here is necessarily used maliciously in the
moment; the risk is what that unnecessary access enables later, if the
skill is compromised, updated, or simply misbehaves.
