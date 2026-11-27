"""The contract every scanner adapter follows.

An adapter wraps one external scanner (open source or paid) and translates its
native output into the single ScanResult shape below, so the rest of SkillsGoat
never needs to know how any particular scanner reports things.

Keep this module free of third-party imports and of Python >3.7 syntax: the
core app must keep working even when no scanner is installed.
"""

from dataclasses import dataclass, field

# Lowest to highest. Used to compare and sort severities across scanners.
SEVERITY_ORDER = ["none", "info", "low", "medium", "high", "critical"]

# verdict values:
#   flagged  the scanner considers this skill unsafe
#   clean    the scanner found nothing it considers unsafe (NOT a guarantee)
#   error    the scan did not complete; never treat this as clean
VERDICTS = ("flagged", "clean", "error")


def severity_rank(severity):
    try:
        return SEVERITY_ORDER.index((severity or "none").lower())
    except ValueError:
        return 0


@dataclass
class Finding:
    rule: str
    severity: str
    title: str
    file: str = ""
    line: int = 0
    message: str = ""
    # Other places the exact same match was reported (see the adapter); kept so
    # merging repeats never loses a location.
    also_at: list = field(default_factory=list)

    def to_dict(self):
        return {
            "rule": self.rule,
            "severity": self.severity,
            "title": self.title,
            "file": self.file,
            "line": self.line,
            "message": self.message,
            "also_at": self.also_at,
        }


@dataclass
class ScanResult:
    verdict: str                      # one of VERDICTS
    scanner: str                      # registry id, e.g. "skill-scanner"
    scanner_version: str = ""
    profile: str = ""                 # profile id used for this scan
    mode: str = ""                    # e.g. "static" or "judge"
    max_severity: str = "none"
    findings: list = field(default_factory=list)
    duration_seconds: float = 0.0
    tokens: dict = None               # LLM usage when the scanner reports it
    error: str = ""                   # set when verdict == "error"
    raw: dict = None                  # the scanner's own output, unedited
    # For scanners that grade a skill with a score. max_severity above always
    # means "the worst single finding"; overall_severity is the scanner's
    # severity for the skill as a whole. Left empty when a scanner has neither.
    score: int = None                 # e.g. 45 (out of 100)
    recommendation: str = ""          # the scanner's own wording, e.g. "CAUTION"
    overall_severity: str = ""        # e.g. "medium"

    def to_dict(self):
        return {
            "verdict": self.verdict,
            "scanner": self.scanner,
            "scanner_version": self.scanner_version,
            "profile": self.profile,
            "mode": self.mode,
            "max_severity": self.max_severity,
            "findings": [f.to_dict() for f in self.findings],
            "duration_seconds": round(self.duration_seconds, 2),
            "tokens": self.tokens,
            "error": self.error,
            "raw": self.raw,
            "score": self.score,
            "recommendation": self.recommendation,
            "overall_severity": self.overall_severity,
        }


def scrub_secrets(text, secrets):
    """Remove secret values from text before it is shown or logged."""
    for secret in secrets:
        if secret and len(secret) >= 8:
            text = text.replace(secret, "<hidden>")
    return text


def friendly_error(text):
    """A plain-English message for the usual LLM problems, or None if unknown."""
    low = (text or "").lower()
    if "rate_limit" in low or "ratelimit" in low or "too many requests" in low:
        return ("the LLM provider's rate limit was reached (free plans allow only a few "
                "thousand tokens per minute). Wait a minute and try again.")
    if "invalid_api_key" in low or "incorrect api key" in low or "unauthorized" in low:
        return "the LLM provider rejected the API key. Check the key in your .scanners/*.env file."
    if "llm stage degraded" in low or "llm batch failed" in low:
        return ("the LLM stage did not finish, so there is no complete result. "
                "Wait a minute and try again, or use a Static profile.")
    return None


def error_result(scanner, message, **kwargs):
    """A failed scan. Always an explicit error, never a silent 'clean'."""
    return ScanResult(verdict="error", scanner=scanner, error=message, **kwargs)


class ScannerAdapter:
    """Subclass this once per scanner and register it in scanners.yaml."""

    #: registry id; must match the key in scanners.yaml
    id = ""

    def __init__(self, spec, scanners_dir):
        self.spec = spec                  # this scanner's block from scanners.yaml
        self.scanners_dir = scanners_dir  # the .scanners/ folder

    def known_version(self):
        """The version if a check has already succeeded, else None. Starts no process."""
        return getattr(self, "_version", None)

    def check(self):
        """Return (ok, detail). detail is the version when ok, else the reason.

        Must actually try to run the scanner, not just look for a file, so a
        broken install is reported as broken.
        """
        raise NotImplementedError

    def scan(self, skill_dir, profile, extra_env=None, timeout=300):
        """Scan one skill directory and return a ScanResult.

        Must never raise for ordinary failures (timeouts, bad output, LLM
        errors). Return error_result(...) instead.
        """
        raise NotImplementedError
