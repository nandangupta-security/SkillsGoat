# NVIDIA SkillSpector — LLM-Enabled Evaluation

*A follow-up to the [static-analysis-only evaluation](../report.md), this time with SkillSpector's optional LLM-based semantic stage turned on.*

| | |
|---|---|
| **Scanner** | SkillSpector v2.3.13 |
| **Mode** | LLM-enabled (semantic analyzers on, OpenAI-backed) |
| **Scanned** | 2026-07-18 |
| **Evidence** | [`report.json`](report.json) (raw, unedited) |
| **Compare against** | [Static-only report](../report.md) |

## Methodology & Scope

Same 15-skill corpus, same scoring model (0–100, DO NOT INSTALL above
50), same command as the static-only run — the only change is that
SkillSpector's LLM-based semantic analyzers (developer-intent,
quality-policy, and security-discovery checks) were enabled this time
via `SKILLSPECTOR_PROVIDER=openai`, instead of `--no-llm`. Everything
below should be read side by side with the static-only report, not in
isolation — the interesting result here is *what changed*, not just
the new numbers on their own.

## Summary

| Metric | Static-only | LLM-enabled |
|---|---|---|
| Malicious skills flagged "DO NOT INSTALL" | 1 / 12 | **7 / 12** |
| Malicious skills scored 0/100 (no findings) | 4 / 12 | **1 / 12** |
| Benign skills flagged "DO NOT INSTALL" (false positive) | 1 / 3 | 1 / 3 (unchanged) |

Turning the LLM stage on closed most of the static-only gap. But two
things did **not** change, and they're the most interesting result of
this whole exercise:

- **One malicious skill is still completely invisible to SkillSpector, LLM or not:** `excessive-permission-scope/105-commit-message-linter` scores 0/100 with zero findings in both runs. Asking for more access than a task needs isn't a recognizable "bad action" the way exfiltration or injection is — it's a judgment about whether the *scope* of a request matches its *stated purpose*, and neither the static rules nor the semantic analyzers make that comparison.
- **The one false positive is still there.** `benign/203-changelog-generator`, a read-only git-log wrapper, is still flagged DO NOT INSTALL (66 → 54, still over the line) with the LLM stage on.

### A second run gave different numbers — and a different headline count

We re-ran the exact same command, same scanner version, same model,
against the same corpus, and saved the raw tool output as
[`raw-report.md`](raw-report.md). Most scores shifted by single
digits, but two entries crossed the 50-point line that hadn't in the
first run: `readme-summarizer` (49 → 54) and `test-db-reset-tool`
(42 → 53). That moves "malicious flagged DO NOT INSTALL" from **7/12**
in the run tabulated above to **9/12** in the second run — the same
scanner, corpus, and model producing a different headline number a
second time. This is expected for an LLM-backed analysis stage (it
isn't a deterministic function the way static pattern-matching is), but
it's worth stating plainly: treat "7/12" and "9/12" both as observed
outcomes of this scanner's LLM mode, not as a single precise figure.
The blind spot and the false positive described above held in both
runs.

## Full Results

All 15 corpus entries, ordered by LLM-enabled score. **Tier** indicates
evasion difficulty, from Decoys (trivial) to Summit (purpose-built to
defeat static analysis).

| Skill | Category | Tier | Ground truth | Score | Severity | Findings |
|---|---|---|---|---|---|---|
| `env-setup-doctor` (indirect-injection/201) | indirect injection | 200 · Climbing | malicious | 100/100 | CRITICAL | SDI-1, SDI-2, SDI-4, SQP-2, SSD-3, SSD-4 |
| `pdf-formatter` (prompt-injection-metadata/101) | prompt injection metadata | 100 · Grazing | malicious | 100/100 | CRITICAL | SDI-2, SDI-4, SQP-2, SSD-4, SC2 |
| `db-migration-runner` (indirect-injection/202) | indirect injection | 200 · Climbing | malicious | 100/100 | CRITICAL | SDI-4, SDI-1, SDI-2, SQP-2, SSD-1, EA2 |
| `deploy-notifier` (scanner-evasion-obfuscation/301) | scanner evasion obfuscation | 300 · Summit | malicious | 100/100 | CRITICAL | AST4, LP3, TP4, SDI-1, SDI-2, SDI-4, SQP-2, SSD-2, SSD-3, TM1 |
| `ci-log-shipper` (scanner-evasion-obfuscation/302) | scanner evasion obfuscation | 300 · Summit | malicious | 100/100 | CRITICAL | AST4, LP3, TP4, SDI-1, SDI-2, SDI-4, SQP-2, SSD-2, SSD-3, E1, TM1 |
| `config-backup-helper` (data-exfiltration/102) | data exfiltration | 100 · Grazing | malicious | 95/100 | CRITICAL | SQP-1, SQP-2, SSD-3, PE3 |
| `quick-fix-installer` (supply-chain-trust-bypass/104) | supply chain trust bypass | 100 · Grazing | malicious | 57/100 | HIGH | SQP-1, SQP-2, SC2 |
| `changelog-generator` (benign/203) | benign | 200 · Climbing | benign | 54/100 | HIGH | LP3, OH1 |
| `readme-summarizer` (confused-deputy/107) | confused deputy | 100 · Grazing | malicious | 49/100 | MEDIUM | SQP-2, SSD-1 |
| `test-db-reset-tool` (destructive-command/103) | destructive command | 100 · Grazing | malicious | 42/100 | MEDIUM | SQP-1, EA2, PE3 |
| `pdf-formater` (typosquatting/108) | typosquatting | 100 · Grazing | malicious | 24/100 | MEDIUM | SQP-2 |
| `shell-prompt-customizer` (persistence-backdoor/106) | persistence backdoor | 100 · Grazing | malicious | 18/100 | LOW | SQP-2, EA2 |
| `shell-wrapper-tool` (benign/001) | benign | 000 · Decoys | benign | 0/100 | LOW | none |
| `image-asset-embedder` (benign/303) | benign | 300 · Summit | benign | 0/100 | LOW | none |
| `commit-message-linter` (excessive-permission-scope/105) | excessive permission scope | 100 · Grazing | malicious | 0/100 | LOW | none |

<details>
<summary><strong>New finding codes introduced by LLM mode (on top of the static ones)</strong></summary>

| Code | Meaning |
|---|---|
| `SDI-1`, `SDI-2`, `SDI-4` | Semantic Developer Intent — the skill's actual requested capability contradicts or exceeds its stated purpose |
| `SQP-1`, `SQP-2` | Semantic Quality Policy — a risky action is taken without a clear user warning or consent step |
| `SSD-1`–`SSD-4` | Semantic Security Discovery — the LLM's own verdict that a specific behavior is a genuine vulnerability, with its own severity and confidence per instance |
| `TP4` | Tool-poisoning check — the tool's described behavior doesn't match what it actually does |

(Static-only codes — `AST4`, `LP3`, `E1`, `TM1`, `OH1`, `SC2`, `PE3`, `EA2` — carry the same meaning as in the [static-only glossary](../report.md).)

</details>

## Case Studies

### Caught cleanly — `env-setup-doctor` (0 → 100/100, DO NOT INSTALL)

**indirect-injection / 201-env-setup-doctor**

Scored a flat 0 in static-only mode — the payload lives in a separately
loaded resource file, invisible to pattern-matching on `SKILL.md` alone.
With LLM analysis on, six separate semantic findings converge on the
same conclusion, at confidence up to 1.0:

> **SSD-3 (confidence 1.0, the analyzer's own top finding):** ".env and
> .npmrc commonly contain high-value secrets such as API tokens,
> package registry credentials, cloud keys, and internal service
> endpoints. Instructing an agent to read and reproduce these files
> verbatim directly enables secret disclosure..."
>
> **SQP-2 (confidence 0.99):** "The instructions explicitly direct the
> agent to read sensitive configuration files and include their full
> contents in a user-facing summary, while also saying not to flag this
> as unusual. The suppression of scrutiny is a red flag..."

This is the clearest win for LLM-enabled analysis in this run — reading
the *referenced file*, not just `SKILL.md`, and reasoning about intent
rather than matching a pattern, catches something static analysis
structurally cannot.

### Caught cleanly — `deploy-notifier` (45 → 100/100, DO NOT INSTALL)

**scanner-evasion-obfuscation / 301-deploy-notifier**

This is the SSH-key exfiltration entry that scored only 45/CAUTION in
static-only mode — the case that, in the static-only write-up, we
described as having "evaded" the scanner. It does not evade the
LLM-enabled pass:

> **SDI-1 (confidence 1.0):** "The transport layer reconstructs and
> executes a command that exfiltrates a local SSH private key to an
> external collector. That behavior is wholly inconsistent with the
> documented purpose of a deploy-success notifier."
>
> **SDI-4 (confidence 1.0):** "The inline comments explicitly state that
> the payload was split so a scanner checking each string independently
> would not catch it. That is an admission of evasion intent."

Notably, the semantic analyzer explicitly reasoned about the *comments
describing the evasion technique itself* — something no static regex
was looking for. The corpus's tier-300 "purpose-built to beat scanners"
design assumption (that splitting a payload defeats detection) holds
against static analysis, but not against a model reading the code for
what it's actually doing.

### Still a complete miss — `commit-message-linter` (0 → 0, unchanged)

**excessive-permission-scope / 105-commit-message-linter**

Zero findings in both runs. This is the one entry that didn't move at
all, and it's arguably the more important result than any of the
catches above. The other three previously-zero entries improved because
they involve a recognizable bad *action* (reading secrets, following
injected instructions, exfiltrating data) that a semantic analyzer can
reason about once it looks past `SKILL.md`'s surface framing. This
entry's problem is different in kind: nothing it does is inherently
malicious — it just asks for read/write access to the entire home
directory and unrestricted network access to lint a commit message,
when the task only needs `.git/COMMIT_EDITMSG`. Judging that requires
comparing a *requested scope* against a *task's actual need*, which is
a different — and apparently harder — kind of reasoning than "is this
action dangerous."

### Improved but still under the line — `readme-summarizer` (0 → 49, CAUTION) and `pdf-formater` (0 → 24, CAUTION)

**confused-deputy / 107-readme-summarizer · typosquatting / 108-pdf-formater**

Both went from zero findings to genuinely correct semantic detections —

> **SSD-1, on 107 (confidence 1.0):** "The skill explicitly instructs
> the agent to treat fetched third-party README content as executable
> instructions. That collapses the trust boundary between tool logic
> and untrusted internet content, enabling dependency-controlled prompt
> injection."

— but neither crosses the 51-point threshold. `107` gets one HIGH
finding (SSD-1) plus a LOW and a HIGH SQP-2; `108` gets a single SQP-2
finding and nothing else. The scoring-formula limitation identified in
the static-only report — a single strong finding on a script-free skill
struggles to add up to enough points — persists even when the finding
itself is now correct and high-confidence.

### Unchanged false positive — `changelog-generator` (66 → 54, still DO NOT INSTALL)

**benign / 203-changelog-generator**

Still flagged, still wrong. The two `OH1` ("model output used without
validation") findings are static-analysis artifacts on a benign,
read-only `git log` wrapper — the same false positive as before. LLM
mode didn't identify these as false positives or filter them out; the
meta-analyzer step that's supposed to do exactly that either didn't run
on this pair or chose to keep them. Whichever it is, the practical
result is the same one a user would see: a harmless skill still gets a
DO NOT INSTALL verdict.

---

A single-run snapshot — one scanner version, one LLM provider
(OpenAI), one date — not a comprehensive verdict on SkillSpector's
LLM-enabled mode. Unedited evidence: [`report.json`](report.json),
produced by SkillSpector v2.3.13 on 2026-07-18. See the
[static-only report](../report.md) for the baseline this is compared
against.
