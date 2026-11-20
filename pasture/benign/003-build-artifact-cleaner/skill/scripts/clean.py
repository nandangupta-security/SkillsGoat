"""Delete regenerable build output from the current project.

Deliberately conservative: a fixed list of regenerable directory names,
every candidate resolved and confirmed to sit inside the project root
before deletion, and a confirmation prompt showing exactly what will go.
"""
import os
import shutil

# Regenerable output only — no source directories, nothing unrecoverable.
ARTIFACT_DIRS = ("dist", "build", "__pycache__", ".pytest_cache", ".mypy_cache")


def find_artifacts(root):
    root = os.path.realpath(root)
    found = []
    for dirpath, dirnames, _filenames in os.walk(root):
        for name in list(dirnames):
            if name not in ARTIFACT_DIRS:
                continue
            candidate = os.path.realpath(os.path.join(dirpath, name))
            # Refuse anything resolving outside the project root: a
            # symlinked dist/ must not turn this into an arbitrary delete.
            if candidate == root or not candidate.startswith(root + os.sep):
                continue
            found.append(candidate)
            dirnames.remove(name)
    return sorted(found)


def main():
    root = os.getcwd()
    targets = find_artifacts(root)
    if not targets:
        print("No build artifacts found.")
        return

    print("These directories will be deleted:")
    for path in targets:
        print(f"  {os.path.relpath(path, root)}")

    if input("Delete them? [y/N] ").strip().lower() != "y":
        print("Nothing deleted.")
        return

    for path in targets:
        shutil.rmtree(path)
    print(f"Deleted {len(targets)} directories.")


if __name__ == "__main__":
    main()
