#!/bin/bash

# Nyxx Installation Script

# ── Project root ───────────────────────────────────────────────────────────
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# ── Detect Python binary ───────────────────────────────────────────────────
echo "Checking Python environment..."
PYTHON_COMMAND=""
if command -v python3 &> /dev/null; then
    PYTHON_COMMAND="python3"
elif command -v python &> /dev/null; then
    PYTHON_COMMAND="python"
else
    echo "Error: Python 3 is not installed or not in PATH. Please install Python 3."
    exit 1
fi

# ── Create venv if missing ─────────────────────────────────────────────────
if [ ! -d "$SCRIPT_DIR/.venv" ]; then
    echo "Creating Python virtual environment..."
    $PYTHON_COMMAND -m venv "$SCRIPT_DIR/.venv"
fi

# ── Resolve venv paths (Windows vs Unix) ──────────────────────────────────
# This is the fix for the critical bug — activation path is now chosen
# based on what actually exists, not assumed.
if [ -f "$SCRIPT_DIR/.venv/Scripts/activate" ]; then
    # Windows (Git Bash / MSYS2)
    ACTIVATE="$SCRIPT_DIR/.venv/Scripts/activate"
    PYTHON_BIN="$SCRIPT_DIR/.venv/Scripts/python"
else
    # Linux / macOS
    ACTIVATE="$SCRIPT_DIR/.venv/bin/activate"
    PYTHON_BIN="$SCRIPT_DIR/.venv/bin/python"
fi

# ── Activate and install dependencies ─────────────────────────────────────
echo "Activating virtual environment and installing dependencies..."
# shellcheck source=/dev/null
source "$ACTIVATE" || {
    echo "Error: Failed to activate virtual environment."
    echo "       Expected activation script at: $ACTIVATE"
    exit 1
}

pip install -r "$SCRIPT_DIR/requirements.txt" || {
    echo "Error: Failed to install Python dependencies."
    exit 1
}
echo "✓ Python dependencies installed."

# ── Seed ~/.nyxx config directory ─────────────────────────────────────────
echo "Setting up Nyxx config directory..."
mkdir -p "$HOME/.nyxx"

if [ ! -f "$HOME/.nyxx/jumps.json" ]; then
    echo "[]" > "$HOME/.nyxx/jumps.json"
    echo "✓ Created ~/.nyxx/jumps.json"
fi

if [ ! -f "$HOME/.nyxx/memos.json" ]; then
    echo "[]" > "$HOME/.nyxx/memos.json"
    echo "✓ Created ~/.nyxx/memos.json"
fi

if [ ! -f "$HOME/.nyxx/config.json" ]; then
    cat > "$HOME/.nyxx/config.json" << 'EOF_CONFIG'
{
  "sky_theme": "starry night",
  "ground_theme": "city",
  "sky_enabled": true,
  "ground_enabled": true
}
EOF_CONFIG
    echo "✓ Created ~/.nyxx/config.json"
fi

# ── Shell detection and wrapper injection ──────────────────────────────────
SHELL_NAME=$(basename "$SHELL")

case "$SHELL_NAME" in
    bash)
        CONFIG_FILE="$HOME/.bashrc"
        ;;
    zsh)
        CONFIG_FILE="$HOME/.zshrc"
        ;;
    pwsh|powershell)
        echo ""
        echo "PowerShell detected."
        echo "Please manually add the following line to your \$PROFILE file:"
        echo "  (open it with: notepad \$PROFILE)"
        echo ""
        if command -v cygpath &> /dev/null; then
            PS1_PATH="$(cygpath -w "$SCRIPT_DIR/shell_integrations/nyxx.ps1")"
        else
            PS1_PATH="$SCRIPT_DIR/shell_integrations/nyxx.ps1"
        fi
        echo "  . '$PS1_PATH'"
        echo ""
        echo "Then restart PowerShell or run: . \$PROFILE"
        exit 0
        ;;
    *)
        echo ""
        echo "Unsupported shell: $SHELL_NAME"
        echo "Please manually add the nyxx() function to your shell config."
        echo "You can find the function template in: shell_integrations/nyxx.sh"
        exit 1
        ;;
esac

# ── Inject wrapper function ────────────────────────────────────────────────
if grep -qF "nyxx() {" "$CONFIG_FILE" 2>/dev/null; then
    echo "✓ Nyxx wrapper already exists in $CONFIG_FILE — skipping."
else
    echo "Adding Nyxx function to $CONFIG_FILE..."
    cat >> "$CONFIG_FILE" << EOF_NAVI_FUNCTION

# Nyxx Integration
nyxx() {
  # nyxx jump add / nyxx memo add need a live terminal for prompts —
  # run directly without output capture.
  if [[ "\$1" == "jump" && "\$2" == "add" ]] || [[ "\$1" == "memo" && "\$2" == "add" ]]; then
    PYTHONPATH="${SCRIPT_DIR}" "${PYTHON_BIN}" -m src.nyxx.main "\$@"
    return
  fi

  # All other commands: capture the single output line and act on its prefix.
  # Curses draws to /dev/tty directly so it never pollutes this capture.
  local output
  output=\$(PYTHONPATH="${SCRIPT_DIR}" "${PYTHON_BIN}" -m src.nyxx.main "\$@" 2>/dev/null)
  if [[ -n "\$output" ]]; then
    case "\$output" in
      CD:*)   cd "\${output#CD:}" ;;
      EXEC:*) eval "\${output#EXEC:}" ;;
      *)      cd "\$output" ;;
    esac
  fi
}
EOF_NAVI_FUNCTION
    echo "✓ Nyxx function added to $CONFIG_FILE."
fi

# ── Done ───────────────────────────────────────────────────────────────────
echo ""
echo "✓ Nyxx installation complete!"
echo ""
echo "  To activate in your current session, run:"
echo "    source $CONFIG_FILE"
echo ""
echo "  Then try:"
echo "    nyxx          — open home screen"
echo "    nyxx cd       — open directory navigator"
echo "    nyxx jump     — open saved locations"
echo "    nyxx memo     — open saved commands"
echo "    nyxx theme    — change theme"
echo ""