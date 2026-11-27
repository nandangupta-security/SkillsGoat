# Scanners

SkillsGoat can run real skill scanners against the corpus, so you can see what a
scanner catches and misses, skill by skill. Scanners are **optional**: if none is
installed (or one breaks), Learn, Quiz, `export`, `lint` and `serve` all keep
working. Only the scanner features report a problem.

Scanners are never copied into this repo. They are downloaded on demand into
`.scanners/` (gitignored), in their own virtual environment, at a pinned version.

## Quick start

`./install.sh` does all of this for you, including the optional key prompt. The manual steps are:

    python3 goat.py scanners install skill-scanner   # one-time, needs internet
    python3 goat.py scanners install skillspector    # optional second scanner
    python3 goat.py scanners list                    # what is installed and ready
    python3 goat.py scan --all --profile skill-scanner-static   # scan the whole corpus, offline

`scan` prints, for every skill, whether the scanner **caught** it, **missed** it,
raised a **false alarm** on a benign skill, or was **correct clean**. A scan that
could not finish is an **error**, never "clean".

Use `--entry <id>` (repeatable) for specific skills, `--raw` to also print the
scanner's own unedited output, and `--no-cache` to ignore cached results.

## Profiles

Each scanner has two profiles, defined in `scanners/profiles.yaml`:

| Profile | What it does | Sends skill text off your machine? |
|---|---|---|
| `skill-scanner-static` | Cisco skill-scanner: rules and code analysis only | No |
| `skill-scanner-llm` | Cisco skill-scanner plus an LLM (about 5,000 tokens a skill) | Yes, to your chosen provider |
| `skillspector-static` | NVIDIA SkillSpector: static analysis only | No (see the note below) |
| `skillspector-llm` | SkillSpector plus about four LLM calls per skill | Yes, to your chosen provider |

The static mode catches code-level tricks. The LLM also understands plain
English, so it catches problems that rules cannot, such as a skill told to obey
instructions found in fetched content.

## Using the LLM (Static + LLM)

**You choose one LLM provider for the whole app: Groq (has a free plan), OpenAI or
Anthropic (Claude).** Every scanner's "Static + LLM" mode then uses that provider, but
**each scanner has its own key**, so you can use separate keys.

    python3 goat.py llm set openai     # choose the provider (or let ./install.sh ask you)
    python3 goat.py llm show           # which provider, and which scanners still need a key

Each scanner's key lives in its own file in `.scanners/` (gitignored), named
`<scanner>-<provider>.env`:

| Provider | Cisco skill-scanner | SkillSpector |
|---|---|---|
| Groq | `skill-scanner-groq.env` | `skillspector-groq.env` |
| OpenAI | `skill-scanner-openai.env` | `skillspector-openai.env` |
| Anthropic | `skill-scanner-anthropic.env` | `skillspector-anthropic.env` |

`./install.sh` asks for the provider once, then for each scanner's key (typed hidden).
To do it by hand, copy the matching file from `scanners/templates/` (named
`<scanner>-<provider>.env.template`) to `.scanners/` without `.template`, `chmod 600`
it, and put the key after the `=` sign. The key never goes in this repo, the browser or
the chat.

Switching provider later keeps the keys you already saved; just run
`python3 goat.py llm set <provider>` again. Other providers (a gateway, Ollama, Bedrock)
work by adding an entry under `providers:` in `scanners/scanners.yaml` and a template.

The model each template uses is a default you can change inside the key file.
**Only the Groq setup has been tested end to end; the OpenAI and Anthropic templates follow
each scanner's documentation but have not been run against a real key.**

SkillSpector makes about four LLM calls per skill. Measured on Groq with
`openai/gpt-oss-120b`: roughly 9,500 tokens for a skill with only a `SKILL.md` and about
16,000 for one with a script. On Groq's reported free limits (about 8,000 tokens a minute,
200,000 a day) a single scan is fine, but the whole corpus will not fit in one day.

SkillSpector normally sends up to 10 LLM requests at once. On a free plan that burst is
refused with rate-limit errors, so SkillsGoat sets `SKILLSPECTOR_MAX_LLM_CONCURRENCY=1`
(one request at a time) for LLM scans. The OpenAI and Anthropic templates raise it to 4,
since paid plans allow it; edit the key file to change it.

On a free-plan provider (Groq), SkillsGoat also waits between scans, so a batch stays
under the per-minute token cap. Paid providers are not paced.

## The benchmark ledger

Every scan, from a quiz card or from `goat.py scan`, is recorded in `.scanners/results/`
(one file per profile, latest result per skill). The quiz cards show "Added to the
benchmark: ... 12 of 24 skills scanned" after each scan, and `GET /api/results` returns
the ledger joined with each skill's label, category and tier. Nothing is scanned by
reading it.

- Errors are never recorded, so a failed scan can't count as clean or as a miss.
- A result is marked **outdated** (and not counted) if the scanner version, the model or
  the skill's own files change after it was recorded.
- Different profiles may have scanned different skills, so compare scanners only on the
  skills they have all scanned.

## Requirements

- Cisco skill-scanner needs **Python 3.11 to 3.14**; SkillSpector needs **3.12 or 3.13**.
  SkillsGoat itself only needs 3.7+. The installer looks for a suitable Python for
  each scanner and says so if it cannot find one.
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

## How SkillSpector's results are read

SkillSpector grades each skill 0 to 100 and gives a recommendation:

| Score | Overall severity | Recommendation | Its own advice |
|---|---|---|---|
| 0 to 20 | low | SAFE | allow |
| 21 to 50 | medium | CAUTION | warn the user |
| 51 to 100 | high or critical | DO NOT INSTALL | block |

SkillSpector leaves the strictness of the gate to the tool using it. In SkillsGoat,
**CAUTION and above count as flagged** (`flag_at: CAUTION` in `profiles.yaml`). The
panel shows both the overall severity and the worst single finding, which can differ:
a skill can score CAUTION (overall medium) while one finding is high.

A scan that did not inspect the whole skill is shown as an error, never as clean.

**Offline note:** SkillSpector can look up a skill's declared dependencies on OSV.dev.
SkillsGoat points it at an empty local folder, so static mode makes no network calls.
The trade-off is that its known-vulnerable-dependency check finds nothing; none of the
corpus skills depend on this.

## Adding another scanner

1. Add an entry to `scanners/scanners.yaml` (name, pinned version, install, run).
2. Add `scanners/adapters/<name>.py` with a class based on `ScannerAdapter` that
   implements `check()` and `scan()` and returns a `ScanResult`
   (see `scanners/adapters/base.py`).
3. Add its two profiles (static and, if it has an LLM mode, `llm: true`) in `scanners/profiles.yaml`.

Paid or cloud scanners follow the same pattern; their adapter calls the vendor's
API with a key read from a file in `.scanners/`.

## Notes and limits

- A scan with no findings is **not** a guarantee that a skill is safe.
- The scanner is only ever pointed at the skill text. It does not run skills.
- Results are cached in `.scanners/cache/`, keyed by scanner version, profile,
  model and the skill's contents, so unchanged skills are not re-scanned.
