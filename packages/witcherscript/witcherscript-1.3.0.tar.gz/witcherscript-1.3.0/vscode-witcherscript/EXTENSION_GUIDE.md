# 🧙‍♂️ WitcherScript VS Code Extension

Complete intellisense support for WitcherScript in Visual Studio Code!

## ✨ What's Included

### 1. **Syntax Highlighting** 🎨
Full syntax highlighting with proper color coding:
- Keywords (igni, quen, yrden, aard, axii, elixir, hunt, etc.)
- Built-in functions (medallion, sigh, witcher_speed, etc.)
- Strings, numbers, comments
- Operators and punctuation

### 2. **Code Snippets** 📝
30+ ready-to-use snippets for rapid development:

**Control Flow:**
- `igni` → If statement
- `quen` → While loop
- `yrden` → For loop
- `elixir` → Else clause

**Functions:**
- `aard` → Function definition
- `hunt` → Return statement
- `call` → Function call

**Variables:**
- `contract` → Variable declaration
- `mutation` → Constant declaration

**I/O & Arrays:**
- `medallion` → Print output
- `input` → Read input
- `array` → Array literal
- `len` → Array length
- `append` → Add to array

**And many more!**

### 3. **Auto-completion** ⚡
Intelligent code completion:
- Auto-closing brackets and quotes
- Smart indentation
- Code folding (collapse/expand blocks)
- Bracket matching

### 4. **Language Support** 🔧
- File association (.witcher files)
- Comment syntax highlighting
- Proper brace matching
- Code folding regions

## 🚀 Installation

### Quick Install (Recommended)

1. Copy the `vscode-witcherscript` folder to your VS Code extensions:

   **Linux/Mac:**
   ```bash
   cp -r vscode-witcherscript ~/.vscode/extensions/witcherscript-1.0.0
   ```

   **Windows (PowerShell):**
   ```powershell
   Copy-Item -Recurse vscode-witcherscript $env:USERPROFILE\.vscode\extensions\witcherscript-1.0.0
   ```

2. Restart VS Code

3. Open any `.witcher` file - syntax highlighting should be active!

### Manual Installation

1. Open VS Code and go to Extensions (Ctrl+Shift+X)
2. Look for the three dots (⋯) menu
3. Select "Install from VSIX"
4. Navigate to `vscode-witcherscript` folder
5. Select `package.json`

## 💡 Usage Tips

### Using Snippets

1. **Type the prefix** - e.g., `contract`, `igni`, `aard`
2. **Press Tab** - The snippet expands
3. **Fill in the blanks** - Use Tab to jump between placeholders
4. **Press Enter** - Confirm and continue

**Example:**
```
Type: contract
Press: Tab
Jump to: name (highlighted)
Type: my_var
Press: Tab
Jump to: value (highlighted)
Type: 42
Press: Enter
```

Result:
```witcher
contract my_var = 42
```

### Keyboard Shortcuts

- **Ctrl+Space** - Trigger Intellisense/Snippets
- **Ctrl+/** - Comment/uncomment line
- **Ctrl+Shift+/** - Block comment
- **Tab** - Expand snippet or indent
- **Shift+Tab** - Unindent
- **Ctrl+Shift+[** - Fold code block
- **Ctrl+Shift+]** - Unfold code block

### Smart Indentation

The extension automatically maintains proper indentation:
```witcher
aard my_function(x) {           # Auto-indents inside braces
    contract result = x * 2      # Indented
    hunt result                  # Indented
}                                # Back to original level
```

## 📚 Example Session

Create a file `test.witcher`:

```witcher
# Start typing 'contract' and press Tab
contract gold = 100

# Type 'igni' and press Tab
igni gold > 50 {
    # Type 'medallion' and press Tab
    medallion("You are wealthy!")
} elixir {
    medallion("You need more gold.")
}

# Type 'aard' and press Tab
aard calculate(a, b) {
    contract sum = a + b
    hunt sum
}
```

The extension handles:
- ✅ Color coding for all keywords
- ✅ Auto-closing braces and quotes
- ✅ Smart indentation
- ✅ Snippet expansion
- ✅ Comment highlighting
- ✅ Function detection

## 🎨 Color Scheme

Colors automatically adapt to your VS Code theme:
- **Blue/Purple** - Keywords and signs (igni, quen, aard, etc.)
- **Yellow/Cyan** - Built-in functions (medallion, sigh, etc.)
- **Green/Teal** - Constants (truth, falsehood)
- **Red/Orange** - Strings
- **Green** - Numbers
- **Gray** - Comments

## 🔧 Configuration

Optional: Add to your VS Code `settings.json` for custom colors:

```json
"[witcherscript]": {
  "editor.tabSize": 4,
  "editor.insertSpaces": true,
  "editor.autoIndent": "full",
  "editor.formatOnPaste": true
}
```

## 📋 Snippet Reference

### Variables
```
contract         → Variable declaration
mutation         → Constant declaration
```

### Control Flow
```
igni             → If/else statement
igni-only        → If without else
quen             → While loop
yrden            → For loop
```

### Functions
```
aard             → Function definition
call             → Function call
hunt             → Return statement
```

### I/O & Data
```
medallion        → Print output
input            → Read input
array            → Array literal
true             → Boolean true (truth)
false            → Boolean false (falsehood)
```

### Built-in Functions
```
len              → Get array length (monster_count)
append           → Add to array (add_to_bestiary)
typeof           → Get type info (hunter_instinct)
repeat           → Repeat string (witcher_speed)
```

### Operators
```
+                → Addition/concatenation
-                → Subtraction
*                → Multiplication
/                → Division
%                → Modulo
==               → Equal comparison
!=               → Not equal comparison
>                → Greater than
<                → Less than
```

## 🐛 Troubleshooting

**Q: Extension not loading**
- A: Verify file is in correct extensions folder, restart VS Code

**Q: Syntax highlighting not working**
- A: Check file has `.witcher` extension, restart VS Code

**Q: Snippets not appearing**
- A: Make sure `.witcher` file is open, press Ctrl+Space

**Q: Auto-complete not working**
- A: Press Ctrl+Space to manually trigger Intellisense

**Q: Colors look wrong**
- A: Switch to a different VS Code theme or customize in settings.json

## 📦 Extension Contents

```
vscode-witcherscript/
├── package.json                      # Extension manifest
├── language-configuration.json       # Language settings
├── README.md                        # Features overview
├── INSTALLATION.md                  # Installation guide
├── EXTENSION_GUIDE.md              # This file
├── .vscode-settings.json           # Recommended settings
├── syntaxes/
│   └── witcherscript.tmLanguage.json  # Syntax highlighting
└── snippets/
    └── witcherscript.json          # 30+ code snippets
```

## 🎓 Learning Resources

Inside the extension:
- Check snippets for common patterns
- Use Intellisense (Ctrl+Space) to explore

Outside the extension:
- [QUICK_START.md](../QUICK_START.md) - Get started fast
- [CHEAT_SHEET.md](../CHEAT_SHEET.md) - Quick reference
- [LANGUAGE_REFERENCE.md](../LANGUAGE_REFERENCE.md) - Complete docs

## 🎉 Features Summary

✅ Syntax highlighting for all WitcherScript keywords
✅ 30+ code snippets for rapid development
✅ Auto-completion and bracket matching
✅ Code folding support
✅ Smart indentation
✅ File type association (.witcher)
✅ Comment support
✅ Operator highlighting
✅ Built-in function detection
✅ Theme-aware color scheme

## 🚀 Next Steps

1. **Install the extension** - Copy to .vscode/extensions
2. **Create a .witcher file** - Start typing!
3. **Use snippets** - Press Tab to expand
4. **Run your code** - Use the WitcherScript interpreter
5. **Explore more** - Check the language documentation

---

**Enjoy intellisense-powered WitcherScript development!** 🧙‍♂️⚔️

For issues or suggestions, refer to the main WitcherScript documentation.
