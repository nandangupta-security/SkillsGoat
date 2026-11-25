# Scanners

SkillsGoat can run real skill scanners against the corpus, so you can see what a
scanner catches and misses, skill by skill. Scanners are **optional**: if none is
installed (or one breaks), Learn, Quiz, `export`, `lint` and `serve` all keep
working. Only the scanner features report a problem.

Scanners are never copied into this repo. They are downloaded on demand into
`.scanners/` (gitignored), in their own virtual environment, at a pinned version.

## Quick start

    python3 goat.py scanners install skill-scanner   # one-time, needs internet
    python3 goat.py scanners list                    # what is installed and ready
    python3 goat.py scan --all --profile static      # scan the whole corpus, offline

`scan` prints, for every skill, whether the scanner **caught** it, **missed** it,
raised a **false alarm** on a benign skill, or was **correct clean**. A scan that
could not finish is an **error**, never "clean".

Use `--entry <id>` (repeatable) for specific skills, `--raw` to also print the
scanner's own unedited output, and `--no-cache` to ignore cached results.

## Profiles

A profile is a scanner plus a mode, defined in `scanners/profiles.yaml`:

| Profile | What it does | Sends skill text off your machine? |
|---|---|---|
| `static` | Rules and code analysis only | No |
| `groq-judge` | Static + LLM: rules plus an LLM (set up here with Groq's free plan) | Yes, to Groq |

The static mode catches code-level tricks. The LLM also understands plain
English, so it catches problems that rules cannot, such as a skill told to obey
instructions found in fetched content.

## Using the LLM (Static + LLM)

LLM profiles read their key from a file in `.scanners/` that you create yourself.
The key never goes in this repo, the browser or the chat.

    cp .scanners/groq.env.template .scanners/groq.env
    chmod 600 .scanners/groq.env
    # open .scanners/groq.env and paste your key after SKILL_SCANNER_LLM_API_KEY=

To use a different provider, copy a profile in `scanners/profiles.yaml`, point it at
a new env file, and set `SKILL_SCANNER_LLM_MODEL` (and `SKILL_SCANNER_LLM_BASE_URL`
if the provider needs one) in that file. No code changes are needed. Examples of
model names: `anthropic/<model>`, `openai/<model>`, `ollama/<model>` (local, no key).

Free-tier limits apply. Profiles can set `min_seconds_between_scans` so a batch
`scan --all` waits between skills instead of hitting the provider's rate limit.

## Requirements

- The scanner needs **Python 3.11 to 3.14**. SkillsGoat itself only needs 3.7+.
  The installer looks for a suitable Python and says so if it cannot find one.
- Internet access to download the scanner (once) and, for hosted LLM profiles, to
  reach the provider.

### Kali / Debian notes

- System-wide `pip install` is blocked there ("externally managed environment").
  The scanner installs into its own environment, so that is fine. For SkillsGoat's
  own dependency use a venv or `sudo apt install python3-yaml`.
- If creating the environment fails, install the venv package:
  `sudo apt install python3-venv`.
- The web server listens on 127.0.0.1 only. Open the browser inside the VM, or
  forward the port yourself.

## Adding another scanner

1. Add an entry to `scanners/scanners.yaml` (name, pinned version, install, run).
2. Add `scanners/adapters/<name>.py` with a class based on `ScannerAdapter` that
   implements `check()` and `scan()` and returns a `ScanResult`
   (see `scanners/adapters/base.py`).
3. Add one or more profiles in `scanners/profiles.yaml`.

Paid or cloud scanners follow the same pattern; their adapter calls the vendor's
API with a key read from a file in `.scanners/`.

## Notes and limits

- A scan with no findings is **not** a guarantee that a skill is safe.
- The scanner is only ever pointed at the skill text. It does not run skills.
- Results are cached in `.scanners/cache/`, keyed by scanner version, profile,
  model and the skill's contents, so unchanged skills are not re-scanned.
