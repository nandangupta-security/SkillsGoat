# Running the web UI

SkillsGoat has a browser version of the learning material, in two parts:

- **Learn** (`index.html`): one card per vulnerability category, with an
  explanation and real examples from the corpus, easiest to hardest.
- **Quiz** (`quiz.html`): skills in random order. Read each one and name
  the issue, or pick "Benign" if nothing is wrong. You get the answer and
  the reasoning straight after, plus a score by category at the end.

Everything is shown as text. Nothing in the corpus is ever executed.

## Requirements

- Python 3 (the same one the rest of SkillsGoat uses)
- The Python packages from `requirements.txt` (installed in a virtual environment, see below)
- Any modern browser

## Steps

From the repo root, using a virtual environment (recommended, so the
packages stay out of your system Python).

**First time only:**

    python3 -m venv venv
    source venv/bin/activate             # Windows: venv\Scripts\activate
    pip install -r requirements.txt

**Every time:**

    source venv/bin/activate             # skip if your prompt already shows (venv)
    python3 goat.py export               # builds ui/data/ from pasture/
    python3 goat.py serve                # starts the site

When you're done, stop the server with Ctrl+C and leave the environment
with `deactivate`.

Already have the packages installed globally? You can skip the virtual
environment and run the last two commands directly.

Then open <http://127.0.0.1:8765/>.

Use another port with `python3 goat.py serve --port 9000`. Stop the
server with Ctrl+C.

## Why `serve` is needed

The pages load their data with `fetch()`, and browsers block that for
files opened straight from disk (`file://`). If you double-click
`index.html` you'll see "Couldn't load the data". Run `serve` instead.

The server listens on `127.0.0.1` only, so it isn't reachable from other
machines.

## Using it

**Learn**
- Click **Start Learning** on a card. Use the tabs to switch between
  examples (by difficulty tier) and between the files in a skill.
- **Mark as understood** ticks the category off. Your progress is saved
  in your browser only.
- **Reset progress** (in the header, once you've ticked something) clears
  all ticks.

**Quiz**
- Press **Start quiz**. For each skill, choose an answer and press
  **Check answer**.
- **Restart quiz** (top right) starts over with a new random order.
- The results page shows your score per category and links back to the
  Learn page for the ones you missed.
- The quiz has one question per corpus entry, up to 20. The number grows
  as entries are added.

## After changing the corpus

`ui/data/` is generated from `pasture/`. Whenever you add or edit an
entry, run:

    python3 goat.py lint
    python3 goat.py export

then reload the page. Don't edit `ui/data/` by hand; `export` deletes and
rebuilds it.

## Files

    ui/index.html       the Learn page
    ui/quiz.html        the Quiz page
    ui/style.css        shared styling
    ui/data/
      corpus.json         categories and the list of entries
      entries/<id>.json   one skill's files and the explanation

## Troubleshooting

| Problem | Fix |
|---|---|
| "Couldn't load the data" | Run `python3 goat.py export`, then open the page through `serve`, not as a file |
| `ModuleNotFoundError: No module named 'yaml'` | The virtual environment isn't active. Run `source venv/bin/activate`, then `pip install -r requirements.txt` |
| `Address already in use` | Another process has the port. Use `--port` with a different number |
| New entry doesn't show up | Re-run `python3 goat.py export` and reload |
| Progress disappeared | It's stored per browser. Clearing site data or using a private window resets it |
