# WitcherScript VS Code Extension

This extension adds full language support for WitcherScript to Visual Studio Code.

## Features

### 🎨 Syntax Highlighting
- Proper color coding for all WitcherScript keywords
- Syntax highlighting for signs (igni, quen, yrden, aard, axii)
- String, number, and comment highlighting

### 📝 Snippets & Autocomplete
Quick snippets for common patterns:
- `contract` - Variable declaration
- `mutation` - Constant declaration
- `grimoire` - Import another .witcher file ⭐
- `igni` - If statement
- `quen` - While loop
- `yrden` - For loop
- `aard` - Function definition
- `hunt` - Return statement
- `medallion` - Print output
- And many more!

### 🧩 Code Folding
Automatic code folding support for braces

### ⚙️ Auto-completion
- Closing braces and quotes
- Smart indentation
- Bracket matching

## Installation

### From VS Code Extension Marketplace (if published)
1. Open Extensions in VS Code (Ctrl+Shift+X / Cmd+Shift+X)
2. Search for "WitcherScript"
3. Click Install

### Manual Installation
1. Copy this folder to `~/.vscode/extensions/witcherscript-1.0.0`
2. Restart VS Code

## Usage

1. Create a new file with `.witcher` extension
2. Start typing WitcherScript code
3. Use Intellisense (Ctrl+Space) for autocomplete
4. Type snippet prefix and press Tab to expand

## Example Snippets

### Create a variable
```
Type: contract
Press: Tab
Result: contract name = value
```

### Create a function
```
Type: aard
Press: Tab
Result: aard function_name(params) {
          // code
          hunt result
        }
```

### Create a loop
```
Type: quen
Press: Tab
Result: quen condition {
          // code
        }
```

## Supported Syntax

### Keywords
- **Signs**: igni, quen, yrden, aard, axii
- **Variables**: contract, mutation
- **Control**: elixir, hunt
- **I/O**: medallion
- **Modules**: grimoire ⭐
- **Logic**: and, or, not
- **Values**: truth, falsehood

### Built-in Functions
- medallion() - Print
- sigh() - Input
- witcher_speed() - String repeat
- monster_count() - Array length
- add_to_bestiary() - Array append
- hunter_instinct() - Type info
- potion_effect() - Combine values

## Theme Colors

The extension uses VS Code's standard theme colors:
- Keywords: Blue/Purple
- Strings: Red/Orange
- Numbers: Green
- Comments: Gray
- Functions: Yellow/Cyan

## Tips

1. **Use Snippets**: Start typing a keyword and press Ctrl+Space to see suggestions
2. **Code Folding**: Click the fold arrow next to braces to collapse code blocks
3. **Auto-format**: Use Tab for indentation (automatically configured)
4. **Comment**: Use # for single-line comments

## Extension Version

- **Version**: 1.0.0
- **Scope**: WitcherScript (.witcher files)
- **Dependencies**: None
- **License**: MIT

## For More Information

See the main WitcherScript documentation:
- README.md - Main guide
- QUICK_START.md - Getting started
- LANGUAGE_REFERENCE.md - Complete specification
