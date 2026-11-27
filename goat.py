import argparse
import json
import os
import sys

from lib.corpus import PASTURE_DIR, load_entries, tier_of
from lib.schema import load_taxonomy, validate_expected


def c(text, code):
    """Wrap text in an ANSI color code, unless stdout isn't a terminal."""
    if not sys.stdout.isatty():
        return text
    return f"\033[{code}m{text}\033[0m"

SKILL_TEMPLATE = """---
name: {slug}
description: >
  TODO: describe what this skill does, including the risky or benign
  behavior this entry is meant to demonstrate.
---

# {title}

TODO: body text.
"""

EXPECTED_TEMPLATE = """verdict: benign  # or: malicious
categories: []    # e.g. [prompt-injection] -- must match taxonomy.yaml
why: >
  TODO: one or two sentences explaining the verdict. This is shown to the
  learner in quiz mode after they guess, so write it for them.
"""


def cmd_quiz(args):
    entries = load_entries()
    total = len(entries)
    correct_count = 0

    for i, entry in enumerate(entries, start=1):
        print(c(f"\n[{i} of {total}]", "36;1"))
        print(c("=" * 60, "36"))
        with open(entry.skill_path) as f:
            print(f.read())
        print(c("=" * 60, "36"))

        guess = input("Is this skill benign or malicious? ").strip().lower()
        answer = entry.expected["verdict"]
        if guess == answer:
            correct_count += 1
            print(c("Correct!", "32;1"))
        else:
            print(c(f"Not quite. This one is: {answer}", "31;1"))

        input("\n(press enter to see the category) ")
        categories = entry.expected.get("categories") or []
        print("Categories:", ", ".join(categories) if categories else "(none)")

        input("\n(press enter to see why) ")
        print("Why:", entry.expected["why"])
        print()

    print(c("=" * 60, "36"))
    print(c(f"Score: {correct_count} / {total} correct", "1"))
    print(c("=" * 60, "36"))


def cmd_lint(args):
    taxonomy = load_taxonomy()
    seen_ids = set()
    errors = []

    for entry in load_entries():
        if entry.id in seen_ids:
            errors.append(f"{entry.id}: duplicate entry id")
        seen_ids.add(entry.id)

        errors += [f"{entry.id}: {e}" for e in validate_expected(entry.expected, taxonomy)]

    if errors:
        print(f"{len(errors)} problem(s) found:")
        for e in errors:
            print(" -", e)
        raise SystemExit(1)

    print(f"All {len(seen_ids)} entries look good.")


def _table_rows(entries):
    lines = ["| id | verdict | categories | why |", "|---|---|---|---|"]
    for entry in entries:
        categories = ", ".join(entry.expected.get("categories") or []) or "-"
        why = entry.expected["why"].strip().replace("\n", " ")
        lines.append(f"| {entry.id} | {entry.expected['verdict']} | {categories} | {why} |")
    return lines


def cmd_index(args):
    entries = load_entries()

    by_category = {}
    by_tier = {}
    for entry in entries:
        by_category.setdefault(entry.category, []).append(entry)
        by_tier.setdefault(tier_of(entry.id), []).append(entry)

    category_lines = ["# Corpus index — by category", ""]
    for category in sorted(by_category):
        category_lines.append(f"## {category}")
        category_lines += _table_rows(by_category[category])
        category_lines.append("")

    tier_lines = ["# Corpus index — by tier", ""]
    for number, name in sorted(by_tier):
        tier_lines.append(f"## Tier {number} — {name}")
        tier_lines += _table_rows(by_tier[(number, name)])
        tier_lines.append("")

    category_path = os.path.join(PASTURE_DIR, "INDEX_BY_CATEGORY.md")
    tier_path = os.path.join(PASTURE_DIR, "INDEX_BY_TIER.md")

    with open(category_path, "w") as f:
        f.write("\n".join(category_lines) + "\n")
    with open(tier_path, "w") as f:
        f.write("\n".join(tier_lines) + "\n")

    print(f"Wrote {category_path}")
    print(f"Wrote {tier_path}")


UI_DIR = "ui"
UI_DATA_DIR = os.path.join(UI_DIR, "data")


def _parse_blocks(text):
    """Tiny markdown subset -> [{"type": "p"|"h"|"ul", ...}].

    Supports "## " headings, "- " bullet lists and plain paragraphs. Inline
    **bold** and `code` are left in the text for the UI to render.
    """
    blocks = []
    para = []   # lines of the paragraph being built
    items = []  # bullet items being built

    def flush():
        if para:
            blocks.append({"type": "p", "text": " ".join(" ".join(para).split())})
            para.clear()
        if items:
            blocks.append({"type": "ul", "items": [" ".join(i.split()) for i in items]})
            items.clear()

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            flush()
        elif stripped.startswith("## "):
            flush()
            blocks.append({"type": "h", "text": stripped[3:].strip()})
        elif stripped.startswith("- "):
            if para:
                flush()
            items.append(stripped[2:])
        elif items:
            items[-1] += " " + stripped  # wrapped bullet continuation
        else:
            para.append(stripped)
    flush()
    return blocks


def _read_category_readme(category):
    """Return (title, blocks) from pasture/<category>/README.md."""
    path = os.path.join(PASTURE_DIR, category, "README.md")
    if not os.path.exists(path):
        return category, []
    with open(path) as f:
        text = f.read().strip()
    lines = text.splitlines()
    title = category
    if lines and lines[0].startswith("# "):
        title = lines[0][2:].strip()
        text = "\n".join(lines[1:]).strip()
    return title, _parse_blocks(text)


def _skill_files(skill_dir):
    """Every text file under skill/, SKILL.md first."""
    files = []
    for root, _, names in os.walk(skill_dir):
        for name in sorted(names):
            full = os.path.join(root, name)
            rel = os.path.relpath(full, skill_dir)
            try:
                with open(full) as f:
                    files.append({"path": rel, "content": f.read()})
            except UnicodeDecodeError:
                continue
    files.sort(key=lambda x: (x["path"] != "SKILL.md", x["path"]))
    return files


def _write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(obj, f, indent=1, ensure_ascii=False)
        f.write("\n")


def cmd_export(args):
    """Write ui/data/: corpus.json (index) + entries/<id>.json (skill text)."""
    import shutil
    import yaml
    with open("taxonomy.yaml") as f:
        categories = list(yaml.safe_load(f)) + ["benign"]

    # Rebuild from scratch so deleted entries don't leave stale files behind.
    shutil.rmtree(UI_DATA_DIR, ignore_errors=True)

    entries_by_category = {}
    for entry in load_entries():
        number, tier_name = tier_of(entry.id)
        entries_by_category.setdefault(entry.category, []).append({
            "id": entry.id,
            "tier": number,
            "tierName": tier_name,
            "verdict": entry.expected["verdict"],
            "severity": entry.expected.get("severity"),
        })
        _write_json(os.path.join(UI_DATA_DIR, "entries", f"{entry.id}.json"), {
            "id": entry.id,
            "category": entry.category,
            "why": " ".join(entry.expected["why"].split()),
            "files": _skill_files(entry.skill_dir),
        })

    index = []
    for category in categories:
        title, blocks = _read_category_readme(category)
        index.append({
            "slug": category,
            "title": title,
            "blocks": blocks,
            "entries": sorted(entries_by_category.get(category, []), key=lambda e: e["id"]),
        })
    _write_json(os.path.join(UI_DATA_DIR, "corpus.json"), index)
    print(f"Wrote {UI_DATA_DIR}/corpus.json and {sum(len(c['entries']) for c in index)} entry files")


def cmd_serve(args):
    """Serve ui/ on localhost so the pages can fetch their JSON data."""
    import functools
    import hmac
    import http.server
    import secrets
    import threading

    # Scanner endpoints. They can spend an LLM key, so they are locked down:
    #  - Host must be this server (blocks DNS-rebinding from other sites)
    #  - POST needs a per-run token that only a page served from here can read
    #  - the browser sends an entry id and a profile name, never a file path
    token = secrets.token_urlsafe(24)
    allowed_hosts = {f"127.0.0.1:{args.port}", f"localhost:{args.port}"}
    scan_lock = threading.Lock()          # one live scan at a time
    # Live scans wait in a short queue: one running and up to three waiting. A
    # request beyond that is refused at once (HTTP 429) instead of piling up a
    # waiting thread, and a real scan, for every request a script can send.
    MAX_LIVE_QUEUE = 4
    gate = {"pending": 0}
    gate_lock = threading.Lock()

    class Handler(http.server.SimpleHTTPRequestHandler):
        def _json(self, status, payload, headers=None):
            body = json.dumps(payload).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            for name, value in (headers or {}).items():
                self.send_header(name, value)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def _api_allowed(self):
            if self.headers.get("Host", "") not in allowed_hosts:
                self._json(403, {"error": "forbidden host"})
                return False
            return True

        def do_GET(self):
            if not self.path.startswith("/api/"):
                return super().do_GET()
            if not self._api_allowed():
                return
            if self.path == "/api/token":
                return self._json(200, {"token": token})
            if self.path == "/api/scanners":
                try:
                    from lib import scanning
                    return self._json(200, scanning.all_status())
                except Exception as exc:  # scanner support is optional
                    return self._json(200, {"scanners": [], "profiles": [], "error": str(exc)})
            if self.path == "/api/results":          # the benchmark ledger; runs no scans
                try:
                    from lib import scanning
                    return self._json(200, scanning.load_results())
                except Exception as exc:
                    return self._json(200, {"rows": [], "coverage": {}, "total": 0, "error": str(exc)})
            if self.path.startswith("/api/scan-status"):
                from urllib.parse import parse_qs, urlsplit
                profile = parse_qs(urlsplit(self.path).query).get("profile", [""])[0]
                try:
                    from lib import scanning
                    return self._json(200, {"wait_seconds": scanning.pacing_wait(profile)})
                except Exception:
                    return self._json(200, {"wait_seconds": 0})
            self._json(404, {"error": "not found"})

        def do_POST(self):
            if self.path != "/api/scan":
                return self._json(404, {"error": "not found"})
            if not self._api_allowed():
                return
            origin = self.headers.get("Origin")
            if origin and origin.split("://", 1)[-1] not in allowed_hosts:
                return self._json(403, {"error": "forbidden origin"})
            if not hmac.compare_digest(self.headers.get("X-SkillsGoat-Token", ""), token):
                return self._json(403, {"error": "missing or wrong token"})
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if length > 4096:
                    return self._json(413, {"error": "request too large"})
                body = json.loads(self.rfile.read(length) or b"{}")
                entry, profile = str(body["entry"]), str(body["profile"])
            except (ValueError, KeyError, TypeError):
                return self._json(400, {"error": "expected JSON with 'entry' and 'profile'"})
            try:
                from lib import scanning
                use_cache = not body.get("fresh")
                # 1) Instant answers (errors, saved results) never wait behind a slow scan.
                done = scanning.peek(entry, profile, use_cache)
                if done is not None:
                    result, cached = done
                    result["cached"] = cached
                    return self._json(200, result)
                # 2) A live scan is needed: bounded queue, one runs at a time.
                with gate_lock:
                    busy = gate["pending"] >= MAX_LIVE_QUEUE
                    if not busy:
                        gate["pending"] += 1
                if busy:
                    return self._json(429, {"verdict": "error", "cached": False,
                                            "error": "The server is busy with other scans. Wait a minute and try again."},
                                      headers={"Retry-After": "30"})
                try:
                    with scan_lock:
                        result, cached = scanning.scan_entry(entry, profile, use_cache)
                finally:
                    with gate_lock:
                        gate["pending"] -= 1
                result["cached"] = cached
                self._json(200, result)
            except Exception as exc:  # a scanner problem must never crash the server
                self._json(200, {"verdict": "error", "error": f"scan failed: {exc}"})

    def warm_up():                    # check the scanners once at start, not inside the first requests
        try:
            from lib import scanning
            scanning.all_status()
        except Exception:
            pass
    threading.Thread(target=warm_up, daemon=True).start()

    handler = functools.partial(Handler, directory=UI_DIR)
    # 127.0.0.1 only: this site displays deliberately malicious skill text.
    with http.server.ThreadingHTTPServer(("127.0.0.1", args.port), handler) as server:
        print(f"Serving on http://127.0.0.1:{args.port}/  (Ctrl+C to stop)")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print()


def cmd_new(args):
    taxonomy = load_taxonomy()
    valid_categories = taxonomy | {"benign"}
    if args.category not in valid_categories:
        raise SystemExit(f"'{args.category}' is not in taxonomy.yaml (or 'benign')")

    tier_prefix = args.tier.zfill(3)
    if tier_prefix not in {"000", "100", "200", "300"}:
        raise SystemExit(f"'{args.tier}' is not a known tier (000, 100, 200, 300)")

    existing_ids = [
        int(entry.id.split("-", 1)[0])
        for entry in load_entries()
        if tier_of(entry.id)[0] == tier_prefix
    ]
    next_id = max(existing_ids, default=int(tier_prefix)) + 1

    category_dir = os.path.join(PASTURE_DIR, args.category)
    os.makedirs(category_dir, exist_ok=True)
    readme_path = os.path.join(category_dir, "README.md")
    if not os.path.exists(readme_path):
        with open(readme_path, "w") as f:
            f.write(f"# {args.category}\n\nTODO: describe this category.\n")

    slug = args.name.strip().lower().replace(" ", "-")
    folder = os.path.join(category_dir, f"{next_id:03d}-{slug}")
    skill_dir = os.path.join(folder, "skill")
    os.makedirs(skill_dir)

    with open(os.path.join(skill_dir, "SKILL.md"), "w") as f:
        f.write(SKILL_TEMPLATE.format(slug=slug, title=args.name.title()))

    with open(os.path.join(folder, "expected.yaml"), "w") as f:
        f.write(EXPECTED_TEMPLATE)

    print(f"Created {folder}/")


def cmd_scanners(args):
    """list / doctor / install external scanners (all optional)."""
    # Imported here, not at the top: a missing or broken scanner must never
    # stop goat.py from starting.
    from lib import scanning

    if args.action == "install":
        if not args.scanner:
            raise SystemExit("usage: goat.py scanners install <scanner-id>   (see: goat.py scanners list)")
        ok, message = scanning.install_scanner(args.scanner)
        print(("OK: " if ok else "FAILED: ") + message)
        raise SystemExit(0 if ok else 1)

    status = scanning.all_status()
    print("Scanners")
    for s in status["scanners"]:
        print(f"  {'ok ' if s['ready'] else 'no '} {s['id']:<16} {s['detail']}")
    print("\nProfiles")
    for p in status["profiles"]:
        where = f"sends skill text to {p['provider'] or 'a remote service'}" if p["sends_data_off_machine"] else "runs locally"
        state = "ready" if p["ready"] else "not ready"
        print(f"  {p['id']:<22} {state:<10} {p['label']}  [{where}]")
        if not p["ready"]:
            print(f"  {'':<22} {'':<10} -> {p['detail']}")
    if args.action == "doctor" and not any(p["ready"] for p in status["profiles"]):
        print("\nNo profile is ready. Everything else in SkillsGoat still works.")


def cmd_llm(args):
    """Choose the one LLM provider for every scanner, and show which keys are in place."""
    from lib import scanning

    if args.action == "set":
        if not args.provider:
            raise SystemExit("usage: goat.py llm set <provider>   (groq, openai or anthropic)")
        ok, message = scanning.set_provider(args.provider)
        print(("OK: " if ok else "FAILED: ") + message)
        if not ok:
            raise SystemExit(1)
    status = scanning.llm_status()
    providers = scanning.load_providers()
    if args.plain:                          # for install.sh: no key values, only names and yes/no
        pid = status["provider"]
        print("\t".join(["provider", pid or "-", providers[pid]["name"] if pid else "-"]))
        for row in status["scanners"]:
            print("\t".join(["scanner", row["scanner"], row["name"], row["file"] or "-",
                             row.get("key_var", "-"), "yes" if row["has_key"] else "no"]))
        return
    if not status["provider"]:
        print("No LLM provider chosen. Choose one: python3 goat.py llm set groq|openai|anthropic")
        return
    print(f"LLM provider: {providers[status['provider']]['name']}  (used by every scanner's Static + LLM mode)")
    for row in status["scanners"]:
        mark = "key set    " if row["has_key"] else "key MISSING"
        print(f"  {row['name']:<22} {mark}  .scanners/{row['file']}  ({row['key_var']})")
    if not all(r["has_key"] for r in status["scanners"]):
        print("Add a key by running ./install.sh, or copy the .template beside each file and fill it in.")


def cmd_scan(args):
    """Scan corpus entries with a scanner profile and compare to the labels."""
    from lib import scanning

    entries = {e.id: e for e in load_entries()}
    if args.all:
        ids = sorted(entries)
    elif args.entry:
        ids = args.entry
    else:
        raise SystemExit("choose --entry <id> (repeatable) or --all")
    unknown = [i for i in ids if i not in entries]
    if unknown:
        raise SystemExit(f"unknown entry id(s): {', '.join(unknown)}")

    status = scanning.profile_status(args.profile)
    if not status["ready"]:
        raise SystemExit(f"profile '{args.profile}' is not ready: {status['detail']}")
    if status["sends_data_off_machine"]:
        print(f"Note: this profile sends skill text to {status['provider'] or 'a remote service'}.")

    tally = {"caught": 0, "missed": 0, "false alarm": 0, "correct clean": 0, "error": 0}

    def show(entry_id, result, cached):
        malicious = entries[entry_id].expected["verdict"] == "malicious"
        verdict = result["verdict"]
        if verdict == "error":
            outcome = "error"
        elif malicious:
            outcome = "caught" if verdict == "flagged" else "missed"
        else:
            outcome = "false alarm" if verdict == "flagged" else "correct clean"
        tally[outcome] += 1
        extra = result.get("error") or result.get("max_severity", "")
        tokens = (result.get("tokens") or {}).get("total_tokens")
        suffix = (f", {tokens} tokens" if tokens else "") + (", cached" if cached else "")
        print(f"  {entry_id:<34} {outcome:<14} ({verdict}, {extra}{suffix})")
        if args.raw and result.get("raw"):
            print(json.dumps(result["raw"], indent=2))

    print(f"Scanning {len(ids)} entr{'y' if len(ids) == 1 else 'ies'} with profile '{args.profile}'")
    scanning.scan_many(ids, args.profile, show, use_cache=not args.no_cache)
    print("\n" + ", ".join(f"{k}: {v}" for k, v in tally.items() if v))


def main():
    parser = argparse.ArgumentParser(prog="goat")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("quiz", help="quiz yourself on the corpus").set_defaults(func=cmd_quiz)
    subparsers.add_parser("lint", help="check the corpus is internally consistent").set_defaults(func=cmd_lint)
    subparsers.add_parser("index", help="regenerate pasture/INDEX_BY_*.md").set_defaults(func=cmd_index)

    subparsers.add_parser("export", help="write ui/data/*.json for the web UI").set_defaults(func=cmd_export)

    serve_parser = subparsers.add_parser("serve", help="serve the web UI on localhost")
    serve_parser.add_argument("--port", type=int, default=8765)
    serve_parser.set_defaults(func=cmd_serve)

    new_parser = subparsers.add_parser("new", help="scaffold a new corpus entry")
    new_parser.add_argument("--category", required=True, help="e.g. prompt-injection, benign")
    new_parser.add_argument("--tier", required=True, help="e.g. 100, 200, 300")
    new_parser.add_argument("--name", required=True, help="e.g. 'payload in config'")
    new_parser.set_defaults(func=cmd_new)

    scanners_parser = subparsers.add_parser("scanners", help="list, check or install optional scanners")
    scanners_parser.add_argument("action", choices=["list", "doctor", "install"])
    scanners_parser.add_argument("scanner", nargs="?", help="scanner id, for install (e.g. skill-scanner)")
    scanners_parser.set_defaults(func=cmd_scanners)

    llm_parser = subparsers.add_parser("llm", help="choose the LLM provider used by every scanner")
    llm_parser.add_argument("action", choices=["show", "set"])
    llm_parser.add_argument("provider", nargs="?", help="groq, openai or anthropic (for set)")
    llm_parser.add_argument("--plain", action="store_true", help=argparse.SUPPRESS)
    llm_parser.set_defaults(func=cmd_llm)

    scan_parser = subparsers.add_parser("scan", help="scan corpus entries with a scanner profile")
    scan_parser.add_argument("--profile", default="skill-scanner-static", help="profile id (default: skill-scanner-static)")
    scan_parser.add_argument("--entry", action="append", help="entry id; repeat for several")
    scan_parser.add_argument("--all", action="store_true", help="scan every entry")
    scan_parser.add_argument("--no-cache", action="store_true", help="ignore cached results")
    scan_parser.add_argument("--raw", action="store_true", help="also print the scanner's raw output")
    scan_parser.set_defaults(func=cmd_scan)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
