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


def tier_of(entry_id):
    number, name = TIER_NAMES[entry_id[0]]
    return number, name


@dataclass
class Entry:
    id: str
    category: str
    skill_path: str
    skill_dir: str
    expected: dict


def load_entries(pasture_dir=PASTURE_DIR):
    entries = []

    # SKILL.md lives in <entry>/skill/ so scanners can be pointed at
    # <entry>/skill/ alone without also seeing expected.yaml, which sits one
    # level up as a sibling of skill/, never inside it.
    for skill_path in sorted(glob.glob(f"{pasture_dir}/**/skill/SKILL.md", recursive=True)):
        skill_dir = os.path.dirname(skill_path)
        folder = os.path.dirname(skill_dir)
        expected_path = os.path.join(folder, "expected.yaml")

        with open(expected_path) as f:
            expected = yaml.safe_load(f)

        entries.append(Entry(
            id=os.path.basename(folder),
            category=os.path.basename(os.path.dirname(folder)),
            skill_path=skill_path,
            skill_dir=skill_dir,
            expected=expected,
        ))

    return entries
