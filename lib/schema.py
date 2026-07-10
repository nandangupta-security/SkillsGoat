import yaml

VALID_VERDICTS = {"benign", "malicious"}
VALID_SEVERITIES = {"low", "medium", "high"}


def load_taxonomy(path="taxonomy.yaml"):
    with open(path) as f:
        return set(yaml.safe_load(f))


def validate_expected(expected, taxonomy):
    errors = []

    verdict = expected.get("verdict")
    if verdict not in VALID_VERDICTS:
        errors.append(f"verdict must be one of {VALID_VERDICTS}, got {verdict!r}")

    categories = expected.get("categories") or []
    unknown = [c for c in categories if c not in taxonomy]
    if unknown:
        errors.append(f"unknown categories {unknown} — add them to taxonomy.yaml first")

    if verdict == "malicious" and not categories:
        errors.append("malicious entries must have at least one category")

    if not (expected.get("why") or "").strip():
        errors.append("missing or empty 'why'")

    severity = expected.get("severity")
    if severity is not None and severity not in VALID_SEVERITIES:
        errors.append(f"severity must be one of {VALID_SEVERITIES}, got {severity!r}")

    return errors
