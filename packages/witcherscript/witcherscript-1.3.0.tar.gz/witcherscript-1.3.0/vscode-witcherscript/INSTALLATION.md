# VS Code Extension Installation Guide

## Quick Start

### Option 1: Install from Folder (Recommended for Development)

1. **Find your VS Code extensions folder:**
   - **Linux**: `~/.vscode/extensions/`
   - **macOS**: `~/.vscode/extensions/`
   - **Windows**: `%USERPROFILE%\.vscode\extensions\`

2. **Copy the extension:**
   ```bash
   cp -r vscode-witcherscript ~/.vscode/extensions/witcherscript-1.0.0
   ```

3. **Restart VS Code**

4. **Verify installation:**
   - Open a `.witcher` file
   - You should see syntax highlighting

### Option 2: Manual Installation

1. Open VS Code
2. Go to Extensions (Ctrl+Shift+X / Cmd+Shift+X)
3. Click the "..." menu and select "Install from VSIX..."
4. Navigate to the extension folder and select package.json

## Testing the Extension

### Test 1: Syntax Highlighting
1. Create a file named `test.witcher`
2. Type:
   ```witcher
   medallion("Hello, Witcher!")
   ```
3. You should see color-coded syntax

### Test 2: Snippets
1. Create a new `.witcher` file
2. Type `contract` and press Tab
3. The snippet should expand to: `contract name = value`
4. Type `igni` and press Tab
5. An if statement template should appear

### Test 3: Auto-completion
1. Type `medallion("test")`
2. The closing parenthesis should be auto-completed
3. Type `{` and `}` should appear automatically

## Troubleshooting

### Extension not loading
- Check that the file is in the correct extensions folder
- Restart VS Code completely
- Check the Extensions panel for any errors

### Syntax highlighting not working
- Verify the file has `.witcher` extension
- Restart VS Code
- Check that the grammar file exists

### Snippets not appearing
- Make sure you have a `.witcher` file open
- Press Ctrl+Space to trigger Intellisense
- Type a snippet prefix (e.g., `contract`, `igni`)

## Features Included

✅ **Syntax Highlighting**
- Keywords, operators, strings, comments

✅ **Snippets**
- 30+ ready-to-use code snippets
- For all common patterns

✅ **Code Folding**
- Collapse/expand code blocks

✅ **Auto-completion**
- Closing brackets and quotes
- Smart indentation

✅ **Language Configuration**
- Comment syntax
- Bracket matching
- Auto-closing pairs

## Available Snippets

| Snippet | Expands To |
|---------|-----------|
| `contract` | Variable declaration |
| `mutation` | Constant declaration |
| `igni` | If/else statement |
| `quen` | While loop |
| `yrden` | For loop |
| `aard` | Function definition |
| `hunt` | Return statement |
| `medallion` | Print output |
| `array` | Array literal |
| `true` | Boolean true (truth) |
| `false` | Boolean false (falsehood) |
| `input` | Read user input |
| `len` | Get array length |
| `append` | Append to array |
| And 15+ more... |

## Next Steps

1. **Write Code**: Create `.witcher` files and use the intellisense
2. **Run Programs**: Use the interpreter to execute your programs
3. **Read Docs**: Check QUICK_START.md and LANGUAGE_REFERENCE.md

## Support

For issues or questions:
1. Check the main WitcherScript documentation
2. Review the extension README.md
3. Examine the example programs

## Extension Files

```
vscode-witcherscript/
├── package.json                          # Extension manifest
├── README.md                             # This documentation
├── language-configuration.json           # Language config
├── syntaxes/
│   └── witcherscript.tmLanguage.json    # Syntax highlighting
└── snippets/
    └── witcherscript.json               # Code snippets
```

Enjoy coding with WitcherScript in VS Code! 🧙‍♂️⚔️
