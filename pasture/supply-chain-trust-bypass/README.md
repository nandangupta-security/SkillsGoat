# Supply Chain Trust Bypass

The skill fetches or installs code from an unpinned, unverified source —
a bare `curl | bash`, a raw GitHub URL, a dependency added outside the
lockfile — bypassing the package registry's provenance and signing
entirely. Usually stated plainly, not hidden: the risk isn't that it's
disguised, it's that skipping verification is treated as a convenience
shortcut. Compare to `scanner-evasion-obfuscation/`, where the concern is
*hiding* a payload rather than *skipping verification* of one.
