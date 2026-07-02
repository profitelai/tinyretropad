# TinyRetroPad — Linux Edition

A lightweight Notepad-style text editor for Linux, built with Python 3 + Tkinter.  
Zero external dependencies. Single file. Runs anywhere Python is installed.

Inspired by [PlummersSoftwareLLC/TinyRetroPad](https://github.com/PlummersSoftwareLLC/TinyRetroPad) — the original Windows x86 Assembly Notepad clone (~2.5 KB).  
This port brings the same spirit to Linux (and macOS) with a full GUI.

---

## Features

- File: New · Open · Save · Save As
- Edit: Undo · Cut · Copy · Paste · Delete · Select All · Time/Date insert
- Find · Find Next · Replace · Replace All · Go To Line
- Format: Word Wrap · Line Numbers · Font chooser (family, size, style + live preview)
- View: Status bar (Ln/Col, char count) · Dark mode
- Unsaved changes prompt on close / new / open
- Open file via command line argument: `python3 tinyretropad.py file.txt`

---

## Run

```bash
python3 tinyretropad.py
```

Requires Python 3.8+ with Tkinter. On most Linux distros Tkinter ships with Python.  
If missing: `sudo apt install python3-tk` (Debian/Ubuntu) or `sudo dnf install python3-tkinter` (Fedora).

---

## Size

**~22 KB · 457 lines** — single file, no dependencies beyond the Python standard library.

---

## License

MIT — see [LICENSE](LICENSE)
