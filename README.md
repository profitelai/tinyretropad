# Linote — Linux Edition

> A working, Notepad-style text editor in a single Python file. Two versions — pick your style.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20macOS-lightgrey)]()
[![Dependencies](https://img.shields.io/badge/Dependencies-zero-brightgreen)]()

Inspired by [PlummersSoftwareLLC/TinyRetroPad](https://github.com/PlummersSoftwareLLC/TinyRetroPad) — a full Notepad clone originally written in **x86 Assembly for Windows** (~2.5 KB). This project ports the same spirit to Linux and macOS using Python 3, zero external dependencies.

---

## Two Versions

### Version 1 — Desktop GUI (`linote.py`)

A full graphical editor using Python's built-in `tkinter`. Requires a desktop environment (X11, Wayland, or macOS).

```bash
python3 linote.py
python3 linote.py myfile.txt
```

![GUI Editor](https://img.shields.io/badge/UI-Tkinter%20GUI-blue)

| Feature | Details |
|---|---|
| File | New · Open · Save · Save As |
| Edit | Undo · Cut · Copy · Paste · Delete · Select All · Time/Date |
| Find | Find · Find Next · **Regex** · Whole Word · Wrap-around · Find All |
| Replace | Replace · Replace All · **Capture group support** (`\1`, `\2`) |
| Format | Word Wrap · Line Numbers · Font chooser with live preview |
| View | Status bar (Ln/Col · char count) · **Dark mode** |
| UX | Unsaved changes prompt · CLI file argument · Keyboard shortcuts |

---

### Version 2 — Terminal / Linux Editor (`linote_terminal.py`)

A full terminal UI editor built with Python's built-in `curses`. Runs anywhere — no desktop needed. Works over SSH. **Replaces `nano`.**

```bash
python3 linote_terminal.py
python3 linote_terminal.py myfile.py
```

**To replace `nano` system-wide** — add to your `~/.bashrc` or `~/.zshrc`:

```bash
alias nano='python3 /path/to/linote_terminal.py'
```

![Terminal Editor](https://img.shields.io/badge/UI-Terminal%20TUI-green)

| Feature | Details |
|---|---|
| **Syntax highlighting** | Python · JS/TS · PHP · HTML · CSS · JSON · Shell · Go · Rust · Ruby · Lua · SQL · YAML · C/C++ |
| **Mouse selection** | Click and drag to select — auto-copies to system clipboard on release |
| **System clipboard** | `Ctrl+C` copy · `Ctrl+V` paste — works with your OS clipboard |
| File | `Ctrl+O` save · `Ctrl+X` exit |
| Edit | Undo · Redo · Cut line · Paste · Duplicate line |
| Search | `Ctrl+W` find · `Ctrl+N` next · `Ctrl+P` previous · `Ctrl+/` go to line |
| Navigation | Arrow keys · Word jump · Page up/down · Home/End · Mouse click |
| Auto-indent | Smart indent after `:` `{` `[` in Python, JS, C, PHP, Go, Rust |
| UI | Header bar · Line numbers · Status bar · Two-row shortcut bar |

#### Keyboard Shortcuts (Terminal Editor)

| Shortcut | Action |
|---|---|
| `Ctrl+O` | Save |
| `Ctrl+X` | Exit (or cut selection) |
| `Ctrl+C` | Copy selection → system clipboard |
| `Ctrl+V` | Paste from system clipboard |
| `Ctrl+Z` | Undo |
| `Ctrl+R` | Redo |
| `Ctrl+W` | Find |
| `Ctrl+N` | Find next |
| `Ctrl+P` | Find previous |
| `Ctrl+K` | Cut current line |
| `Ctrl+U` | Paste cut buffer |
| `Ctrl+D` | Duplicate line |
| `Ctrl+A` | Select all |
| `Ctrl+G` | Help |
| `Ctrl+/` | Go to line |

---

## Requirements

Python 3.8+ with no external packages.

- **GUI version**: Tkinter (usually bundled with Python)
- **Terminal version**: curses (bundled with Python on Linux/macOS)

If Tkinter is missing on Linux:

```bash
sudo apt install python3-tk        # Debian / Ubuntu
sudo dnf install python3-tkinter   # Fedora
sudo pacman -S tk                  # Arch
```

For system clipboard in the terminal version on Linux:

```bash
sudo apt install xclip    # X11
sudo apt install wl-clipboard  # Wayland
```

On macOS, `pbcopy`/`pbpaste` are built in — no install needed.

---

## Size

| | Original (Windows x86 ASM) | GUI version | Terminal version |
|---|---|---|---|
| **File** | `TinyRetroPad.asm` | `linote.py` | `linote_terminal.py` |
| **Size** | ~2.5 KB compressed | ~22 KB | ~30 KB |
| **Lines** | ~650 ASM lines | 457 Python lines | 700+ Python lines |
| **Dependencies** | Windows API | Python stdlib | Python stdlib |
| **Platform** | Windows only | Linux · macOS | Linux · macOS · SSH |

---

## License

MIT — see [LICENSE](LICENSE)

---

## Related

- [PlummersSoftwareLLC/TinyRetroPad](https://github.com/PlummersSoftwareLLC/TinyRetroPad) — the original Windows x86 Assembly version (~2.5 KB)
