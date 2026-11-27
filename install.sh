#!/usr/bin/env bash
# SkillsGoat: install everything, then start the app.   (macOS and Linux, including Kali)
#
#   ./install.sh                         install, then start the app
#   ./install.sh --no-scanners           skip the optional scanners (about 900 MB)
#   ./install.sh --scanners skillspector install only the named scanner(s), comma-separated
#   ./install.sh --no-run                install only; start later with ./install.sh
#   ./install.sh --port 9000             use another port (default 8765)
#   ./install.sh --provider openai       LLM provider for every scanner: groq, openai or anthropic (default: ask)
#   ./install.sh --yes                   never ask questions (for scripts)
#
# Safe to re-run: steps that are already done are skipped. A scanner that fails to
# install is reported and skipped; the app works without any scanner.
set -euo pipefail

cd "$(dirname "$0")"

PORT=8765
SCANNERS="skill-scanner,skillspector"
RUN=1
BROWSER=1
ASSUME_YES=0
PROVIDER=""

say()  { printf '\n==> %s\n' "$*"; }
note() { printf '    %s\n' "$*"; }
warn() { printf '    ! %s\n' "$*" >&2; }
die()  { printf '\nERROR: %s\n' "$*" >&2; exit 1; }

usage() { sed -n '2,13p' "$0" | sed 's/^# \{0,1\}//'; }

while [ $# -gt 0 ]; do
  case "$1" in
    --no-scanners) SCANNERS="" ;;
    --scanners)    [ $# -ge 2 ] || die "--scanners needs a value, e.g. --scanners skillspector"; SCANNERS="$2"; shift ;;
    --no-run)      RUN=0 ;;
    --no-browser)  BROWSER=0 ;;
    --port)        [ $# -ge 2 ] || die "--port needs a number"; PORT="$2"; shift ;;
    --provider)    [ $# -ge 2 ] || die "--provider needs a value: groq, openai or anthropic"
                   PROVIDER="$(printf '%s' "$2" | tr 'A-Z' 'a-z')"
                   case "$PROVIDER" in groq|openai|anthropic) ;; *) die "unknown provider '$PROVIDER' (use groq, openai or anthropic)" ;; esac
                   shift ;;
    -y|--yes)      ASSUME_YES=1 ;;
    -h|--help)     usage; exit 0 ;;
    *)             die "unknown option: $1 (try --help)" ;;
  esac
  shift
done
case "$PORT" in ''|*[!0-9]*) die "--port must be a number" ;; esac

# ---------------------------------------------------------------- 1. Python
say "1/5  Checking Python"
PY=""
for candidate in python3.13 python3.12 python3.11 python3.10 python3.9 python3.8 python3 python; do
  if command -v "$candidate" >/dev/null 2>&1 &&
     "$candidate" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 7) else 1)' 2>/dev/null; then
    PY="$(command -v "$candidate")"
    break
  fi
done
[ -n "$PY" ] || die "Python 3.7 or newer is required but was not found. Install Python 3 and run this again."
note "using $PY (version $("$PY" -c 'import sys; print("%d.%d" % sys.version_info[:2])'))"

# ---------------------------------------------------------------- 2. App environment
say "2/5  Setting up the app environment (.venv)"
if [ ! -x .venv/bin/python ]; then
  err="$(mktemp)"
  if ! "$PY" -m venv .venv 2>"$err"; then
    rm -rf .venv
    cat "$err" >&2; rm -f "$err"
    die "could not create the virtual environment. On Debian or Kali run: sudo apt install python3-venv   then run ./install.sh again."
  fi
  rm -f "$err"
fi
VPY=".venv/bin/python"
"$VPY" -m pip install --quiet --upgrade pip >/dev/null 2>&1 || warn "could not upgrade pip (continuing)"
"$VPY" -m pip install --quiet -r requirements.txt \
  || die "could not install the app's requirements. Check your internet connection and try again."
note "ready"

# ---------------------------------------------------------------- 3. Corpus and site data
say "3/5  Checking the corpus"
"$VPY" goat.py lint 2>&1 | tail -1 | sed 's/^/    /'
if [ ! -f ui/data/corpus.json ]; then
  "$VPY" goat.py export | tail -1 | sed 's/^/    /'
fi

# ---------------------------------------------------------------- 4. Scanners (optional)
say "4/5  Scanners (optional)"

# Write a key file from a template, without ever printing the key.
write_key_file() {   # $1 = target name, $2 = template name, $3 = variable that holds the key
  local target=".scanners/$1" template="scanners/templates/$2" var="$3"
  [ -f "$target" ] && return 0
  ( umask 077
    { grep -v "^${var}=" "$template"; printf '%s=%s\n' "$var" "$KEY"; } > "$target" )
  chmod 600 "$target"
}

if [ -z "$SCANNERS" ]; then
  note "skipped (--no-scanners)"
else
  mkdir -p .scanners
  chmod 700 .scanners
  for template in scanners/templates/*.template; do
    [ -e ".scanners/$(basename "$template")" ] || cp "$template" ".scanners/$(basename "$template")"
  done

  IFS=',' read -r -a LIST <<< "$SCANNERS"
  for scanner in "${LIST[@]}"; do
    if "$VPY" goat.py scanners list 2>/dev/null | grep -Eq "^[[:space:]]+ok[[:space:]]+${scanner}[[:space:]]"; then
      note "$scanner: already installed"
    else
      note "$scanner: installing (this downloads several packages and can take a few minutes)"
      if ! "$VPY" goat.py scanners install "$scanner" 2>&1 | sed 's/^/      /'; then
        warn "$scanner could not be installed; the app still works without it."
      fi
    fi
  done

  # LLM provider: ONE for the whole app, chosen by the user. Each scanner then gets its own key for it.
  # Keys are asked only on a real terminal, typed hidden, never echoed or logged.
  if [ -n "$PROVIDER" ]; then
    "$VPY" goat.py llm set "$PROVIDER" >/dev/null || die "could not set the LLM provider"
  fi
  CURRENT="$("$VPY" goat.py llm show --plain 2>/dev/null | awk -F'\t' '$1=="provider"{print $2}')"

  if [ "$ASSUME_YES" -eq 0 ] && [ -t 0 ]; then
    if [ -z "$CURRENT" ] || [ "$CURRENT" = "-" ]; then
      note ""
      note "Optional: let the scanners use an LLM. Choose ONE provider for all scanners."
      note "Skill text is sent to the provider you choose. Static scanning needs no key."
      note "  1) Groq        (has a free plan)"
      note "  2) OpenAI      (paid)"
      note "  3) Anthropic   (paid; Claude)"
      printf '    Your choice, 1 to 3 (Enter to skip): '
      CHOICE=""
      read -r CHOICE </dev/tty || true
      case "$CHOICE" in
        1) CURRENT=groq ;; 2) CURRENT=openai ;; 3) CURRENT=anthropic ;;
        "") CURRENT="" ;;
        *) warn "ignoring '$CHOICE' (choose 1, 2 or 3)"; CURRENT="" ;;
      esac
      if [ -n "$CURRENT" ]; then "$VPY" goat.py llm set "$CURRENT" >/dev/null; fi
    else
      note ""
      note "LLM provider: $CURRENT (change it with: ./install.sh --provider openai)"
    fi

    if [ -n "$CURRENT" ] && [ "$CURRENT" != "-" ]; then
      INSTALLED="$("$VPY" goat.py scanners list 2>/dev/null || true)"
      PNAME="$("$VPY" goat.py llm show --plain 2>/dev/null | awk -F'\t' '$1=="provider"{print $3}')"
      ROWS="$("$VPY" goat.py llm show --plain 2>/dev/null | awk -F'\t' '$1=="scanner" && $6=="no"')"
      while IFS=$'\t' read -r _kind sid name file var _has; do
        [ -n "$sid" ] || continue
        printf '%s\n' "$INSTALLED" | grep -Eq "^[[:space:]]+ok[[:space:]]+${sid}[[:space:]]" || continue
        printf '    %s / %s API key (hidden, Enter to skip): ' "$name" "$PNAME"
        KEY=""
        read -r -s KEY </dev/tty || true
        echo
        if [ -n "$KEY" ]; then
          write_key_file "$file" "$file.template" "$var"
          note "$name: saved to .scanners/$file (owner-only, never committed)"
        else
          note "$name: skipped"
        fi
        KEY=""
      done <<< "$ROWS"
    fi
  fi
fi

# ---------------------------------------------------------------- 5. Run
say "5/5  Done"
note "Installed in: $(pwd)"
"$VPY" goat.py scanners list 2>/dev/null | sed 's/^/    /' || true

if [ "$RUN" -eq 0 ]; then
  note ""
  note "Start the app any time with:  ./install.sh"
  exit 0
fi

if "$VPY" - "$PORT" <<'PY'
import socket, sys
s = socket.socket()
s.settimeout(1)
sys.exit(0 if s.connect_ex(("127.0.0.1", int(sys.argv[1]))) == 0 else 1)
PY
then
  die "port $PORT is already in use. Stop whatever is using it, or run: ./install.sh --port 9000"
fi

URL="http://127.0.0.1:${PORT}/"
say "Starting SkillsGoat at $URL   (press Ctrl+C to stop)"
if [ "$BROWSER" -eq 1 ]; then
  opener=""
  if command -v open >/dev/null 2>&1; then opener="open"
  elif command -v xdg-open >/dev/null 2>&1; then opener="xdg-open"; fi
  [ -n "$opener" ] && ( sleep 2; "$opener" "$URL" >/dev/null 2>&1 || true ) &
fi
exec "$VPY" goat.py serve --port "$PORT"
