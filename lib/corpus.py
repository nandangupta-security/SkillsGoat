import glob
import os
from dataclasses import dataclass

import yaml

PASTURE_DIR = "pasture"

# Tier isn't a folder — it's derived from an entry id's leading digit
# (e.g. "101-..." -> tier 100). See docs/TIERS.md for what each tier means.
TIER_NAMES = {
    "0": ("000", "decoys"),
    "1": ("100", "grazing"),
    "2": ("200", "climbing"),
    "3": ("300", "summit"),
}


class CorpusError(Exception):
    """A corpus entry is malformed in a way that breaks the tooling.

    Raised instead of letting a KeyError or FileNotFoundError surface as a
    traceback, so a contributor who mistypes a folder name gets told which
    folder and what's wrong with it. `goat.py` turns this into a one-line
    error and a non-zero exit.
    """


def tier_of(entry_id):
    try:
        return TIER_NAMES[entry_id[0]]
    except (KeyError, IndexError):
        valid = "/".join(sorted(TIER_NAMES))
        raise CorpusError(
            f"{entry_id}: id must start with a known tier digit ({valid}) — "
            f"see docs/TIERS.md"
        ) from None


@dataclass
class Entry:
    id: str
    category: str
    skill_path: str
    skill_dir: str
    expected: dict


def load_entries(pasture_dir=PASTURE_DIR, tolerant=False):
    """Load every corpus entry under `pasture_dir`.

    With `tolerant=True` an entry whose expected.yaml is missing or
    unparseable is returned with `expected=None` instead of raising, so
    `lint` can report every problem in one pass rather than stopping at
    the first. Everything else loads strictly.
    """
    entries = []

    # SKILL.md lives in <entry>/skill/ so scanners can be pointed at
    # <entry>/skill/ alone without also seeing expected.yaml, which sits one
    # level up as a sibling of skill/, never inside it.
    for skill_path in sorted(glob.glob(f"{pasture_dir}/**/skill/SKILL.md", recursive=True)):
        skill_dir = os.path.dirname(skill_path)
        folder = os.path.dirname(skill_dir)
        entry_id = os.path.basename(folder)
        expected_path = os.path.join(folder, "expected.yaml")

        expected = None
        if not os.path.exists(expected_path):
            if not tolerant:
                raise CorpusError(
                    f"{entry_id}: no expected.yaml next to skill/ — every entry "
                    f"needs one (expected at {expected_path})"
                )
        else:
            try:
                with open(expected_path) as f:
                    expected = yaml.safe_load(f)
            except yaml.YAMLError as exc:
                if not tolerant:
                    raise CorpusError(f"{entry_id}: expected.yaml is not valid YAML — {exc}") from None
            if expected is not None and not isinstance(expected, dict):
                if not tolerant:
                    raise CorpusError(
                        f"{entry_id}: expected.yaml must contain a mapping, "
                        f"got {type(expected).__name__}"
                    )
                expected = None

        entries.append(Entry(
            id=entry_id,
            category=os.path.basename(os.path.dirname(folder)),
            skill_path=skill_path,
            skill_dir=skill_dir,
            expected=expected,
        ))

    return entries
