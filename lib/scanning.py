"""Scanner support: registry, profiles, install, doctor and scan.

Everything here is optional. Nothing imports this module until a scanner
command or endpoint is used, and a missing or broken scanner only ever makes
these functions report a problem; Learn, Quiz, export, lint and serve do not
depend on it.
"""

import hashlib
import json
import os
import shutil
import subprocess
import sys
import time

import yaml

from lib.corpus import PASTURE_DIR, load_entries
from scanners.adapters import load_adapter

SCANNERS_DIR = ".scanners"            # gitignored: venvs, key files, cache
REGISTRY_PATH = os.path.join("scanners", "scanners.yaml")
PROFILES_PATH = os.path.join("scanners", "profiles.yaml")
CACHE_DIR = os.path.join(SCANNERS_DIR, "cache")


# -- registry and profiles ---------------------------------------------------

def _load_yaml(path, key):
    try:
        with open(path) as handle:
            return (yaml.safe_load(handle) or {}).get(key) or {}
    except OSError:
        return {}


def load_registry():
    return _load_yaml(REGISTRY_PATH, "scanners")


def load_profiles():
    profiles = _load_yaml(PROFILES_PATH, "profiles")
    for profile_id, profile in profiles.items():
        profile["id"] = profile_id
    return profiles


_adapters = {}            # one adapter per scanner, so it can remember its version


def get_adapter(scanner_id):
    if scanner_id not in _adapters:
        registry = load_registry()
        if scanner_id not in registry:
            raise KeyError("unknown scanner %r" % scanner_id)
        _adapters[scanner_id] = load_adapter(scanner_id, registry[scanner_id], SCANNERS_DIR)
    return _adapters[scanner_id]


# -- key files ---------------------------------------------------------------

def read_env_file(name):
    """Read KEY=VALUE pairs from .scanners/<name>. Returns {} if absent.

    Only a plain file name is accepted, so a profile cannot point outside
    .scanners/. Values are never printed by this module.
    """
    if not name or os.path.basename(name) != name:
        return {}
    values = {}
    try:
        with open(os.path.join(SCANNERS_DIR, name)) as handle:
            for line in handle:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                values[key.strip()] = value.strip().strip('"').strip("'")
    except OSError:
        return {}
    return values


# -- status ------------------------------------------------------------------

_STATUS_TTL = 30          # seconds; running `--version` every request is slow
_status_cache = {}


def scanner_status(scanner_id):
    cached = _status_cache.get(scanner_id)
    if cached and time.time() - cached[0] < _STATUS_TTL:
        return dict(cached[1])
    try:
        ok, detail = get_adapter(scanner_id).check()
    except Exception as exc:  # a broken adapter must not take the app down
        ok, detail = False, "adapter error: %s" % exc
    status = {"id": scanner_id, "ready": ok, "detail": detail}
    _status_cache[scanner_id] = (time.time(), status)
    return dict(status)


def profile_status(profile_id):
    profiles = load_profiles()
    if profile_id not in profiles:
        return {"id": profile_id, "ready": False, "detail": "unknown profile"}
    profile = profiles[profile_id]
    scanner = scanner_status(profile["scanner"])
    status = {
        "id": profile_id,
        "label": profile.get("label", profile_id),
        "scanner": profile["scanner"],
        "scanner_name": load_registry().get(profile["scanner"], {}).get("name", profile["scanner"]),
        "mode": profile.get("mode", "static"),
        "sends_data_off_machine": bool(profile.get("sends_data_off_machine")),
        "provider": profile.get("provider", ""),
        "ready": scanner["ready"],
        "detail": scanner["detail"],
    }
    env_file = profile.get("env_file")
    if status["ready"] and env_file:
        env = read_env_file(env_file)
        if not env.get("SKILL_SCANNER_LLM_API_KEY"):
            status["ready"] = False
            status["detail"] = "no API key: create .scanners/%s from its .template and add your key" % env_file
    return status


def all_status():
    return {
        "scanners": [scanner_status(s) for s in load_registry()],
        "profiles": [profile_status(p) for p in load_profiles()],
    }


# -- install -----------------------------------------------------------------

def _python_version(path):
    try:
        out = subprocess.run(
            [path, "-c", "import sys;print('%d.%d' % sys.version_info[:2])"],
            capture_output=True, text=True, timeout=20,
        ).stdout.strip()
        major, minor = out.split(".")
        return int(major), int(minor)
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return None


def find_python(minimum, maximum):
    """Find a Python in [minimum, maximum] (strings like '3.11')."""
    low = tuple(int(p) for p in minimum.split("."))
    high = tuple(int(p) for p in maximum.split("."))
    candidates = ["python%d.%d" % (3, m) for m in range(high[1], low[1] - 1, -1)]
    candidates += ["python3", sys.executable]
    for name in candidates:
        path = shutil.which(name) or (name if os.path.isabs(name) else None)
        if path:
            version = _python_version(path)
            if version and low <= version <= high:
                return path
    return None


def _venv_python(venv):
    sub = "Scripts" if sys.platform.startswith("win") else "bin"
    exe = "python.exe" if sys.platform.startswith("win") else "python"
    return os.path.join(venv, sub, exe)


def install_scanner(scanner_id, log=print):
    """Install a scanner into .scanners/<id>-venv. Returns (ok, message).

    On any failure the partial install is removed and nothing else changes.
    """
    registry = load_registry()
    if scanner_id not in registry:
        return False, "unknown scanner %r (see scanners/scanners.yaml)" % scanner_id
    spec = registry[scanner_id]["install"]
    if spec.get("method") != "pip-venv":
        return False, "install method %r is not supported yet" % spec.get("method")

    python = find_python(spec["python_min"], spec["python_max"])
    if not python:
        return False, ("needs Python %s to %s, but none was found. Install one "
                       "(for example: sudo apt install python3.12) and try again."
                       % (spec["python_min"], spec["python_max"]))

    venv = os.path.join(SCANNERS_DIR, scanner_id + "-venv")
    os.makedirs(SCANNERS_DIR, exist_ok=True)
    shutil.rmtree(venv, ignore_errors=True)

    def fail(message):
        shutil.rmtree(venv, ignore_errors=True)
        return False, message

    log("Using %s" % python)
    log("Creating environment %s ..." % venv)
    made = subprocess.run([python, "-m", "venv", venv], capture_output=True, text=True)
    if made.returncode != 0:
        hint = ""
        if "ensurepip" in made.stderr or "venv" in made.stderr:
            hint = " On Debian or Kali, run: sudo apt install python3-venv"
        return fail("could not create the environment.%s\n%s" % (hint, made.stderr.strip()[-300:]))

    package = "%s==%s" % (spec["package"], spec["version"])
    log("Installing %s (this downloads several packages) ..." % package)
    pip = subprocess.run(
        [_venv_python(venv), "-m", "pip", "install", "--quiet", package],
        capture_output=True, text=True,
    )
    if pip.returncode != 0:
        return fail("pip could not install %s (network, proxy or platform problem?)\n%s"
                    % (package, pip.stderr.strip()[-400:]))

    _status_cache.pop(scanner_id, None)       # re-check for real after installing
    ok, detail = get_adapter(scanner_id).check()
    if not ok:
        return fail("installed, but the scanner does not run: %s" % detail)
    return True, "%s %s is ready" % (scanner_id, detail)


# -- scanning ----------------------------------------------------------------

def find_entry(entry_id):
    for entry in load_entries(PASTURE_DIR):
        if entry.id == entry_id:
            return entry
    return None


def _content_hash(skill_dir):
    digest = hashlib.sha256()
    for root, dirs, files in os.walk(skill_dir):
        dirs.sort()
        for name in sorted(files):
            path = os.path.join(root, name)
            digest.update(os.path.relpath(path, skill_dir).encode())
            with open(path, "rb") as handle:
                digest.update(handle.read())
    return digest.hexdigest()


CACHE_FORMAT = "2"        # bump when the stored result shape or merging changes


def _cache_path(adapter, profile, env, skill_dir):
    parts = [CACHE_FORMAT, adapter.id, adapter.version(), profile["id"], profile.get("mode", ""),
             profile.get("policy", ""), env.get("SKILL_SCANNER_LLM_MODEL", ""),
             _content_hash(skill_dir)]
    key = hashlib.sha256("|".join(parts).encode()).hexdigest()
    return os.path.join(CACHE_DIR, key + ".json")


def scan_entry(entry_id, profile_id, use_cache=True):
    """Scan one corpus entry with one profile. Returns (result_dict, from_cache)."""
    entry = find_entry(entry_id)
    if entry is None:
        return {"verdict": "error", "error": "unknown entry %r" % entry_id}, False
    profiles = load_profiles()
    if profile_id not in profiles:
        return {"verdict": "error", "error": "unknown profile %r" % profile_id}, False
    profile = profiles[profile_id]

    status = profile_status(profile_id)
    if not status["ready"]:
        return {"verdict": "error", "scanner": profile["scanner"],
                "error": status["detail"]}, False

    adapter = get_adapter(profile["scanner"])
    env = read_env_file(profile.get("env_file")) if profile.get("env_file") else {}
    cache = _cache_path(adapter, profile, env, entry.skill_dir)

    if use_cache and os.path.exists(cache):
        try:
            with open(cache) as handle:
                return json.load(handle), True
        except (OSError, ValueError):
            pass

    result = adapter.scan(entry.skill_dir, profile, extra_env=env).to_dict()
    if result["verdict"] != "error":          # never cache failures
        os.makedirs(CACHE_DIR, exist_ok=True)
        with open(cache, "w") as handle:
            json.dump(result, handle)
    return result, False


def scan_many(entry_ids, profile_id, on_result, use_cache=True):
    """Scan several entries, pausing between uncached scans if the profile asks."""
    profile = load_profiles().get(profile_id, {})
    pause = profile.get("min_seconds_between_scans", 0)
    last_live = None
    for entry_id in entry_ids:
        if pause and last_live is not None:
            wait = pause - (time.time() - last_live)
            if wait > 0:
                time.sleep(wait)
        result, cached = scan_entry(entry_id, profile_id, use_cache)
        if not cached:
            last_live = time.time()
        on_result(entry_id, result, cached)
