#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────
#  Watson — one-click installer for macOS / Linux
# ──────────────────────────────────────────────────────────────────
set -e

CYAN='\033[0;36m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
info()  { echo -e "${CYAN}[Watson]${NC} $*"; }
ok()    { echo -e "${GREEN}[✓]${NC} $*"; }
warn()  { echo -e "${YELLOW}[!]${NC} $*"; }
err()   { echo -e "${RED}[✗]${NC} $*"; exit 1; }

echo ""
echo -e "${CYAN}╔══════════════════════════════════════╗${NC}"
echo -e "${CYAN}║   Watson — AI Bug Bounty Assistant   ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════╝${NC}"
echo ""

# ── Check Python ──────────────────────────────────────────────────
info "Checking Python..."
command -v python3 &>/dev/null || err "Python 3 not found. Install from https://python.org"
PY_VER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
info "Found Python $PY_VER"
[[ "${PY_VER%%.*}" -ge 3 && "${PY_VER#*.}" -ge 9 ]] || warn "Python 3.9+ recommended (found $PY_VER)"

# ── Create virtual environment ────────────────────────────────────
info "Creating virtual environment (.venv)..."
python3 -m venv .venv
ok "Virtual environment ready"

# ── Install Python dependencies ───────────────────────────────────
info "Installing Python dependencies..."
.venv/bin/pip install --quiet --upgrade pip
.venv/bin/pip install --quiet -r requirements.txt
ok "Dependencies installed"

# ── Copy .env if missing ──────────────────────────────────────────
if [ ! -f .env ]; then
    cp .env.example .env
    warn ".env created — edit it and add your API key(s) before starting."
else
    ok ".env already exists — skipping."
fi

# ── Check for JAR ─────────────────────────────────────────────────
JAR=$(find extension/ -name "*.jar" 2>/dev/null | head -1)

echo ""
if [ -n "$JAR" ]; then
    ok "Extension JAR found: $JAR"
    JAR_PATH="$JAR"
else
    warn "No JAR found in extension/."
    warn "Download watson-burp.jar from the GitHub Releases page and place it in extension/"
    JAR_PATH="extension/watson-burp.jar  (download from Releases)"
fi

# ── Done ──────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}══════════════════════════════════════════${NC}"
echo -e "${GREEN}  Watson installation complete!           ${NC}"
echo -e "${GREEN}══════════════════════════════════════════${NC}"
echo ""
echo -e "${CYAN}Next steps:${NC}"
echo ""
echo "  1. Edit .env — add your API key"
echo "     Gemini is FREE → https://aistudio.google.com/apikey"
echo ""
echo "  2. Start the Watson backend:"
echo "     ./start.sh"
echo ""
echo "  3. Load the Burp extension:"
echo "     Burp Suite → Extensions → Add → Java extension"
echo "     File: $JAR_PATH"
echo ""
