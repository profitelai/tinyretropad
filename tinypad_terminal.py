#!/usr/bin/env python3
"""
TinyRetroPad Terminal — nano replacement
Python 3 + curses · zero dependencies · Linux / macOS / SSH

Usage:
    python3 tinypad_terminal.py [file]
    alias nano='python3 /path/to/tinypad_terminal.py'
"""

import curses, os, sys, re, subprocess
from datetime import datetime

# ── System clipboard ─────────────────────────────────────────────────────────

def _sys_copy(text):
    """Write text to the OS clipboard (macOS + Linux X11/Wayland)."""
    try:
        if sys.platform == 'darwin':
            subprocess.run(['pbcopy'], input=text.encode(), timeout=2)
            return
        for cmd in (['xclip', '-selection', 'clipboard'],
                    ['xsel', '--clipboard', '--input'],
                    ['wl-copy']):
            try:
                subprocess.run(cmd, input=text.encode(), timeout=2, check=True)
                return
            except (FileNotFoundError, subprocess.CalledProcessError,
                    subprocess.TimeoutExpired):
                pass
    except Exception:
        pass

def _sys_paste():
    """Read text from the OS clipboard. Returns '' on failure."""
    try:
        if sys.platform == 'darwin':
            r = subprocess.run(['pbpaste'], capture_output=True, timeout=2)
            return r.stdout.decode('utf-8', errors='replace')
        for cmd in (['xclip', '-selection', 'clipboard', '-o'],
                    ['xsel', '--clipboard', '--output'],
                    ['wl-paste', '--no-newline']):
            try:
                r = subprocess.run(cmd, capture_output=True, timeout=2, check=True)
                return r.stdout.decode('utf-8', errors='replace')
            except (FileNotFoundError, subprocess.CalledProcessError,
                    subprocess.TimeoutExpired):
                pass
    except Exception:
        pass
    return ''

# ── Syntax definitions ───────────────────────────────────────────────────────

LANG_MAP = {
    '.py':'python', '.pyw':'python',
    '.js':'js', '.jsx':'js', '.ts':'js', '.tsx':'js', '.mjs':'js',
    '.php':'php', '.sh':'shell', '.bash':'shell', '.zsh':'shell',
    '.html':'html', '.htm':'html', '.css':'css', '.json':'json',
    '.c':'c', '.h':'c', '.cpp':'c', '.cc':'c', '.cs':'c',
    '.rb':'ruby', '.go':'go', '.rs':'rust', '.lua':'lua',
    '.sql':'sql', '.md':'markdown', '.yml':'yaml', '.yaml':'yaml',
}

_KW = {
    'python': r'\b(def|class|import|from|return|if|elif|else|for|while|try|except|finally|with|as|pass|break|continue|yield|lambda|in|not|and|or|is|None|True|False|raise|del|global|nonlocal|assert|async|await)\b',
    'js':     r'\b(function|var|let|const|return|if|else|for|while|class|import|export|from|async|await|new|this|true|false|null|undefined|try|catch|finally|throw|typeof|instanceof|switch|case|break|continue|default|delete|do|of|void|yield)\b',
    'php':    r'\b(function|class|if|else|elseif|for|foreach|while|return|echo|print|new|try|catch|finally|throw|public|private|protected|static|abstract|interface|extends|implements|namespace|use|true|false|null)\b',
    'shell':  r'\b(if|then|else|elif|fi|for|while|do|done|case|esac|function|return|exit|export|local|echo|printf|source|alias|unset|true|false)\b',
    'c':      r'\b(int|char|float|double|void|if|else|for|while|do|return|break|continue|struct|union|enum|typedef|static|const|extern|sizeof|switch|case|default|nullptr|true|false|auto|class|public|private|protected|virtual|new|delete|template|namespace|using|include|define|ifdef|endif)\b',
    'ruby':   r'\b(def|class|module|if|elsif|else|unless|while|until|for|do|end|return|yield|begin|rescue|ensure|raise|true|false|nil|self|super|require|include|attr_accessor|attr_reader)\b',
    'go':     r'\b(func|var|const|type|import|package|return|if|else|for|range|switch|case|break|continue|defer|go|select|chan|map|struct|interface|make|new|true|false|nil|int|string|bool|error|byte|rune)\b',
    'rust':   r'\b(fn|let|mut|const|static|if|else|for|while|loop|match|return|struct|enum|impl|trait|use|mod|pub|super|self|true|false|None|Some|Ok|Err|async|await|move|where|type|as|in|ref)\b',
    'lua':    r'\b(and|break|do|else|elseif|end|false|for|function|if|in|local|nil|not|or|repeat|return|then|true|until|while)\b',
    'sql':    r'\b(SELECT|FROM|WHERE|INSERT|UPDATE|DELETE|CREATE|DROP|ALTER|TABLE|INDEX|VIEW|JOIN|LEFT|RIGHT|INNER|OUTER|ON|AND|OR|NOT|IN|IS|NULL|AS|ORDER|BY|GROUP|HAVING|LIMIT|OFFSET|DISTINCT|UNION|ALL|INTO|VALUES|SET|PRIMARY|KEY|FOREIGN|REFERENCES|CASCADE|DEFAULT|AUTO_INCREMENT|SERIAL|CONSTRAINT)\b',
    'yaml':   r'^(\s*[\w-]+)\s*:',
}

_STR  = re.compile(r'("""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\'|"(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\'|`(?:[^`\\]|\\.)*`)')
_NUM  = re.compile(r'\b(0x[0-9a-fA-F]+|0b[01]+|\d+\.?\d*(?:[eE][+-]?\d+)?)\b')
_CMT  = {
    'python':'#', 'shell':'#', 'ruby':'#', 'yaml':'#', 'lua':'--',
    'js':'//', 'php':'//', 'c':'//', 'go':'//', 'rust':'//',
    'html':'<!--', 'css':'/*', 'sql':'--',
}
_MULTI_CMT = { 'js':('/*','*/'), 'php':('/*','*/'), 'c':('/*','*/'),
               'go':('/*','*/'), 'rust':('/*','*/'), 'css':('/*','*/'),
               'html':('<!--','-->') }

# Color pair IDs
_NORMAL=1; _KEYWORD=2; _STRING=3; _COMMENT=4; _NUMBER=5
_LINENUM=6; _HEADER=7; _STATUS=8; _HILIGHT=9; _SPECIAL=10; _DIM=11

_SCROLL_UP   = getattr(curses, 'BUTTON4_PRESSED', 0)
_SCROLL_DOWN = getattr(curses, 'BUTTON5_PRESSED', 2097152)

SHORTCUTS = [
    ('^X','Exit'), ('^O','Save'), ('^W','Find'), ('^N','Next'),
    ('^K','Cut Ln'), ('^U','Paste'), ('^Z','Undo'), ('^R','Redo'),
    ('^/','Go To'), ('^G','Help'), ('^C','Position'), ('^T','File End'),
]


def _colormap(line, lang):
    """Build per-character (pair, bold) color array for a line."""
    n = len(line)
    if n == 0 or not lang or lang == 'markdown':
        return [(_NORMAL, 0)] * n

    colors = [(_NORMAL, 0)] * n

    def fill(start, end, pair, bold=0):
        for i in range(max(0,start), min(n,end)):
            colors[i] = (pair, bold)

    # Keywords
    kpat = _KW.get(lang)
    if kpat:
        flags = re.IGNORECASE if lang == 'sql' else 0
        for m in re.finditer(kpat, line, flags):
            fill(m.start(), m.end(), _KEYWORD, curses.A_BOLD)

    # Numbers
    for m in _NUM.finditer(line):
        fill(m.start(), m.end(), _NUMBER)

    # Strings (override keywords/numbers)
    for m in _STR.finditer(line):
        fill(m.start(), m.end(), _STRING)

    # Single-line comment (highest priority — overrides everything)
    pfx = _CMT.get(lang)
    if pfx:
        idx = line.find(pfx)
        if idx >= 0:
            # Don't treat // inside a string as a comment
            in_str = any(m.start() <= idx < m.end() for m in _STR.finditer(line))
            if not in_str:
                fill(idx, n, _COMMENT, curses.A_DIM)

    # Multi-line comment openers on this line
    ml = _MULTI_CMT.get(lang)
    if ml:
        op, cl = ml
        idx = line.find(op)
        if idx >= 0:
            end_idx = line.find(cl, idx + len(op))
            fill(idx, end_idx + len(cl) if end_idx >= 0 else n, _COMMENT, curses.A_DIM)

    # HTML tags
    if lang == 'html':
        for m in re.finditer(r'<[^>]*>', line):
            fill(m.start(), m.end(), _SPECIAL)
    # JSON keys
    elif lang == 'json':
        for m in re.finditer(r'"([^"]+)"\s*:', line):
            fill(m.start(), m.end()-1, _SPECIAL, curses.A_BOLD)
    # YAML keys
    elif lang == 'yaml':
        m = re.match(r'^(\s*)([\w-]+)\s*:', line)
        if m:
            fill(m.start(2), m.end(2), _SPECIAL, curses.A_BOLD)
    # CSS properties
    elif lang == 'css':
        for m in re.finditer(r'([\w-]+)\s*:', line):
            fill(m.start(), m.end()-1, _KEYWORD, curses.A_BOLD)

    return colors


# ── Editor ───────────────────────────────────────────────────────────────────

class Editor:
    def __init__(self, stdscr, filename=None):
        self.scr      = stdscr
        self.filename = filename
        self.lines    = ['']
        self.cx = self.cy = 0
        self.top = self.left = 0
        self.modified  = False
        self.message   = ''
        self.clipboard : list[str] = []
        self.undo_stack: list = []
        self.redo_stack: list = []
        self.search    = ''
        self.lang      = ''
        self.sel_anchor: tuple | None = None  # (cy, cx) where drag started
        self._mouse_down = False
        self._in_multi_comment = False
        self._init_colors()
        if filename:
            if os.path.isfile(filename):
                self._load(filename)
            else:
                self.message = f'New file: {filename}'
                self.lang = self._detect_lang()

    def _init_colors(self):
        curses.start_color()
        curses.use_default_colors()
        bg = -1
        curses.init_pair(_NORMAL,  -1,                   bg)
        curses.init_pair(_KEYWORD, curses.COLOR_CYAN,    bg)
        curses.init_pair(_STRING,  curses.COLOR_YELLOW,  bg)
        curses.init_pair(_COMMENT, curses.COLOR_GREEN,   bg)
        curses.init_pair(_NUMBER,  curses.COLOR_MAGENTA, bg)
        curses.init_pair(_LINENUM, curses.COLOR_WHITE,   bg)
        curses.init_pair(_HEADER,  curses.COLOR_BLACK,   curses.COLOR_CYAN)
        curses.init_pair(_STATUS,  curses.COLOR_BLACK,   curses.COLOR_WHITE)
        curses.init_pair(_HILIGHT, curses.COLOR_BLACK,   curses.COLOR_YELLOW)
        curses.init_pair(_SPECIAL, curses.COLOR_BLUE,    bg)
        curses.init_pair(_DIM,     curses.COLOR_WHITE,   bg)

    def _detect_lang(self):
        if not self.filename: return ''
        return LANG_MAP.get(os.path.splitext(self.filename)[1].lower(), '')

    def _load(self, path):
        try:
            with open(path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            self.lines = content.splitlines() or ['']
            self.lang = self._detect_lang()
            self.modified = False
            self.message = f'Opened: {os.path.basename(path)}'
        except OSError as e:
            self.message = f'Error: {e}'

    def _save(self, path=None):
        target = path or self.filename
        if not target:
            target = self._prompt('File name to write: ', '')
            if not target:
                self.message = 'Cancelled.'; return
            self.filename = target
            self.lang = self._detect_lang()
        try:
            with open(target, 'w', encoding='utf-8') as f:
                f.write('\n'.join(self.lines) + '\n')
            self.filename = target
            self.modified = False
            self.message = f'Saved: {os.path.basename(target)}'
        except OSError as e:
            self.message = f'Save error: {e}'

    # ── Dimensions ───────────────────────────────────────────────────────────

    @property
    def H(self): return curses.LINES
    @property
    def W(self): return curses.COLS
    @property
    def editor_h(self): return max(1, self.H - 4)  # header + status + 2 shortcut rows
    @property
    def lnum_w(self): return len(str(len(self.lines))) + 2
    @property
    def edit_w(self): return max(1, self.W - self.lnum_w)

    # ── Drawing ───────────────────────────────────────────────────────────────

    def _draw(self):
        self.scr.erase()
        self._draw_header()
        self._draw_body()
        self._draw_status()
        self._draw_shortcuts()
        # Physical cursor
        sy = 1 + max(0, min(self.cy - self.top, self.editor_h - 1))
        sx = self.lnum_w + max(0, min(self.cx - self.left, self.edit_w - 1))
        try: self.scr.move(sy, sx)
        except curses.error: pass
        self.scr.refresh()

    def _safe(self, y, x, s, attr=0):
        if y < 0 or y >= self.H or x >= self.W: return
        s = s[:max(0, self.W - x)]
        try: self.scr.addstr(y, x, s, attr)
        except curses.error: pass

    def _draw_header(self):
        mod = ' [+]' if self.modified else ''
        name = os.path.basename(self.filename) if self.filename else 'New File'
        lang = f'  [{self.lang}]' if self.lang else ''
        left  = f'  TinyRetroPad Terminal'
        right = f'{name}{mod}{lang}  '
        gap   = max(1, self.W - len(left) - len(right))
        title = (left + ' ' * gap + right)[:self.W]
        self._safe(0, 0, title.ljust(self.W), curses.color_pair(_HEADER) | curses.A_BOLD)

    def _sel_range(self):
        """Return (sy, sx, ey, ex) normalized, or None if no selection."""
        if self.sel_anchor is None: return None
        ay, ax = self.sel_anchor
        by, bx = self.cy, self.cx
        if (ay, ax) == (by, bx): return None
        if (ay, ax) < (by, bx): return ay, ax, by, bx
        return by, bx, ay, ax

    def _sel_text(self):
        r = self._sel_range()
        if not r: return ''
        sy, sx, ey, ex = r
        if sy == ey: return self.lines[sy][sx:ex]
        parts = [self.lines[sy][sx:]] + self.lines[sy+1:ey] + [self.lines[ey][:ex]]
        return '\n'.join(parts)

    def _delete_sel(self):
        """Delete selected text. Returns True if there was a selection."""
        r = self._sel_range()
        if not r: return False
        self._snapshot()
        sy, sx, ey, ex = r
        if sy == ey:
            self.lines[sy] = self.lines[sy][:sx] + self.lines[sy][ex:]
        else:
            self.lines[sy] = self.lines[sy][:sx] + self.lines[ey][ex:]
            del self.lines[sy+1:ey+1]
        if not self.lines: self.lines = ['']
        self.cy, self.cx = sy, sx
        self.sel_anchor = None
        self.modified = True
        self._clamp()
        return True

    def _sel_for_row(self, row):
        """Return (sc, ec) selection column range on this row, or None."""
        r = self._sel_range()
        if not r: return None
        sy, sx, ey, ex = r
        if row < sy or row > ey: return None
        return (sx if row == sy else 0), (ex if row == ey else len(self.lines[row]) + 1)

    def _draw_body(self):
        lw = self.lnum_w
        ew = self.edit_w
        for row in range(self.editor_h):
            y      = row + 1
            docrow = row + self.top
            if docrow >= len(self.lines):
                self._safe(y, 0, '~'.ljust(lw), curses.color_pair(_DIM) | curses.A_DIM)
                continue
            # Line number
            is_cur = (docrow == self.cy)
            lnum   = str(docrow + 1).rjust(lw - 2) + ' │'
            lattr  = curses.color_pair(_STATUS) if is_cur else (curses.color_pair(_DIM) | curses.A_DIM)
            self._safe(y, 0, lnum, lattr)
            # Content
            line    = self.lines[docrow]
            visible = line[self.left : self.left + ew]
            sel     = self._sel_for_row(docrow)
            cmap    = _colormap(line, self.lang) if self.lang else None
            x = lw
            for ci in range(self.left, min(self.left + ew, len(line))):
                ch = line[ci]
                if cmap:
                    pair, bold = cmap[ci]
                else:
                    pair, bold = _NORMAL, 0
                attr = curses.color_pair(pair) | bold
                if sel and sel[0] <= ci < sel[1]:
                    attr = curses.color_pair(_HILIGHT) | curses.A_BOLD
                try: self.scr.addch(y, x, ch, attr)
                except curses.error: pass
                x += 1
            # Pad rest of line with selection color if selection extends to EOL
            if sel and sel[0] <= len(line) < sel[1] and x < self.W:
                try: self.scr.addch(y, x, ' ', curses.color_pair(_HILIGHT))
                except curses.error: pass
            # Search highlights (on top of everything)
            if self.search and not self._sel_range():
                pat = re.compile(re.escape(self.search), re.IGNORECASE)
                for m in pat.finditer(visible):
                    hx = lw + m.start()
                    self._safe(y, hx, m.group(), curses.color_pair(_HILIGHT) | curses.A_BOLD)

    def _draw_status(self):
        total = len(self.lines)
        pct   = int(100*(self.cy+1)/total) if total else 0
        pos   = f'Ln {self.cy+1}/{total}, Col {self.cx+1}  {pct}%  UTF-8  {self.lang or "text"}'
        msg   = self.message if self.message else pos
        self._safe(self.H-3, 0, f' {msg} '.ljust(self.W)[:self.W], curses.color_pair(_STATUS))
        self.message = ''

    def _draw_shortcuts(self):
        rows = [SHORTCUTS[:6], SHORTCUTS[6:]]
        for ri, row in enumerate(rows):
            x = 0; y = self.H - 2 + ri
            for key, desc in row:
                if x + len(key) + len(desc) + 2 >= self.W: break
                try:
                    self.scr.addstr(y, x, key, curses.A_REVERSE | curses.A_BOLD)
                    self.scr.addstr(y, x+len(key), f' {desc} ', curses.color_pair(_NORMAL))
                except curses.error: pass
                x += len(key) + len(desc) + 2

    # ── Mini-bar prompt ───────────────────────────────────────────────────────

    def _prompt(self, msg, default=''):
        buf = list(default); pos = len(buf)
        y = self.H - 3
        while True:
            bar = (msg + ''.join(buf)).ljust(self.W)[:self.W]
            try:
                self.scr.addstr(y, 0, bar, curses.color_pair(_STATUS))
                self.scr.move(y, min(len(msg)+pos, self.W-1))
            except curses.error: pass
            self.scr.refresh()
            ch = self.scr.getch()
            if ch in (10, 13):       return ''.join(buf)
            elif ch == 27:           return ''
            elif ch in (curses.KEY_BACKSPACE, 127, 8):
                if pos > 0: buf.pop(pos-1); pos -= 1
            elif ch == curses.KEY_LEFT  and pos > 0:     pos -= 1
            elif ch == curses.KEY_RIGHT and pos<len(buf): pos += 1
            elif ch == curses.KEY_HOME:  pos = 0
            elif ch == curses.KEY_END:   pos = len(buf)
            elif 32 <= ch <= 126: buf.insert(pos, chr(ch)); pos += 1

    # ── Undo / Redo ───────────────────────────────────────────────────────────

    def _snapshot(self):
        self.undo_stack.append((list(self.lines), self.cx, self.cy))
        self.redo_stack.clear()
        if len(self.undo_stack) > 300: self.undo_stack.pop(0)

    def _undo(self):
        if not self.undo_stack: self.message = 'Nothing to undo.'; return
        self.redo_stack.append((list(self.lines), self.cx, self.cy))
        self.lines, self.cx, self.cy = self.undo_stack.pop()
        self.modified = True; self.message = 'Undo.'; self._clamp()

    def _redo(self):
        if not self.redo_stack: self.message = 'Nothing to redo.'; return
        self.undo_stack.append((list(self.lines), self.cx, self.cy))
        self.lines, self.cx, self.cy = self.redo_stack.pop()
        self.modified = True; self.message = 'Redo.'; self._clamp()

    # ── Scroll / cursor ───────────────────────────────────────────────────────

    def _clamp(self):
        self.cy = max(0, min(self.cy, len(self.lines)-1))
        self.cx = max(0, min(self.cx, len(self.lines[self.cy])))
        if self.cy < self.top: self.top = self.cy
        elif self.cy >= self.top + self.editor_h: self.top = self.cy - self.editor_h + 1
        if self.cx < self.left: self.left = self.cx
        elif self.cx >= self.left + self.edit_w: self.left = self.cx - self.edit_w + 1

    def _move(self, dy, dx):
        self.cy = max(0, min(self.cy + dy, len(self.lines)-1))
        if dx:
            self.cx += dx
            line = self.lines[self.cy]
            if self.cx < 0 and self.cy > 0:
                self.cy -= 1; self.cx = len(self.lines[self.cy])
            elif self.cx > len(line) and self.cy < len(self.lines)-1:
                self.cy += 1; self.cx = 0
            else:
                self.cx = max(0, min(self.cx, len(self.lines[self.cy])))
        else:
            self.cx = min(self.cx, len(self.lines[self.cy]))
        self._clamp()

    def _move_word(self, fwd):
        line = self.lines[self.cy]
        if fwd:
            m = re.search(r'\W*\w+', line[self.cx:])
            if m: self.cx += m.end()
            elif self.cy < len(self.lines)-1: self.cy += 1; self.cx = 0
        else:
            m = re.search(r'\w+\W*$', line[:self.cx])
            if m: self.cx = m.start()
            elif self.cy > 0: self.cy -= 1; self.cx = len(self.lines[self.cy])
        self._clamp()

    def _page(self, down):
        d = self.editor_h - 1
        if down:
            self.cy  = min(self.cy  + d, len(self.lines)-1)
            self.top = min(self.top + d, max(0, len(self.lines)-self.editor_h))
        else:
            self.cy  = max(self.cy  - d, 0)
            self.top = max(self.top - d, 0)
        self.cx = min(self.cx, len(self.lines[self.cy]))
        self._clamp()

    # ── Editing ───────────────────────────────────────────────────────────────

    def _insert(self, ch):
        self._snapshot()
        line = self.lines[self.cy]
        self.lines[self.cy] = line[:self.cx] + ch + line[self.cx:]
        self.cx += len(ch); self.modified = True

    def _newline(self):
        self._snapshot()
        line = self.lines[self.cy]
        indent = re.match(r'^(\s*)', line).group(1)
        extra = ''
        if self.lang in ('python','js','c','php','ruby','go','rust'):
            if line.rstrip().endswith((':','{','(','[')):
                extra = '    '
        self.lines[self.cy] = line[:self.cx]
        self.lines.insert(self.cy+1, indent + extra + line[self.cx:])
        self.cy += 1; self.cx = len(indent)+len(extra)
        self.modified = True; self._clamp()

    def _backspace(self):
        self._snapshot()
        if self.cx > 0:
            l = self.lines[self.cy]
            self.lines[self.cy] = l[:self.cx-1] + l[self.cx:]
            self.cx -= 1
        elif self.cy > 0:
            self.cx = len(self.lines[self.cy-1])
            self.lines[self.cy-1] += self.lines[self.cy]
            self.lines.pop(self.cy); self.cy -= 1
        self.modified = True; self._clamp()

    def _delete_char(self):
        self._snapshot()
        l = self.lines[self.cy]
        if self.cx < len(l):
            self.lines[self.cy] = l[:self.cx] + l[self.cx+1:]
        elif self.cy < len(self.lines)-1:
            self.lines[self.cy] = l + self.lines[self.cy+1]
            self.lines.pop(self.cy+1)
        self.modified = True

    def _cut_line(self):
        self._snapshot()
        self.clipboard.append(self.lines[self.cy])
        self.lines.pop(self.cy)
        if not self.lines: self.lines = ['']
        self.cy = min(self.cy, len(self.lines)-1)
        self.cx = min(self.cx, len(self.lines[self.cy]))
        self.modified = True; self.message = 'Line cut (^U to paste).'; self._clamp()

    def _paste(self):
        if not self.clipboard: self.message = 'Nothing to paste.'; return
        self._snapshot()
        for ln in self.clipboard:
            self.lines.insert(self.cy, ln); self.cy += 1
        self.modified = True
        self.message = f'Pasted {len(self.clipboard)} line(s).'
        self._clamp()

    def _tab(self):
        self._insert(' ' * (4 - self.cx % 4))

    def _duplicate_line(self):
        self._snapshot()
        self.lines.insert(self.cy+1, self.lines[self.cy])
        self.cy += 1; self.modified = True; self._clamp()
        self.message = 'Line duplicated.'

    # ── Search ────────────────────────────────────────────────────────────────

    def _search_dialog(self):
        hint = f' [{self.search}]' if self.search else ''
        q = self._prompt(f'Search{hint}: ')
        if q: self.search = q
        if self.search: self._find_next()

    def _find_next(self, backward=False):
        if not self.search: self.message = 'No search term (^W to set).'; return
        pat = re.compile(re.escape(self.search), re.IGNORECASE)
        rows = range(len(self.lines))
        order = list(rows[self.cy:]) + list(rows[:self.cy]) if not backward else \
                list(reversed(rows[:self.cy+1])) + list(reversed(rows[self.cy:]))
        for i, row in enumerate(order):
            sc = self.cx+1 if (i == 0 and not backward) else 0
            m  = pat.search(self.lines[row], sc) if not backward else \
                 list(pat.finditer(self.lines[row]))
            if not backward and m:
                self.cy = row; self.cx = m.start()
                self.message = f"Found '{self.search}'  (^N next)"
                self._clamp(); return
            elif backward and m:
                last = [x for x in m if x.end() <= self.cx] if i==0 else m
                if last:
                    self.cy = row; self.cx = last[-1].start()
                    self.message = f"Found '{self.search}'"
                    self._clamp(); return
        self.message = f"'{self.search}' not found."

    def _goto_line(self):
        s = self._prompt('Go to line: ')
        if not s: return
        try:
            n = int(s)-1
            self.cy = max(0, min(n, len(self.lines)-1)); self.cx = 0
            self._clamp(); self.message = f'Jumped to line {self.cy+1}.'
        except ValueError:
            self.message = 'Invalid line number.'

    # ── Help overlay ─────────────────────────────────────────────────────────

    def _help(self):
        lines = [
            '  TinyRetroPad Terminal — Help',
            '',
            '  Navigation',
            '    Arrow keys       move cursor',
            '    Ctrl+Left/Right  move by word',
            '    Home / End       line start / end',
            '    Ctrl+A / Ctrl+E  line start / end',
            '    PgUp / PgDn      page up / down',
            '    Ctrl+Y / Ctrl+V  page up / down (nano)',
            '    Ctrl+T           jump to end of file',
            '',
            '  Editing',
            '    Tab              smart indent (4 spaces)',
            '    Ctrl+D           duplicate current line',
            '    Ctrl+K           cut current line',
            '    Ctrl+U           paste cut buffer',
            '    Ctrl+Z           undo',
            '    Ctrl+R           redo',
            '',
            '  File',
            '    Ctrl+O           save  (prompts if unnamed)',
            '    Ctrl+X           exit  (asks to save if modified)',
            '',
            '  Search',
            '    Ctrl+W           find (enter query)',
            '    Ctrl+N           find next',
            '    Ctrl+P           find previous',
            '    Ctrl+/           go to line number',
            '',
            '  Other',
            '    Ctrl+C           show cursor position',
            '    Ctrl+G           this help screen',
            '',
            '  Press any key to close.',
        ]
        bh = min(len(lines)+2, self.H-2)
        bw = min(max(len(l) for l in lines)+4, self.W-4)
        by = (self.H-bh)//2; bx = (self.W-bw)//2
        try:
            box = curses.newwin(bh, bw, by, bx)
            box.bkgd(' ', curses.color_pair(_STATUS))
            box.box()
            for i, ln in enumerate(lines[:bh-2]):
                box.addstr(i+1, 2, ln[:bw-4])
            box.refresh(); box.getch()
        except curses.error: pass

    # ── Quit ─────────────────────────────────────────────────────────────────

    def _quit(self):
        if not self.modified: return True
        ans = self._prompt('Save before exit? [y/n]: ').lower()
        if ans == 'y': self._save(); return True
        if ans == 'n': return True
        return False

    # ── Main loop ─────────────────────────────────────────────────────────────

    def run(self):
        curses.curs_set(1)
        curses.raw()          # capture Ctrl+C as key code 3, not SIGINT
        self.scr.keypad(True)
        try: curses.mousemask(curses.ALL_MOUSE_EVENTS | curses.REPORT_MOUSE_POSITION)
        except Exception: pass

        while True:
            self._draw()
            key = self.scr.getch()

            # Mouse
            if key == curses.KEY_MOUSE:
                try:
                    _, mx, my, _, bs = curses.getmouse()
                    if _SCROLL_UP   and bs & _SCROLL_UP:   self._page(False)
                    elif _SCROLL_DOWN and bs & _SCROLL_DOWN: self._page(True)
                    elif 1 <= my <= self.editor_h:
                        ny = self.top + my - 1
                        nx = self.left + max(0, mx - self.lnum_w)
                        ny = max(0, min(ny, len(self.lines)-1))
                        nx = max(0, min(nx, len(self.lines[ny])))
                        if bs & curses.BUTTON1_PRESSED:
                            # Start fresh selection anchor
                            self.sel_anchor  = (ny, nx)
                            self._mouse_down = True
                            self.cy, self.cx = ny, nx
                            self._clamp()
                        elif bs & curses.REPORT_MOUSE_POSITION and self._mouse_down:
                            # Dragging — extend selection
                            self.cy, self.cx = ny, nx
                            self._clamp()
                        elif bs & curses.BUTTON1_RELEASED:
                            self._mouse_down = False
                            self.cy, self.cx = ny, nx
                            self._clamp()
                            if self.sel_anchor == (self.cy, self.cx):
                                self.sel_anchor = None
                            elif self._sel_range():
                                # Auto-copy selection to system clipboard on release
                                txt = self._sel_text()
                                _sys_copy(txt)
                                self.message = f'Selected {len(txt)} char(s) → clipboard. Ctrl+V to paste anywhere.'
                except curses.error: pass
                continue

            if key == curses.KEY_RESIZE:
                curses.update_lines_cols(); self._clamp(); continue

            # ── Arrow / nav keys (clear selection) ───────────────────────
            if   key == curses.KEY_UP:
                self.sel_anchor = None; self._move(-1, 0)
            elif key == curses.KEY_DOWN:
                self.sel_anchor = None; self._move(1, 0)
            elif key == curses.KEY_LEFT:
                self.sel_anchor = None; self._move(0, -1)
            elif key == curses.KEY_RIGHT:
                self.sel_anchor = None; self._move(0, 1)
            elif key == curses.KEY_HOME:
                self.sel_anchor = None; self.cx = 0; self._clamp()
            elif key == curses.KEY_END:
                self.sel_anchor = None; self.cx = len(self.lines[self.cy]); self._clamp()
            elif key == curses.KEY_PPAGE:
                self.sel_anchor = None; self._page(False)
            elif key == curses.KEY_NPAGE:
                self.sel_anchor = None; self._page(True)
            elif key == curses.KEY_DC:
                if not self._delete_sel(): self._delete_char()
            elif key in (curses.KEY_BACKSPACE, 127, 8):
                if not self._delete_sel(): self._backspace()

            # Ctrl+Left / Ctrl+Right
            elif key in (545, 546, 544):
                self.sel_anchor = None; self._move_word(False)
            elif key in (560, 561, 559):
                self.sel_anchor = None; self._move_word(True)

            # ── Ctrl keys ─────────────────────────────────────────────────
            elif key == 1:   # ^A — select all
                self.sel_anchor = (0, 0)
                self.cy = len(self.lines)-1; self.cx = len(self.lines[-1]); self._clamp()
            elif key == 5:   # ^E — line end
                self.sel_anchor = None; self.cx = len(self.lines[self.cy]); self._clamp()
            elif key == 20:  # ^T — file end
                self.sel_anchor = None
                self.cy = len(self.lines)-1; self.cx = len(self.lines[self.cy]); self._clamp()
            elif key == 25:  # ^Y — page up (nano compat)
                self.sel_anchor = None; self._page(False)
            elif key == 23:  # ^W — find
                self.sel_anchor = None; self._search_dialog()
            elif key == 14:  # ^N — find next
                self._find_next()
            elif key == 16:  # ^P — find previous
                self._find_next(backward=True)
            elif key == 15:  # ^O — save
                self._save()
            elif key == 24:  # ^X — cut selection or exit
                if self._sel_range():
                    txt = self._sel_text()
                    self.clipboard = txt.splitlines() or ['']
                    _sys_copy(txt)
                    self._delete_sel()
                    self.message = f'Cut {len(txt)} char(s) → system clipboard.'
                else:
                    if self._quit(): break
            elif key == 3:   # ^C — copy selection or show position
                if self._sel_range():
                    txt = self._sel_text()
                    self.clipboard = txt.splitlines() or ['']
                    _sys_copy(txt)
                    self.message = f'Copied {len(txt)} char(s) → system clipboard.'
                else:
                    total = len(self.lines)
                    chars = sum(len(l) for l in self.lines)
                    self.message = f'Ln {self.cy+1}/{total}  Col {self.cx+1}  {chars:,} chars  {self.lang or "text"}'
            elif key == 22:  # ^V — paste from system clipboard
                txt = _sys_paste()
                if txt:
                    self._delete_sel()
                    self._snapshot()
                    for i, part in enumerate(txt.splitlines()):
                        if i == 0:
                            self._insert(part)
                        else:
                            self._newline()
                            # _newline adds auto-indent, insert remainder after it
                            line = self.lines[self.cy]
                            indent_len = len(line) - len(line.lstrip())
                            self.lines[self.cy] = line[:indent_len] + part
                            self.cx = indent_len + len(part)
                    self.message = f'Pasted {len(txt)} char(s) from system clipboard.'
                else:
                    self.message = 'System clipboard is empty.'
                continue
            elif key == 26:  # ^Z — undo
                self.sel_anchor = None; self._undo()
            elif key == 18:  # ^R — redo
                self.sel_anchor = None; self._redo()
            elif key == 11:  # ^K — cut line
                self.sel_anchor = None; self._cut_line()
            elif key == 21:  # ^U — paste
                self._paste()
            elif key == 4:   # ^D — duplicate line
                self._duplicate_line()
            elif key == 7:   # ^G — help
                self._help()
            elif key in (28, 47):  # ^\ or / — go to line
                self._goto_line()
            elif key == 9:   # Tab
                self._delete_sel(); self._tab()
            elif key in (10, 13):  # Enter
                self._delete_sel(); self._newline()
            elif 32 <= key <= 126:
                self._delete_sel(); self._insert(chr(key))


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    fn = sys.argv[1] if len(sys.argv) > 1 else None
    try:
        curses.wrapper(lambda s: Editor(s, fn).run())
    except KeyboardInterrupt:
        pass
    print('Bye.')

if __name__ == '__main__':
    main()
