import subprocess


def commits_since_last_tag():
    last_tag = subprocess.run(
        ["git", "describe", "--tags", "--abbrev=0"],
        capture_output=True, text=True,
    ).stdout.strip()

    range_spec = f"{last_tag}..HEAD" if last_tag else "HEAD"
    result = subprocess.run(
        ["git", "log", range_spec, "--pretty=format:%s"],
        capture_output=True, text=True,
    )
    return result.stdout.splitlines()
