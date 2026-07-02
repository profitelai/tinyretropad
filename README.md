# TinyRetroPad — Linux Edition

> A working, Notepad-style text editor in a single Python file.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20macOS-lightgrey)]()
[![Dependencies](https://img.shields.io/badge/Dependencies-zero-brightgreen)]()
[![Size](https://img.shields.io/badge/Size-22%20KB-brightgreen)]()

---

## What is this?

**TinyRetroPad** is a Linux port of [PlummersSoftwareLLC/TinyRetroPad](https://github.com/PlummersSoftwareLLC/TinyRetroPad) — a fully working Notepad clone originally written in **x86 Assembly for Windows** (~2.5 KB compressed).

This edition brings the same spirit to Linux and macOS using **Python 3 + Tkinter**.  
One file. Zero dependencies beyond the Python standard library.

---

## Features

| Category | Features |
|---|---|
| **File** | New · Open · Save · Save As |
| **Edit** | Undo · Cut · Copy · Paste · Delete · Select All · Time/Date insert |
| **Search** | Find · Find Next · Replace · Replace All · Go To Line |
| **Format** | Word Wrap · Line Numbers · Font chooser (family, size, style, live preview) |
| **View** | Status bar (Ln/Col · char count) · Dark mode |
| **UX** | Unsaved changes prompt · CLI file argument · Keyboard shortcuts |

---

## Run

```bash
python3 tinyretropad.py
```

Open a file directly:

```bash
python3 tinyretropad.py myfile.txt
```

### Requirements

- Python 3.8+
- Tkinter (usually bundled with Python)

If Tkinter is missing:

```bash
# Debian / Ubuntu
sudo apt install python3-tk

# Fedora
sudo dnf install python3-tkinter

# Arch
sudo pacman -S tk
```

---

## Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| `Ctrl+N` | New file |
| `Ctrl+O` | Open file |
| `Ctrl+S` | Save |
| `Ctrl+Shift+S` | Save As |
| `Ctrl+Z` | Undo |
| `Ctrl+X / C / V` | Cut / Copy / Paste |
| `Ctrl+A` | Select All |
| `Ctrl+F` | Find |
| `F3` | Find Next |
| `Ctrl+H` | Replace |
| `Ctrl+G` | Go To Line |
| `F5` | Insert Time/Date |

---

## Size

| | Original (Windows x86 ASM) | This port (Python + Tkinter) |
|---|---|---|
| **Size** | ~2.5 KB compressed | ~22 KB |
| **Lines** | ~650 ASM lines | 457 Python lines |
| **Dependencies** | Windows API (RICHEDIT50W) | Python stdlib only |
| **Platform** | Windows only | Linux · macOS · any Python |

---

## Project Structure

```
tinyretropad/
├── tinyretropad.py   ← the entire app (single file)
├── README.md
└── LICENSE
```

---

## Background

The original TinyRetroPad by [Dave Plummer](https://github.com/PlummersSoftwareLLC) is a tour de force in x86 Assembly — a complete Notepad clone compressed into ~2.5 KB using MASM + Crinkler. It works by routing almost every feature to a one- or two-instruction handler on top of the Windows `RICHEDIT50W` control.

This Linux port recreates the same feature set using Python's built-in `tkinter` GUI library. No frameworks, no packages, no build step — just run it.

---

## License

MIT — see [LICENSE](LICENSE)

---

## Related

- [PlummersSoftwareLLC/TinyRetroPad](https://github.com/PlummersSoftwareLLC/TinyRetroPad) — the original Windows x86 Assembly version
