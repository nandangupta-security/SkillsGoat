import argparse
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
    os.makedirs(folder)

    with open(os.path.join(folder, "SKILL.md"), "w") as f:
        f.write(SKILL_TEMPLATE.format(slug=slug, title=args.name.title()))

    with open(os.path.join(folder, "expected.yaml"), "w") as f:
        f.write(EXPECTED_TEMPLATE)

    print(f"Created {folder}/")


def main():
    parser = argparse.ArgumentParser(prog="goat")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("quiz", help="quiz yourself on the corpus").set_defaults(func=cmd_quiz)
    subparsers.add_parser("lint", help="check the corpus is internally consistent").set_defaults(func=cmd_lint)
    subparsers.add_parser("index", help="regenerate pasture/INDEX_BY_*.md").set_defaults(func=cmd_index)

    new_parser = subparsers.add_parser("new", help="scaffold a new corpus entry")
    new_parser.add_argument("--category", required=True, help="e.g. prompt-injection, benign")
    new_parser.add_argument("--tier", required=True, help="e.g. 100, 200, 300")
    new_parser.add_argument("--name", required=True, help="e.g. 'payload in config'")
    new_parser.set_defaults(func=cmd_new)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
