# WitcherScript

A programming language inspired by The Witcher 3: Wild Hunt, featuring Witcher signs as keywords and game-themed syntax.

## Features

- **Witcher Signs as Keywords**: `igni` (if), `quen` (while), `yrden` (for), `aard` (function), `axii` (switch)
- **Game-Themed Syntax**: `contract` (variable), `medallion` (print), `hunt` (return), `grimoire` (import)
- **Full Language Support**: Variables, functions, loops, conditionals, arrays, operators
- **No Dependencies**: Requires only Python 3.6+

## Quick Start

```bash
# Interactive mode
python3 witcher_interpreter.py

# Run a file
python3 witcher_interpreter.py example_programs/01_hello_world.witcher

# Or install via pip
pip install witcherscript
```

## Examples

### Hello World
```witcher
medallion("Hail, fellow Witcher!")
```

### Variables & Functions
```witcher
contract gold = 100
contract reward = 50
medallion(gold + reward)  # Output: 150

aard cast_igni(intensity) {
    contract damage = 50 * intensity
    hunt damage
}
```

### Control Flow
```witcher
# If statement
igni level >= 50 {
    medallion("You are a master!")
} elixir {
    medallion("Train more.")
}

# While loop
contract count = 1
quen count <= 5 {
    medallion(count)
    count = count + 1
}

# For loop
contract monsters = ["Griffin", "Basilisk", "Drowner"]
yrden monster -> monsters {
    medallion(monster)
}
```

## Keywords

| Keyword | Purpose | Example |
|---------|---------|---------|
| `contract` | Variable | `contract x = 10` |
| `mutation` | Constant | `mutation MAX = 99` |
| `medallion` | Print | `medallion("text")` |
| `igni` | If | `igni x > 0 { ... }` |
| `quen` | While | `quen x < 10 { ... }` |
| `yrden` | For | `yrden item -> items { ... }` |
| `aard` | Function | `aard func(x) { ... }` |
| `hunt` | Return | `hunt result` |
| `elixir` | Else | `igni ... { } elixir { }` |
| `grimoire` | Import | `grimoire "lib/module"` |

## Built-in Functions

- `medallion(value)` - Print output
- `sigh(prompt)` - Read input
- `witcher_speed(text, times)` - Repeat string
- `monster_count(array)` - Array length
- `add_to_bestiary(array, value)` - Append to array
- `hunter_instinct(value)` - Get type info
- `potion_effect(a, b)` - Combine values

## Data Types

- **Numbers**: `42`, `3.14`
- **Text**: `"Geralt of Rivia"`
- **Truth/Falsehood**: `truth`, `falsehood`
- **Bestiary**: `["item1", "item2"]`

## Operators

- **Arithmetic**: `+`, `-`, `*`, `/`, `%`
- **Comparison**: `==`, `!=`, `<`, `>`, `<=`, `>=`
- **Logical**: `and`, `or`, `not`

## Project Structure

```
WitcherScript/
├── witcher_interpreter.py          # Main interpreter
├── example_programs/               # Sample programs
│   ├── 01_hello_world.witcher
│   ├── 02_monster_hunt.witcher
│   ├── 03_casting_signs.witcher
│   ├── 04_bestiary.witcher
│   ├── 05_alchemy.witcher
│   ├── 06_quest_system.witcher
│   ├── 07_combat.witcher
│   ├── 08_fibonacci.witcher
│   ├── 09_bubble_sort.witcher
│   ├── 10_grimoire_import.witcher
│   └── 11_multiple_grimoires.witcher
├── lib/                             # Library modules
│   ├── monster_helpers.witcher
│   ├── math_utils.witcher
│   └── quicksort.witcher
└── vscode-witcherscript/           # VS Code extension
    ├── syntaxes/                    # Syntax highlighting
    ├── snippets/                    # Code snippets
    └── package.json
```

## Try It

```bash
python3 witcher_interpreter.py example_programs/02_monster_hunt.witcher
python3 witcher_interpreter.py example_programs/08_fibonacci.witcher
python3 witcher_interpreter.py example_programs/09_bubble_sort.witcher
```

## VS Code Extension

Install the WitcherScript extension for syntax highlighting and snippets:

```bash
cd vscode-witcherscript
npm install
vsce package
```

Then install the `.vsix` file in VS Code.

## License

MIT License - See [LICENSE](LICENSE)

## Inspired By

The Witcher 3: Wild Hunt - CD Projekt Red

---

**Start your witcher journey!** 🧙‍♂️

```witcher
medallion("May your blade be sharp and your wits sharper!")
```
