"""Adapter for NVIDIA's SkillSpector (https://github.com/NVIDIA/SkillSpector).

Runs as a separate program in its own virtual environment
(.scanners/skillspector-venv/); SkillsGoat never imports it.

Two modes: "static" (`--no-llm`, fully offline) and "judge" (static plus
SkillSpector's LLM stages, configured through the profile's env file).
SkillSpector grades a skill with a 0-100 score and a recommendation
(SAFE / CAUTION / DO NOT INSTALL).
Whether CAUTION counts as "flagged" is a policy choice, set per profile with
`flag_at` (default CAUTION).
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
    friendly_error,
    scrub_secrets,
    severity_rank,
)

# Recommendation tiers, lowest to highest.
TIERS = ["SAFE", "CAUTION", "DO_NOT_INSTALL"]


def _tier(value):
    return TIERS.index(re.sub(r"[\s-]+", "_", (value or "SAFE").strip().upper()))


class SkillSpectorAdapter(ScannerAdapter):
    id = "skillspector"

    def __init__(self, spec, scanners_dir):
        ScannerAdapter.__init__(self, spec, scanners_dir)
        self._version = None

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
            proc = subprocess.run([exe, "--version"], capture_output=True, text=True, timeout=60)
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
        if mode not in ("static", "judge"):
            return error_result(self.id, "unknown mode %r" % mode, mode=mode)
        if self._version is None or not os.path.exists(self.executable()):
            ok, detail = self.check()
            if not ok:
                return error_result(self.id, detail, mode=mode)

        # Point SkillSpector's dependency-CVE check at an empty local folder so
        # it never calls OSV.dev. Static mode then stays fully offline; the
        # cost is that known-vulnerable-dependency checks find nothing.
        osv_dir = os.path.join(self.scanners_dir, "osv-offline")
        os.makedirs(osv_dir, exist_ok=True)
        env = dict(os.environ)
        env.update(extra_env or {})
        env["SKILLSPECTOR_OSV_DB_PATH"] = os.path.abspath(osv_dir)
        if mode == "judge":
            # By default SkillSpector sends up to 10 LLM requests at once, which a free
            # plan answers with rate-limit errors (its own code says so). One at a time
            # is slower but finishes. A profile's env file can set a higher value.
            env.setdefault("SKILLSPECTOR_MAX_LLM_CONCURRENCY", "1")

        workdir = tempfile.mkdtemp(prefix="skillgoat-ss-")      # keep stray files out of the repo
        out_path = os.path.join(workdir, "report.json")
        secrets = [v for k, v in env.items() if "KEY" in k or "TOKEN" in k]
        cmd = [os.path.abspath(self.executable()), "scan"]
        if mode == "static":
            cmd.append("--no-llm")
        else:
            timeout = max(timeout, 540)      # several LLM calls, and free tiers can make it wait
        cmd += ["--format", "json", "--output", out_path, "--", os.path.abspath(skill_dir)]

        started = time.time()
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, errors="replace",
                                  env=env, timeout=timeout, cwd=workdir)
        except subprocess.TimeoutExpired:
            self._cleanup(workdir)
            return error_result(self.id, "scan timed out after %ds" % timeout,
                                scanner_version=self.version(), mode=mode)
        except OSError as exc:
            self._cleanup(workdir)
            return error_result(self.id, "could not start scanner: %s" % exc, mode=mode)

        elapsed = time.time() - started
        raw = None
        try:
            with open(out_path) as handle:
                raw = json.load(handle)
        except (OSError, ValueError):
            pass
        self._cleanup(workdir)

        if raw is None or proc.returncode == 2:     # 2 = error (bad input, internal failure)
            full = scrub_secrets((proc.stderr or proc.stdout or "no output").strip(), secrets)
            tail = " | ".join(full.splitlines()[-3:])[:400]
            return error_result(self.id, friendly_error(full) or "scanner produced no result: %s" % tail,
                                scanner_version=self.version(), mode=mode)
        return self._normalize(raw, profile, mode, elapsed)

    # -- helpers -------------------------------------------------------------

    @staticmethod
    def _cleanup(workdir):
        try:
            for name in os.listdir(workdir):
                os.remove(os.path.join(workdir, name))
            os.rmdir(workdir)
        except OSError:
            pass

    @staticmethod
    def _where(location):
        location = location or {}
        return location.get("file") or "", location.get("start_line") or 0

    def _normalize(self, raw, profile, mode, elapsed):
        if not raw.get("execution_successful", True):
            return error_result(self.id, "SkillSpector reported that the scan did not complete",
                                scanner_version=self.version(), mode=mode)

        # A "Static + LLM" result must really have used the LLM.
        meta = raw.get("metadata") or {}
        if mode == "judge" and not (meta.get("llm_requested") and meta.get("llm_available")):
            return error_result(self.id, "the LLM analysis was requested but did not run",
                                scanner_version=self.version(), mode=mode)
        usage = meta.get("inference_usage") or []
        tokens = None
        if usage:                           # sum SkillSpector's per-call usage list
            tokens = {
                "input_tokens": sum(u.get("prompt_tokens", 0) for u in usage),
                "output_tokens": sum(u.get("completion_tokens", 0) for u in usage),
                "total_tokens": sum(u.get("total_tokens", 0) for u in usage),
            }

        risk = raw.get("risk_assessment") or {}
        recommendation = (risk.get("recommendation") or "SAFE").replace("_", " ")
        flag_at = profile.get("flag_at", "CAUTION")
        flagged = _tier(recommendation) >= _tier(flag_at)

        # Never present a partially inspected skill as clean.
        completeness = raw.get("analysis_completeness") or {}
        if not flagged and completeness.get("is_complete") is False:
            return error_result(
                self.id,
                "scan was incomplete (%s%% of the skill was inspected), so there is no clean verdict"
                % completeness.get("coverage_percent", "?"),
                scanner_version=self.version(), mode=mode,
            )

        findings = []
        for issue in raw.get("issues", []):
            file, line = self._where(issue.get("location"))
            others = []
            for occ in (issue.get("occurrences") or [])[1:]:
                f2, l2 = self._where(occ)
                others.append("%s:%s" % (f2, l2))
            findings.append(Finding(
                rule=issue.get("id", ""),
                severity=(issue.get("severity") or "low").lower(),
                title=issue.get("pattern") or issue.get("category") or "",
                file=file,
                line=line,
                message=issue.get("explanation", ""),
                also_at=others,
            ))
        findings.sort(key=lambda f: -severity_rank(f.severity))

        return ScanResult(
            verdict="flagged" if flagged else "clean",
            scanner=self.id,
            scanner_version=self.version(),
            profile=profile.get("id", ""),
            mode=mode,
            max_severity=findings[0].severity if findings else "none",
            findings=findings,
            duration_seconds=elapsed,
            tokens=tokens,
            raw=raw,
            score=risk.get("score"),
            recommendation=recommendation,
            overall_severity=(risk.get("severity") or "").lower(),
        )
