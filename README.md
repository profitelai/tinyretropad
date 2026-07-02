```
  _____      _             _____          _   _     _
 |  __ \    | |           |  __ \        | | | |   (_)
 | |__) |___| |_ _ __ ___ | |__) |_ _  __| | | |    _ _ __  _   ___  __
 |  _  // _ \ __| '__/ _ \|  ___/ _` |/ _` | | |   | | '_ \| | | \ \/ /
 | | \ \  __/ |_| | | (_) | |  | (_| | (_| | | |___| | | | | |_| |>  <
 |_|  \_\___|\__|_|  \___/|_|   \__,_|\__,_| |_____|_|_| |_|\__,_/_/\_\

  T I N Y   L I N U X   T E X T   E D I T O R  ·  P Y T H O N   E D I T I O N
```

# TinyRetroPad — Linux Edition

A working, Notepad-style Linux text editor. Two versions — GUI and terminal. Single Python file each. Zero dependencies.

A Linux port of [PlummersSoftwareLLC/TinyRetroPad](https://github.com/PlummersSoftwareLLC/TinyRetroPad) — the legendary Notepad clone written in **x86 Assembly for Windows** (~2.5 KB compressed). This edition brings the same minimalist, feature-complete spirit to Linux and macOS using **Python 3 + stdlib only**.

---

## Two Editors

### `tinyretropad.py` — Desktop GUI

Full graphical Notepad clone using Python's built-in `tkinter`. Requires a desktop (X11, Wayland, or macOS).

```bash
python3 tinyretropad.py
python3 tinyretropad.py myfile.txt
```

| Menu | Features |
|------|----------|
| **File** | New · Open · Save · Save As |
| **Edit** | Undo · Cut · Copy · Paste · Delete · Select All · Time/Date |
| **Find** | Find · Find Next · Regex mode · Whole Word · Wrap-around · Find All |
| **Replace** | Replace · Replace All · Capture groups (`\1`, `\2`) |
| **Format** | Word Wrap · Line Numbers · Font chooser (family · size · style · live preview) |
| **View** | Status bar (Ln/Col · char count) · Dark mode |

---

### `tinypad_terminal.py` — Terminal Editor (nano replacement)

Full terminal UI editor using Python's built-in `curses`. No desktop needed. Works over SSH. Drop-in replacement for `nano`.

```bash
python3 tinypad_terminal.py
python3 tinypad_terminal.py myfile.py
```

**Replace nano system-wide** — add to `~/.bashrc` or `~/.zshrc`:
```bash
alias nano='python3 /path/to/tinypad_terminal.py'
```

| Feature | Details |
|---------|---------|
| **Syntax highlighting** | Python · JS/TS · PHP · HTML · CSS · JSON · Shell · Go · Rust · Ruby · Lua · SQL · YAML · C/C++ |
| **Mouse selection** | Click and drag — auto-copies to system clipboard on release |
| **System clipboard** | `Ctrl+C` copy · `Ctrl+V` paste — works with your OS clipboard |
| **Auto-indent** | Smart indent after `:` `{` `[` in Python, JS, C, PHP, Go, Rust |
| **Undo / Redo** | Full undo stack (300 levels) |
| **UI** | Cyan header bar · line numbers · status bar · two-row shortcut bar |

#### Terminal Editor Shortcuts

| Key | Action | Key | Action |
|-----|--------|-----|--------|
| `Ctrl+O` | Save | `Ctrl+X` | Exit / Cut selection |
| `Ctrl+C` | Copy → clipboard | `Ctrl+V` | Paste from clipboard |
| `Ctrl+Z` | Undo | `Ctrl+R` | Redo |
| `Ctrl+W` | Find | `Ctrl+N` | Find next |
| `Ctrl+K` | Cut line | `Ctrl+U` | Paste cut buffer |
| `Ctrl+D` | Duplicate line | `Ctrl+A` | Select all |
| `Ctrl+G` | Help | `Ctrl+/` | Go to line |

---

## Install & Run

**Requirements:** Python 3.8+ — no external packages.

```bash
# ── macOS ────────────────────────────────────────────────────────────────────
# Check your Python version first:
python3 --version   # e.g. Python 3.14.x

# Install tkinter to match (Homebrew Python):
brew install python-tk@3.14   # Python 3.14
brew install python-tk@3.13   # Python 3.13
brew install python-tk@3.12   # Python 3.12

# Clipboard: pbcopy/pbpaste are built in — nothing to install.

# ── Linux ────────────────────────────────────────────────────────────────────
# GUI — install tkinter if missing:
sudo apt install python3-tk        # Debian / Ubuntu
sudo dnf install python3-tkinter   # Fedora
sudo pacman -S tk                  # Arch

# Terminal — install clipboard tool:
sudo apt install xclip             # Linux X11
sudo apt install wl-clipboard      # Linux Wayland
```

---

## Contents

| File | Description |
|------|-------------|
| `tinyretropad.py` | Desktop GUI editor (Tkinter) |
| `tinypad_terminal.py` | Terminal TUI editor (curses) — nano replacement |
| `LICENSE` | MIT License |

---

## Size Comparison

| | Original (Windows x86 ASM) | GUI (`tinyretropad.py`) | Terminal (`tinypad_terminal.py`) |
|---|---|---|---|
| **Compressed size** | ~2.5 KB | — | — |
| **Source size** | ~650 ASM lines | ~460 lines / 22 KB | ~740 lines / 30 KB |
| **Dependencies** | Windows API (RICHEDIT50W) | Python stdlib only | Python stdlib only |
| **Platform** | Windows x86 only | Linux · macOS | Linux · macOS · SSH |

---

## How it works

The original TinyRetroPad routes almost every Notepad feature to a **one- or two-instruction handler** on top of the Windows `RICHEDIT50W` control — the WinAPI does the heavy lifting, keeping the assembly tiny.

This Linux edition follows the same philosophy: let the toolkit do the work.

- **GUI version** — every menu command is a single call into `tkinter`'s `Text` widget or a stdlib dialog. Font, Find, Replace, word wrap — all delegated.
- **Terminal version** — `curses` handles screen drawing; every edit operation is a direct mutation of a `list[str]` document model. Syntax highlighting is a per-line regex pass over 15 language definitions.

No frameworks. No packages. No build step. Just run it.

---

## Credits

- **TinyRetroPad (original)** — [PlummersSoftwareLLC/TinyRetroPad](https://github.com/PlummersSoftwareLLC/TinyRetroPad) — Dave Plummer. x86 Assembly, Windows, ~2.5 KB.
- **Dave's Tiny Editor (DTE)** — Matt Power — the sub-1KB RICHEDIT editor the original forks from.
- **TinyRetroPad Linux Edition** — [profitelai/tinyretropad](https://github.com/profitelai/tinyretropad) — Python 3 port for Linux and macOS.

---

## License

MIT — see [LICENSE](LICENSE)
