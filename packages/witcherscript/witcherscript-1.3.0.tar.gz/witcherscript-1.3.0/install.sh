#!/bin/bash
# WitcherScript Installation Script
# Installs WitcherScript for standalone use

set -e

INSTALL_DIR="$HOME/.local/bin"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                 WitcherScript Installation                     ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Create .local/bin if it doesn't exist
mkdir -p "$INSTALL_DIR"

# Copy files
echo "📝 Setting up WitcherScript..."
cp "$SCRIPT_DIR/witcher" "$INSTALL_DIR/witcher"
cp "$SCRIPT_DIR/witcher_interpreter.py" "$INSTALL_DIR/witcher_interpreter.py"

chmod +x "$INSTALL_DIR/witcher"

echo "✓ Files installed to: $INSTALL_DIR"
echo ""

# Check if ~/.local/bin is in PATH
if [[ ":$PATH:" == *":$INSTALL_DIR:"* ]]; then
    echo "✓ $INSTALL_DIR is in your PATH"
else
    echo "⚠ $INSTALL_DIR is NOT in your PATH"
    echo ""
    echo "Add this line to your ~/.bashrc or ~/.zshrc:"
    echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
    echo ""
fi

echo "✓ Installation complete!"
echo ""
echo "Usage:"
echo "  witcher program.witcher"
echo "  witcher example_programs/01_hello_world.witcher"
echo ""
echo "To uninstall:"
echo "  rm $INSTALL_DIR/witcher $INSTALL_DIR/witcher_interpreter.py"
