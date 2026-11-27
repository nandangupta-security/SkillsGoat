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
import threading
import time

import yaml

from lib.corpus import PASTURE_DIR, load_entries, tier_of
from scanners.adapters import load_adapter

SCANNERS_DIR = ".scanners"            # gitignored: venvs, key files, cache
REGISTRY_PATH = os.path.join("scanners", "scanners.yaml")
PROFILES_PATH = os.path.join("scanners", "profiles.yaml")
CACHE_DIR = os.path.join(SCANNERS_DIR, "cache")
RESULTS_DIR = os.path.join(SCANNERS_DIR, "results")      # the benchmark ledger


# -- registry and profiles ---------------------------------------------------

def _load_yaml(path, key):
    try:
        with open(path) as handle:
            return (yaml.safe_load(handle) or {}).get(key) or {}
    except OSError:
        return {}


def load_registry():
    return _load_yaml(REGISTRY_PATH, "scanners")


def load_providers():
    return _load_yaml(REGISTRY_PATH, "providers")


PROVIDER_FILE = os.path.join(SCANNERS_DIR, "llm-provider")


def current_provider():
    """The one LLM provider chosen for the whole app, or None if none is chosen yet."""
    try:
        with open(PROVIDER_FILE) as handle:
            choice = handle.read().strip().lower()
    except OSError:
        return None
    return choice if choice in load_providers() else None


def key_file_for(scanner_id, provider_id):
    """Each scanner keeps its own key file per provider, e.g. skillspector-openai.env."""
    return "%s-%s.env" % (scanner_id, provider_id)


def _apply_provider(profile, provider_id):
    """Fill in the provider-specific parts of an `llm: true` profile."""
    llm = load_registry().get(profile["scanner"], {}).get("llm", {})
    profile["sends_data_off_machine"] = True
    if provider_id is None:
        profile["needs_provider"] = True
        profile["provider"] = ""
        return
    provider = load_providers()[provider_id]
    profile["provider"] = provider["name"]
    profile["provider_id"] = provider_id
    profile["env_file"] = key_file_for(profile["scanner"], provider_id)
    profile["key_var"] = llm.get("keys", {}).get(provider_id, "SKILL_SCANNER_LLM_API_KEY")
    if provider.get("free_plan") and llm.get("free_plan_pause_seconds"):
        profile["min_seconds_between_scans"] = llm["free_plan_pause_seconds"]   # keep under the per-minute cap


def load_profiles():
    profiles = _load_yaml(PROFILES_PATH, "profiles")
    provider_id = current_provider()
    for profile_id, profile in profiles.items():
        profile["id"] = profile_id
        if profile.get("llm"):
            _apply_provider(profile, provider_id)
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


_status_lock = threading.Lock()      # one real `--version` check at a time


def scanner_status(scanner_id):
    cached = _status_cache.get(scanner_id)
    if cached and time.time() - cached[0] < _STATUS_TTL:
        return dict(cached[1])
    with _status_lock:                # many requests at once must not each start a process
        cached = _status_cache.get(scanner_id)
        if cached and time.time() - cached[0] < _STATUS_TTL:
            return dict(cached[1])
        try:
            adapter = get_adapter(scanner_id)
            version = adapter.known_version()
            if version and os.path.exists(adapter.executable()):
                ok, detail = True, version            # already verified; no process needed
            else:
                ok, detail = adapter.check()
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
    if status["ready"] and profile.get("needs_provider"):
        status["ready"] = False
        status["detail"] = ("no LLM provider chosen: run ./install.sh, or "
                            "python3 goat.py llm set groq|openai|anthropic")
    if status["ready"] and env_file:
        env = read_env_file(env_file)
        key_var = profile.get("key_var", "SKILL_SCANNER_LLM_API_KEY")
        if not env.get(key_var):
            status["ready"] = False
            status["detail"] = ("no %s key for this scanner: put it in .scanners/%s as %s "
                                "(copy scanners/templates/%s.template, or run ./install.sh)"
                                % (profile.get("provider", "LLM"), env_file, key_var, env_file))
    return status


def all_status():
    return {
        "scanners": [scanner_status(s) for s in load_registry()],
        "profiles": [profile_status(p) for p in load_profiles()],
    }


# -- choosing the LLM provider -------------------------------------------------

def llm_scanners():
    """Scanners that have an LLM mode, as {id: registry entry}."""
    return dict((k, v) for k, v in load_registry().items() if v.get("llm"))


def llm_status():
    """The chosen provider and, per scanner, whether its key is in place (never the key itself)."""
    provider_id = current_provider()
    rows = []
    for scanner_id, entry in llm_scanners().items():
        row = {"scanner": scanner_id, "name": entry.get("name", scanner_id), "file": None, "has_key": False}
        if provider_id:
            row["file"] = key_file_for(scanner_id, provider_id)
            var = entry["llm"]["keys"].get(provider_id, "")
            row["has_key"] = bool(read_env_file(row["file"]).get(var))
            row["key_var"] = var
        rows.append(row)
    return {"provider": provider_id, "scanners": rows}


def set_provider(provider_id):
    """Choose the app-wide LLM provider. Returns (ok, message). Never touches existing keys."""
    providers = load_providers()
    provider_id = (provider_id or "").strip().lower()
    if provider_id not in providers:
        return False, "unknown provider %r (choose from: %s)" % (provider_id, ", ".join(providers))
    os.makedirs(SCANNERS_DIR, exist_ok=True)
    with open(PROVIDER_FILE, "w") as handle:
        handle.write(provider_id + "\n")
    for scanner_id in llm_scanners():                       # leave a template beside each missing key file
        template = os.path.join("scanners", "templates", key_file_for(scanner_id, provider_id) + ".template")
        copy = os.path.join(SCANNERS_DIR, key_file_for(scanner_id, provider_id) + ".template")
        if os.path.exists(template) and not os.path.exists(copy):
            shutil.copy(template, copy)
    _status_cache.clear()
    return True, "LLM provider set to %s" % providers[provider_id]["name"]


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


def _model_of(env):
    return env.get("SKILL_SCANNER_LLM_MODEL") or env.get("SKILLSPECTOR_MODEL") or ""


def _cache_path(adapter, profile, env, content_hash):
    # Keep this exact layout: changing it orphans every cached result, and LLM
    # results cost real tokens to recreate.
    parts = [CACHE_FORMAT, adapter.id, adapter.version(), profile["id"], profile.get("mode", ""),
             profile.get("policy", ""), env.get("SKILL_SCANNER_LLM_MODEL", ""), env.get("SKILLSPECTOR_MODEL", ""),
             content_hash]
    key = hashlib.sha256("|".join(parts).encode()).hexdigest()
    return os.path.join(CACHE_DIR, key + ".json")


_last_live = {}           # profile id -> when its last live (uncached) scan finished


def _wait_for_pacing(profile):
    """Free LLM plans cap tokens per minute. If the profile asks for a pause
    between scans, wait until enough time has passed since the last one."""
    pause = profile.get("min_seconds_between_scans", 0)
    last = _last_live.get(profile["id"])
    if pause and last:
        wait = pause - (time.time() - last)
        if wait > 0:
            time.sleep(wait)


def pacing_wait(profile_id):
    """Seconds until this profile may start another live scan (0 = now)."""
    profile = load_profiles().get(profile_id, {})
    pause, last = profile.get("min_seconds_between_scans", 0), _last_live.get(profile_id)
    if not pause or not last:
        return 0
    return max(0, int(pause - (time.time() - last) + 0.999))


# -- benchmark ledger --------------------------------------------------------
# The latest result per (profile, skill), so the benchmark can fill in as skills
# are scanned from the quiz page or the terminal. Errors are never recorded.

_ledger_lock = threading.Lock()


def _ledger_path(profile_id):
    return os.path.join(RESULTS_DIR, profile_id + ".json")


def _read_ledger(profile_id):
    try:
        with open(_ledger_path(profile_id)) as handle:
            return json.load(handle)
    except (OSError, ValueError):
        return {}


def _utc(timestamp):
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(timestamp))


def _record(profile, entry_id, result, fingerprint, when):
    if result.get("verdict") not in ("flagged", "clean"):
        return
    keep = {k: result.get(k) for k in (
        "verdict", "scanner", "scanner_version", "mode", "max_severity", "score",
        "recommendation", "overall_severity", "duration_seconds", "tokens")}
    keep["findings"] = len([f for f in result.get("findings", []) if f.get("severity") != "info"])
    with _ledger_lock:
        ledger = _read_ledger(profile["id"])
        ledger[entry_id] = {"entry": entry_id, "at": _utc(when), "fingerprint": fingerprint, "result": keep}
        os.makedirs(RESULTS_DIR, exist_ok=True)
        tmp = _ledger_path(profile["id"]) + ".tmp"
        with open(tmp, "w") as handle:
            json.dump(ledger, handle, indent=1)
        os.replace(tmp, _ledger_path(profile["id"]))        # atomic: never a half-written file


def _outcome(label, verdict):
    if label == "malicious":
        return "caught" if verdict == "flagged" else "missed"
    return "false alarm" if verdict == "flagged" else "correct clean"


def load_results():
    """The ledger joined with the corpus labels. Runs no scans."""
    entries = {e.id: e for e in load_entries(PASTURE_DIR)}
    rows, coverage = [], {}
    for profile_id, profile in load_profiles().items():
        try:
            version = get_adapter(profile["scanner"]).version()
        except Exception:
            version = ""
        env = read_env_file(profile.get("env_file")) if profile.get("env_file") else {}
        hashes = {entry_id: _content_hash(e.skill_dir) for entry_id, e in entries.items()}

        # Pick up scans that are in the cache but not yet in the ledger (made before
        # the ledger existed, or by another process). Costs nothing: no scanner runs.
        if version:
            adapter = get_adapter(profile["scanner"])
            for entry_id, content_hash in hashes.items():
                cache = _cache_path(adapter, profile, env, content_hash)
                fingerprint = {"scanner_version": version, "model": _model_of(env), "content_hash": content_hash}
                if os.path.exists(cache) and _read_ledger(profile_id).get(entry_id, {}).get("fingerprint") != fingerprint:
                    try:
                        with open(cache) as handle:
                            _record(profile, entry_id, json.load(handle), fingerprint, os.path.getmtime(cache))
                    except (OSError, ValueError):
                        pass

        ledger = _read_ledger(profile_id)
        fresh = stale = 0
        for entry_id, record in ledger.items():
            entry = entries.get(entry_id)
            if entry is None:
                continue                                      # skill was removed from the corpus
            current = {"scanner_version": version, "model": _model_of(env), "content_hash": hashes[entry_id]}
            is_stale = bool(version) and record["fingerprint"] != current
            fresh, stale = (fresh, stale + 1) if is_stale else (fresh + 1, stale)
            result = record["result"]
            label = entry.expected["verdict"]
            rows.append({
                "entry": entry_id, "profile": profile_id, "label": label,
                "category": entry.category, "tier": tier_of(entry.id)[0],
                "outcome": _outcome(label, result["verdict"]), "stale": is_stale, "at": record["at"],
                "verdict": result["verdict"], "max_severity": result.get("max_severity"),
                "score": result.get("score"), "recommendation": result.get("recommendation"),
                "overall_severity": result.get("overall_severity"), "tokens": result.get("tokens"),
            })
        coverage[profile_id] = {"scanned": fresh, "stale": stale, "total": len(entries)}
    return {"rows": rows, "coverage": coverage, "total": len(entries)}


def _prepare(entry_id, profile_id, use_cache=True):
    """Everything that can be answered without running a scanner.

    Returns (context, done). `done` is (result, from_cache) when the answer is
    already known (an error, or a saved result); otherwise it is None and
    `context` describes the live scan that is needed.
    """
    entry = find_entry(entry_id)
    if entry is None:
        return None, ({"verdict": "error", "error": "unknown entry %r" % entry_id}, False)
    profiles = load_profiles()
    if profile_id not in profiles:
        return None, ({"verdict": "error", "error": "unknown profile %r" % profile_id}, False)
    profile = profiles[profile_id]

    status = profile_status(profile_id)
    if not status["ready"]:
        return None, ({"verdict": "error", "scanner": profile["scanner"], "error": status["detail"]}, False)

    adapter = get_adapter(profile["scanner"])
    env = read_env_file(profile.get("env_file")) if profile.get("env_file") else {}
    content_hash = _content_hash(entry.skill_dir)
    cache = _cache_path(adapter, profile, env, content_hash)
    fingerprint = {"scanner_version": adapter.version(), "model": _model_of(env), "content_hash": content_hash}

    if use_cache and os.path.exists(cache):
        try:
            with open(cache) as handle:
                cached = json.load(handle)
            # Backfill the ledger from earlier scans the first time we see one.
            if _read_ledger(profile_id).get(entry_id, {}).get("fingerprint") != fingerprint:
                _record(profile, entry_id, cached, fingerprint, os.path.getmtime(cache))
            return None, (cached, True)
        except (OSError, ValueError):
            pass

    context = {"entry": entry, "entry_id": entry_id, "profile": profile, "adapter": adapter,
               "env": env, "cache": cache, "fingerprint": fingerprint}
    return context, None


def peek(entry_id, profile_id, use_cache=True):
    """The instant answer if there is one: (result, from_cache), else None.

    The web server calls this first and only queues the request for a live
    scan when it returns None, so cheap requests never wait behind a slow scan.
    """
    return _prepare(entry_id, profile_id, use_cache)[1]


def scan_entry(entry_id, profile_id, use_cache=True):
    """Scan one corpus entry with one profile. Returns (result_dict, from_cache)."""
    context, done = _prepare(entry_id, profile_id, use_cache)
    if done is not None:
        return done

    profile, entry = context["profile"], context["entry"]
    _wait_for_pacing(profile)
    try:
        result = context["adapter"].scan(entry.skill_dir, profile, extra_env=context["env"]).to_dict()
    finally:
        _last_live[profile["id"]] = time.time()
    if result["verdict"] != "error":          # never cache failures
        os.makedirs(CACHE_DIR, exist_ok=True)
        with open(context["cache"], "w") as handle:
            json.dump(result, handle)
        _record(profile, context["entry_id"], result, context["fingerprint"], time.time())
    return result, False


def scan_many(entry_ids, profile_id, on_result, use_cache=True):
    """Scan several entries in turn. Pacing between live scans happens in scan_entry."""
    for entry_id in entry_ids:
        result, cached = scan_entry(entry_id, profile_id, use_cache)
        on_result(entry_id, result, cached)
