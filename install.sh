#!/usr/bin/env bash
set -euo pipefail

# ── helpers ────────────────────────────────────────────────────────────────
info()  { printf '\033[1;34m[info]\033[0m  %s\n' "$*"; }
ok()    { printf '\033[1;32m[ ok ]\033[0m  %s\n' "$*"; }
warn()  { printf '\033[1;33m[warn]\033[0m  %s\n' "$*"; }
die()   { printf '\033[1;31m[err ]\033[0m  %s\n' "$*" >&2; exit 1; }

# ── Python ─────────────────────────────────────────────────────────────────
PYTHON=$(command -v python3 || command -v python || true)
[[ -z "$PYTHON" ]] && die "Python 3 not found. Install it and re-run."

PY_VER=$("$PYTHON" -c 'import sys; print(sys.version_info[:2])')
info "Using Python: $PYTHON ($PY_VER)"

"$PYTHON" -c 'import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)' \
  || die "Python 3.10+ is required (found $PY_VER)."

# ── libmagic (system library) ───────────────────────────────────────────────
check_libmagic() {
  "$PYTHON" -c "import ctypes.util; exit(0 if ctypes.util.find_library('magic') else 1)" 2>/dev/null
}

if ! check_libmagic; then
  warn "libmagic not found — attempting to install..."
  if command -v brew &>/dev/null; then
    brew install libmagic
  elif command -v apt-get &>/dev/null; then
    sudo apt-get install -y libmagic1
  elif command -v dnf &>/dev/null; then
    sudo dnf install -y file-libs
  elif command -v zypper &>/dev/null; then
    sudo zypper install -y libmagic1
  else
    die "Cannot install libmagic automatically. Install it manually and re-run."
  fi
fi
check_libmagic || die "libmagic still not found after install attempt."
ok "libmagic found"

# ── virtual environment ─────────────────────────────────────────────────────
VENV_DIR="$(dirname "$0")/venv"

if [[ ! -d "$VENV_DIR" ]]; then
  info "Creating virtual environment at $VENV_DIR"
  "$PYTHON" -m venv "$VENV_DIR"
else
  info "Virtual environment already exists at $VENV_DIR"
fi

VENV_PYTHON="$VENV_DIR/bin/python"
VENV_PIP="$VENV_DIR/bin/pip"

# ── Python dependencies ─────────────────────────────────────────────────────
info "Installing Python dependencies..."
"$VENV_PIP" install --upgrade pip --quiet
"$VENV_PIP" install -r "$(dirname "$0")/requirements.txt" --quiet
ok "Dependencies installed"

# ── smoke test ──────────────────────────────────────────────────────────────
info "Running smoke test..."
"$VENV_PYTHON" -c "import rpmfile, magic, zstandard" \
  || die "Smoke test failed — one or more packages failed to import."
ok "Smoke test passed"

# ── done ────────────────────────────────────────────────────────────────────
printf '\n'
ok "Setup complete! Run the tool with:"
printf '    ./cmp-rpm <rpm_a> <rpm_b>\n'
printf '\n'
printf '  Or activate the venv manually:\n'
printf '    source venv/bin/activate\n'
printf '    python compare_rpm_sizes.py <rpm_a> <rpm_b>\n'
printf '\n'
