"""Adapter for Cisco's skill-scanner (https://github.com/cisco-ai-defense/skill-scanner).

The scanner runs as a separate program inside its own virtual environment
(.scanners/skill-scanner-venv/). We never import it, so a missing or broken
install cannot break SkillsGoat itself.
"""

import json
import os
import re
import subprocess
import sys
import tempfile
import time

from .base import (
    Finding,
    ScanResult,
    ScannerAdapter,
    error_result,
    severity_rank,
)

def _scrub(text, secrets):
    """Remove secret values from text before it is shown or logged."""
    for secret in secrets:
        if secret and len(secret) >= 8:
            text = text.replace(secret, "<hidden>")
    return text


class SkillScannerAdapter(ScannerAdapter):
    id = "skill-scanner"

    def __init__(self, spec, scanners_dir):
        ScannerAdapter.__init__(self, spec, scanners_dir)
        self._version = None

    # -- locating the installed scanner ------------------------------------

    def venv_dir(self):
        return os.path.join(self.scanners_dir, self.id + "-venv")

    def executable(self):
        bindir = "Scripts" if sys.platform.startswith("win") else "bin"
        name = self.spec["run"]["executable"]
        if sys.platform.startswith("win"):
            name += ".exe"
        return os.path.join(self.venv_dir(), bindir, name)

    def check(self):
        exe = self.executable()
        if not os.path.exists(exe):
            return False, "not installed (run: python3 goat.py scanners install %s)" % self.id
        try:
            proc = subprocess.run(
                [exe, "--version"], capture_output=True, text=True, timeout=60
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            return False, "installed but could not run: %s" % exc
        output = (proc.stdout + proc.stderr).strip()
        match = re.search(r"\d+\.\d+\.\d+", output)
        if proc.returncode != 0 or not match:
            tail = output.splitlines()[-1] if output else "no output"
            return False, "installed but broken: %s" % tail
        self._version = match.group(0)
        return True, self._version

    def version(self):
        if self._version is None:
            self.check()
        return self._version or ""

    # -- scanning ------------------------------------------------------------

    def scan(self, skill_dir, profile, extra_env=None, timeout=300):
        mode = profile.get("mode", "static")
        # Only run the slow `--version` probe the first time; after that a
        # missing executable is enough to know something changed.
        if self._version is None or not os.path.exists(self.executable()):
            ok, detail = self.check()
            if not ok:
                return error_result(self.id, detail, mode=mode)

        cmd = [self.executable(), "scan", skill_dir, "--format", "json"]
        if mode == "judge":
            cmd += ["--use-llm", "--policy", profile.get("policy", "balanced")]

        env = dict(os.environ)
        env.update(extra_env or {})
        secrets = [v for k, v in env.items() if "KEY" in k or "TOKEN" in k]

        # The scanner mixes log noise into stdout, so ask for a results file.
        handle, out_path = tempfile.mkstemp(suffix=".json", prefix="skillgoat-scan-")
        os.close(handle)
        cmd += ["--output", out_path]

        started = time.time()
        try:
            proc = subprocess.run(
                cmd, capture_output=True, text=True, errors="replace",
                env=env, timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            self._cleanup(out_path)
            return error_result(self.id, "scan timed out after %ds" % timeout,
                                scanner_version=self.version(), mode=mode)
        except OSError as exc:
            self._cleanup(out_path)
            return error_result(self.id, "could not start scanner: %s" % exc, mode=mode)

        elapsed = time.time() - started
        raw = self._load_json(out_path, proc.stdout)
        self._cleanup(out_path)

        if raw is None:
            tail = _scrub((proc.stderr or proc.stdout or "no output").strip(), secrets)
            tail = " | ".join(tail.splitlines()[-3:])[:400]
            return error_result(self.id, "scanner produced no result: %s" % tail,
                                scanner_version=self.version(), mode=mode)

        return self._normalize(raw, profile, mode, elapsed)

    # -- helpers -------------------------------------------------------------

    @staticmethod
    def _cleanup(path):
        try:
            os.remove(path)
        except OSError:
            pass

    @staticmethod
    def _load_json(out_path, stdout):
        """Prefer the results file; fall back to JSON found inside stdout."""
        try:
            with open(out_path) as handle:
                text = handle.read()
            if text.strip():
                return json.loads(text)
        except (OSError, ValueError):
            pass
        start = stdout.find("\n{")
        if start != -1:
            try:
                return json.loads(stdout[start:])
            except ValueError:
                return None
        return None

    def _normalize(self, raw, profile, mode, elapsed):
        result = raw["results"][0] if "results" in raw and raw["results"] else raw
        analyzers = result.get("analyzers_used") or []

        # A judge scan that silently ran without the judge must not pass for one.
        if mode == "judge" and "llm_analyzer" not in analyzers:
            return error_result(
                self.id, "the LLM analysis was requested but did not run",
                scanner_version=self.version(), mode=mode,
            )

        # Every finding is kept, including low-signal ones such as a missing
        # license. The one thing merged is an exact repeat: the scanner can
        # report the same matched text twice (once against the whole
        # `description` field, once against the line it sits on). Those become
        # one finding that lists both locations. `raw` is never altered.
        findings = []
        seen = {}                      # (rule, file, matched text) -> (finding, snippet)
        for item in result.get("findings", []):
            finding = Finding(
                rule=item.get("rule_id", ""),
                severity=(item.get("severity") or "info").lower(),
                title=item.get("title", ""),
                file=item.get("file_path") or "",
                line=item.get("line_number") or 0,
                message=item.get("description", ""),
            )
            snippet = item.get("snippet") or ""
            matched = (item.get("metadata") or {}).get("matched_text")
            key = (finding.rule, finding.file, matched) if matched else None
            if key and key in seen:
                first, first_snippet = seen[key]
                here = "%s:%s" % (finding.file, finding.line)
                if len(snippet) < len(first_snippet):
                    # the newer report points at the tighter spot; prefer it
                    first.also_at.append("%s:%s" % (first.file, first.line))
                    first.line = finding.line
                    seen[key] = (first, snippet)
                else:
                    first.also_at.append(here)
                continue
            findings.append(finding)
            if key:
                seen[key] = (finding, snippet)
        findings.sort(key=lambda f: -severity_rank(f.severity))
        top = findings[0].severity if findings else "none"

        return ScanResult(
            verdict="clean" if result.get("is_safe", True) else "flagged",
            scanner=self.id,
            scanner_version=self.version(),
            profile=profile.get("id", ""),
            mode=mode,
            max_severity=top,
            findings=findings,
            duration_seconds=result.get("scan_duration_seconds", elapsed),
            tokens=result.get("llm_usage"),
            raw=raw,
        )
