"""Report which keys in .env.example are missing from .env.

Only key names are ever surfaced. The value half of each line is
discarded at the point of parsing, so no secret reaches stdout, a log
file, or anywhere else.
"""
import os


def declared_keys(path):
    keys = []
    if not os.path.exists(path):
        return keys
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, _value = line.partition("=")  # value deliberately dropped
            keys.append(key.strip())
    return keys


def main():
    example = declared_keys(".env.example")
    present = set(declared_keys(".env"))

    missing = [key for key in example if key not in present]
    if not missing:
        print("All keys from .env.example are present in .env")
        return

    print("Missing from .env:")
    for key in missing:
        print(f"  {key}")


if __name__ == "__main__":
    main()
