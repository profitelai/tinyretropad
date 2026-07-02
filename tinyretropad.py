#!/usr/bin/env python3
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, font as tkfont
import os, sys, re
from datetime import datetime

THEMES = {
    "light": {"bg":"#ffffff","fg":"#1a1a1a","sel_bg":"#0078d7","sel_fg":"#ffffff",
              "status_bg":"#f0f0f0","status_fg":"#444444","find_bg":"#ffff88","cursor":"#000000"},
    "dark":  {"bg":"#1e1e1e","fg":"#d4d4d4","sel_bg":"#264f78","sel_fg":"#ffffff",
              "status_bg":"#007acc","status_fg":"#ffffff","find_bg":"#7b5600","cursor":"#aeafad"},
}

class TinyRetroPad:
    APP_NAME = "TinyRetroPad"

    def __init__(self, root):
        self.root = root
        self.current_file = None
        self.modified = False
        self._find_query = ""
        self._find_start = "1.0"
        self._find_win = None
        self._replace_win = None
        self._find_case = tk.BooleanVar(value=False)
        self._find_regex = tk.BooleanVar(value=False)
        self._find_word  = tk.BooleanVar(value=False)
        self._find_wrap  = tk.BooleanVar(value=True)
        self.word_wrap      = tk.BooleanVar(value=True)
        self.show_statusbar = tk.BooleanVar(value=True)
        self.dark_mode      = tk.BooleanVar(value=False)
        self.show_linenums  = tk.BooleanVar(value=False)
        self._build_menu()
        self._build_editor()
        self._build_statusbar()
        self._apply_theme()
        self._set_title()
        self.editor_font = tkfont.Font(family="Monospace", size=11)
        self.text.configure(font=self.editor_font)
        self.line_nums.configure(font=self.editor_font)
        self.text.bind("<<Modified>>",    self._on_modified)
        self.text.bind("<KeyRelease>",    self._on_keyrelease)
        self.text.bind("<ButtonRelease>", self._update_status)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self._bind_shortcuts()
        self._update_status()

    def _build_menu(self):
        mb = tk.Menu(self.root, tearoff=0)
        m = tk.Menu(mb, tearoff=0)
        m.add_command(label="New",      accelerator="Ctrl+N",       command=self._new)
        m.add_command(label="Open…",    accelerator="Ctrl+O",       command=self._open)
        m.add_separator()
        m.add_command(label="Save",     accelerator="Ctrl+S",       command=self._save)
        m.add_command(label="Save As…", accelerator="Ctrl+Shift+S", command=self._save_as)
        m.add_separator()
        m.add_command(label="Exit",     accelerator="Alt+F4",       command=self._on_close)
        mb.add_cascade(label="File", menu=m)
        m = tk.Menu(mb, tearoff=0)
        m.add_command(label="Undo",      accelerator="Ctrl+Z", command=self._undo)
        m.add_separator()
        m.add_command(label="Cut",       accelerator="Ctrl+X", command=lambda: self.text.event_generate("<<Cut>>"))
        m.add_command(label="Copy",      accelerator="Ctrl+C", command=lambda: self.text.event_generate("<<Copy>>"))
        m.add_command(label="Paste",     accelerator="Ctrl+V", command=lambda: self.text.event_generate("<<Paste>>"))
        m.add_command(label="Delete",    accelerator="Del",    command=self._delete_selection)
        m.add_separator()
        m.add_command(label="Find…",     accelerator="Ctrl+F", command=self._find_dialog)
        m.add_command(label="Find Next", accelerator="F3",     command=self._find_next)
        m.add_command(label="Replace…",  accelerator="Ctrl+H", command=self._replace_dialog)
        m.add_command(label="Go To…",    accelerator="Ctrl+G", command=self._goto_dialog)
        m.add_separator()
        m.add_command(label="Select All", accelerator="Ctrl+A", command=self._select_all)
        m.add_command(label="Time/Date",  accelerator="F5",     command=self._insert_datetime)
        mb.add_cascade(label="Edit", menu=m)
        m = tk.Menu(mb, tearoff=0)
        m.add_checkbutton(label="Word Wrap",    variable=self.word_wrap,     command=self._toggle_wrap)
        m.add_checkbutton(label="Line Numbers", variable=self.show_linenums, command=self._toggle_linenums)
        m.add_separator()
        m.add_command(label="Font…", command=self._font_dialog)
        mb.add_cascade(label="Format", menu=m)
        m = tk.Menu(mb, tearoff=0)
        m.add_checkbutton(label="Status Bar", variable=self.show_statusbar, command=self._toggle_statusbar)
        m.add_checkbutton(label="Dark Mode",  variable=self.dark_mode,      command=self._apply_theme)
        mb.add_cascade(label="View", menu=m)
        m = tk.Menu(mb, tearoff=0)
        m.add_command(label="About TinyRetroPad", command=self._about)
        mb.add_cascade(label="Help", menu=m)
        self.root.config(menu=mb)

    def _build_editor(self):
        self.editor_frame = tk.Frame(self.root)
        self.editor_frame.pack(fill=tk.BOTH, expand=True)
        self.line_nums = tk.Text(self.editor_frame, width=4, padx=4, pady=4,
                                 state=tk.DISABLED, takefocus=0, relief=tk.FLAT, cursor="arrow")
        vsb = tk.Scrollbar(self.editor_frame, orient=tk.VERTICAL)
        hsb = tk.Scrollbar(self.editor_frame, orient=tk.HORIZONTAL)
        self.text = tk.Text(self.editor_frame, wrap=tk.WORD, undo=True, maxundo=-1,
                            yscrollcommand=self._on_yscroll, xscrollcommand=hsb.set,
                            relief=tk.FLAT, padx=6, pady=6, insertwidth=2, selectborderwidth=0)
        vsb.config(command=self._on_textscroll)
        hsb.config(command=self.text.xview)
        vsb.pack(side=tk.RIGHT,  fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        self.text.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self.vsb = vsb
        self.text.tag_configure("found", background="#ffff88", foreground="#000000")

    def _on_yscroll(self, *a):
        self.vsb.set(*a)
        self._update_line_nums()

    def _on_textscroll(self, *a):
        self.text.yview(*a)
        self._update_line_nums()

    def _build_statusbar(self):
        self.status_frame = tk.Frame(self.root, height=22)
        self.status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        self.status_frame.pack_propagate(False)
        self.status_pos   = tk.Label(self.status_frame, text="Ln 1, Col 1", anchor=tk.W, padx=8)
        self.status_file  = tk.Label(self.status_frame, text="UTF-8 · LF",  anchor=tk.E, padx=8)
        self.status_chars = tk.Label(self.status_frame, text="0 chars",      anchor=tk.E, padx=8)
        self.status_pos.pack(side=tk.LEFT)
        self.status_file.pack(side=tk.RIGHT)
        self.status_chars.pack(side=tk.RIGHT)

    def _update_status(self, event=None):
        line, col = self.text.index(tk.INSERT).split(".")
        self.status_pos.config(text=f"Ln {line}, Col {int(col)+1}")
        self.status_chars.config(text=f"{len(self.text.get('1.0', tk.END+'-1c')):,} chars")

    def _update_line_nums(self, event=None):
        if not self.show_linenums.get():
            return
        self.line_nums.config(state=tk.NORMAL)
        self.line_nums.delete("1.0", tk.END)
        count = int(self.text.index("end-1c").split(".")[0])
        self.line_nums.insert("1.0", "\n".join(str(i) for i in range(1, count+1)))
        self.line_nums.config(state=tk.DISABLED)

    def _toggle_linenums(self):
        if self.show_linenums.get():
            self.line_nums.pack(side=tk.LEFT, fill=tk.Y, before=self.text)
            self._update_line_nums()
        else:
            self.line_nums.pack_forget()

    def _apply_theme(self):
        t = THEMES["dark" if self.dark_mode.get() else "light"]
        self.root.config(bg=t["bg"])
        self.editor_frame.config(bg=t["bg"])
        self.text.config(bg=t["bg"], fg=t["fg"], insertbackground=t["cursor"],
                         selectbackground=t["sel_bg"], selectforeground=t["sel_fg"])
        self.text.tag_configure("found", background=t["find_bg"],
                                foreground="#000000" if not self.dark_mode.get() else "#ffffff")
        self.line_nums.config(bg=t["status_bg"], fg=t["status_fg"])
        self.status_frame.config(bg=t["status_bg"])
        for w in (self.status_pos, self.status_file, self.status_chars):
            w.config(bg=t["status_bg"], fg=t["status_fg"])

    def _set_title(self, dirty=False):
        name = os.path.basename(self.current_file) if self.current_file else "Untitled"
        self.root.title(f"{'* ' if dirty else ''}{name} — {self.APP_NAME}")

    def _on_modified(self, event=None):
        if self.text.edit_modified():
            self.modified = True
            self._set_title(dirty=True)
            self._update_line_nums()
        self.text.edit_modified(False)

    def _on_keyrelease(self, event=None):
        self._update_status()
        self._update_line_nums()

    def _ask_save_if_dirty(self):
        if not self.modified:
            return True
        name = os.path.basename(self.current_file) if self.current_file else "Untitled"
        ans = messagebox.askyesnocancel(self.APP_NAME, f'Save changes to "{name}"?', parent=self.root)
        if ans is True:  return self._save()
        if ans is False: return True
        return False

    def _new(self):
        if not self._ask_save_if_dirty(): return
        self.text.delete("1.0", tk.END)
        self.text.edit_reset()
        self.current_file = None
        self.modified = False
        self._set_title()
        self._update_status()
        self._update_line_nums()

    def _open(self):
        if not self._ask_save_if_dirty(): return
        path = filedialog.askopenfilename(parent=self.root,
                                          filetypes=[("Text files","*.txt"),("All files","*.*")])
        if not path: return
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except OSError as e:
            messagebox.showerror("Open Error", str(e), parent=self.root); return
        self.text.delete("1.0", tk.END)
        self.text.insert("1.0", content)
        self.text.edit_reset()
        self.text.mark_set(tk.INSERT, "1.0")
        self.current_file = path
        self.modified = False
        self._set_title()
        self._update_status()
        self._update_line_nums()
        self.status_file.config(text="UTF-8 · LF")

    def _save(self):
        return self._write(self.current_file) if self.current_file else self._save_as()

    def _save_as(self):
        path = filedialog.asksaveasfilename(parent=self.root, defaultextension=".txt",
                                            filetypes=[("Text files","*.txt"),("All files","*.*")])
        if not path: return False
        self.current_file = path
        return self._write(path)

    def _write(self, path):
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.text.get("1.0", tk.END+"-1c"))
            self.modified = False
            self._set_title()
            return True
        except OSError as e:
            messagebox.showerror("Save Error", str(e), parent=self.root)
            return False

    def _undo(self):
        try: self.text.edit_undo()
        except tk.TclError: pass

    def _delete_selection(self):
        try: self.text.delete(tk.SEL_FIRST, tk.SEL_LAST)
        except tk.TclError: pass

    def _select_all(self):
        self.text.tag_add(tk.SEL, "1.0", tk.END)
        self.text.mark_set(tk.INSERT, tk.END)

    def _insert_datetime(self):
        self.text.insert(tk.INSERT, datetime.now().strftime("%I:%M %p %m/%d/%Y"))

    def _search_options(self, parent, row=1):
        """Render shared search option checkboxes. Returns the frame."""
        f = tk.LabelFrame(parent, text="Options", padx=6, pady=4)
        f.grid(row=row, column=0, columnspan=3, padx=10, pady=(0,6), sticky="ew")
        tk.Checkbutton(f, text="Match case",  variable=self._find_case).pack(side=tk.LEFT, padx=6)
        tk.Checkbutton(f, text="Whole word",  variable=self._find_word).pack(side=tk.LEFT, padx=6)
        tk.Checkbutton(f, text="Regex",       variable=self._find_regex).pack(side=tk.LEFT, padx=6)
        tk.Checkbutton(f, text="Wrap around", variable=self._find_wrap).pack(side=tk.LEFT, padx=6)
        return f

    def _build_pattern(self, query):
        """Compile a re.Pattern from current query and option flags. Raises re.error on bad regex."""
        flags = 0 if self._find_case.get() else re.IGNORECASE
        if self._find_regex.get():
            pat = re.compile(query, flags)
        else:
            escaped = re.escape(query)
            if self._find_word.get():
                escaped = rf"\b{escaped}\b"
            pat = re.compile(escaped, flags)
        return pat

    def _find_all_matches(self, content, pat):
        """Return list of (start_char, end_char) for every match in content."""
        return [(m.start(), m.end()) for m in pat.finditer(content)]

    def _char_to_index(self, content, char_pos):
        """Convert absolute char offset in content to Tkinter 'line.col' index."""
        line = content[:char_pos].count("\n") + 1
        col  = char_pos - content[:char_pos].rfind("\n") - 1
        return f"{line}.{col}"

    def _find_dialog(self):
        if self._find_win and self._find_win.winfo_exists():
            self._find_win.lift(); return
        win = tk.Toplevel(self.root)
        win.title("Find"); win.resizable(False, False); win.transient(self.root)
        self._find_win = win
        tk.Label(win, text="Find:").grid(row=0, column=0, padx=10, pady=8, sticky="w")
        q_var = tk.StringVar(value=self._find_query)
        q_ent = tk.Entry(win, textvariable=q_var, width=36)
        q_ent.grid(row=0, column=1, padx=10, pady=8, columnspan=2, sticky="ew")
        q_ent.focus_set()
        self._search_options(win, row=1)
        status = tk.Label(win, text="", anchor="w", fg="gray")
        status.grid(row=3, column=0, columnspan=2, padx=10, sticky="w")
        def do_find():
            self._find_query = q_var.get()
            self._find_start = "1.0"
            self._find_next(status_label=status)
        def do_find_all():
            self._find_query = q_var.get()
            self._highlight_all(status_label=status)
        bf = tk.Frame(win)
        bf.grid(row=3, column=2, padx=6, pady=4, sticky="e")
        tk.Button(bf, text="Find Next", width=11, default=tk.ACTIVE, command=do_find).pack(pady=2)
        tk.Button(bf, text="Find All",  width=11, command=do_find_all).pack(pady=2)
        tk.Button(bf, text="Close",     width=11, command=win.destroy).pack(pady=2)
        win.bind("<Return>", lambda e: do_find())
        win.bind("<Escape>", lambda e: win.destroy())

    def _find_next(self, status_label=None):
        self.text.tag_remove("found", "1.0", tk.END)
        if not self._find_query: return
        try:
            pat = self._build_pattern(self._find_query)
        except re.error as e:
            messagebox.showerror("Regex Error", str(e), parent=self.root); return
        content = self.text.get("1.0", tk.END+"-1c")
        start_char = len(self.text.get("1.0", self._find_start+"-1c")) if self._find_start != "1.0" else 0
        matches = self._find_all_matches(content, pat)
        if not matches:
            msg = "No matches found."
            if status_label: status_label.config(text=msg)
            else: messagebox.showinfo("Find", f'"{self._find_query}" not found.', parent=self.root)
            return
        # Find next match at or after current position
        nxt = next((m for m in matches if m[0] >= start_char), None)
        if nxt is None:
            if self._find_wrap.get():
                nxt = matches[0]
                if status_label: status_label.config(text=f"Wrapped · {len(matches)} match(es)")
            else:
                msg = "No more matches."
                if status_label: status_label.config(text=msg)
                else: messagebox.showinfo("Find", msg, parent=self.root)
                return
        else:
            if status_label: status_label.config(text=f"{len(matches)} match(es)")
        idx  = self._char_to_index(content, nxt[0])
        iend = self._char_to_index(content, nxt[1])
        self.text.tag_add("found", idx, iend)
        self.text.see(idx)
        self.text.mark_set(tk.INSERT, idx)
        self._find_start = iend

    def _highlight_all(self, status_label=None):
        self.text.tag_remove("found", "1.0", tk.END)
        if not self._find_query: return
        try:
            pat = self._build_pattern(self._find_query)
        except re.error as e:
            messagebox.showerror("Regex Error", str(e), parent=self.root); return
        content = self.text.get("1.0", tk.END+"-1c")
        matches = self._find_all_matches(content, pat)
        for s, e in matches:
            self.text.tag_add("found", self._char_to_index(content, s), self._char_to_index(content, e))
        msg = f"{len(matches)} match(es) highlighted" if matches else "No matches found."
        if status_label: status_label.config(text=msg)
        else: messagebox.showinfo("Find All", msg, parent=self.root)
        if matches:
            self.text.see(self._char_to_index(content, matches[0][0]))

    def _replace_dialog(self):
        if self._replace_win and self._replace_win.winfo_exists():
            self._replace_win.lift(); return
        win = tk.Toplevel(self.root)
        win.title("Find & Replace"); win.resizable(False, False); win.transient(self.root)
        self._replace_win = win
        tk.Label(win, text="Find:").grid(   row=0, column=0, padx=10, pady=6, sticky="w")
        tk.Label(win, text="Replace:").grid(row=1, column=0, padx=10, pady=6, sticky="w")
        q_var = tk.StringVar(value=self._find_query)
        r_var = tk.StringVar()
        tk.Entry(win, textvariable=q_var, width=36).grid(row=0, column=1, columnspan=2, padx=10, pady=6, sticky="ew")
        tk.Entry(win, textvariable=r_var, width=36).grid(row=1, column=1, columnspan=2, padx=10, pady=6, sticky="ew")
        tk.Label(win, text="  Tip: use \\1 \\2 for capture groups in Replace (Regex mode)",
                 fg="gray", font=("", 9)).grid(row=2, column=0, columnspan=3, padx=10, sticky="w")
        self._search_options(win, row=3)
        status = tk.Label(win, text="", anchor="w", fg="gray")
        status.grid(row=5, column=0, columnspan=2, padx=10, pady=(0,4), sticky="w")
        win.grid_columnconfigure(1, weight=1)
        def do_replace_next():
            self._find_query = q_var.get()
            self._find_next(status_label=status)
            try:
                pat = self._build_pattern(self._find_query)
                s = self.text.index(tk.SEL_FIRST)
                e = self.text.index(tk.SEL_LAST)
                selected = self.text.get(s, e)
                m = pat.fullmatch(selected)
                replacement = m.expand(r_var.get()) if (m and self._find_regex.get()) else r_var.get()
                self.text.delete(s, e)
                self.text.insert(s, replacement)
            except (tk.TclError, re.error): pass
        def do_replace_all():
            self._find_query = q_var.get()
            try:
                pat = self._build_pattern(self._find_query)
            except re.error as e:
                messagebox.showerror("Regex Error", str(e), parent=self.root); return
            content = self.text.get("1.0", tk.END+"-1c")
            try:
                new, count = pat.subn(r_var.get(), content)
            except re.error as e:
                messagebox.showerror("Replace Error", str(e), parent=self.root); return
            self.text.delete("1.0", tk.END)
            self.text.insert("1.0", new)
            status.config(text=f"{count} replacement(s) made.")
        def do_find_all():
            self._find_query = q_var.get()
            self._highlight_all(status_label=status)
        bf = tk.Frame(win)
        bf.grid(row=5, column=2, padx=6, pady=4, sticky="e")
        tk.Button(bf, text="Find Next",   width=13, command=do_replace_next).pack(pady=2)
        tk.Button(bf, text="Find All",    width=13, command=do_find_all).pack(pady=2)
        tk.Button(bf, text="Replace",     width=13, command=do_replace_next).pack(pady=2)
        tk.Button(bf, text="Replace All", width=13, command=do_replace_all).pack(pady=2)
        tk.Button(bf, text="Close",       width=13, command=win.destroy).pack(pady=2)
        win.bind("<Escape>", lambda e: win.destroy())
        q_var.focus_set()

    def _goto_dialog(self):
        total = int(self.text.index("end-1c").split(".")[0])
        line = simpledialog.askinteger("Go To Line", f"Line number (1–{total}):",
                                       parent=self.root, minvalue=1, maxvalue=total)
        if line:
            self.text.see(f"{line}.0"); self.text.mark_set(tk.INSERT, f"{line}.0")
            self._update_status()

    def _toggle_wrap(self):
        self.text.config(wrap=tk.WORD if self.word_wrap.get() else tk.NONE)

    def _font_dialog(self):
        win = tk.Toplevel(self.root)
        win.title("Font"); win.resizable(True, False); win.transient(self.root); win.grab_set()
        cf = self.editor_font.cget("family")
        cs = self.editor_font.cget("size")
        cw = self.editor_font.cget("weight")
        cl = self.editor_font.cget("slant")
        families = sorted(set(tkfont.families()))
        tk.Label(win, text="Font:").grid(row=0, column=0, padx=8, pady=(8,2), sticky="w")
        fam_var = tk.StringVar()
        tk.Entry(win, textvariable=fam_var, width=26).grid(row=1, column=0, padx=8, sticky="ew")
        fsb = tk.Scrollbar(win, orient=tk.VERTICAL)
        flb = tk.Listbox(win, yscrollcommand=fsb.set, height=12, width=26, exportselection=False)
        fsb.config(command=flb.yview)
        flb.grid(row=2, column=0, padx=(8,0), pady=4, sticky="nsew")
        fsb.grid(row=2, column=1, pady=4, sticky="ns")
        for f in families: flb.insert(tk.END, f)
        if cf in families:
            i = families.index(cf); flb.selection_set(i); flb.see(i)
        def filter_fonts(*_):
            q = fam_var.get().lower(); flb.delete(0, tk.END)
            for f in families:
                if q in f.lower(): flb.insert(tk.END, f)
        fam_var.trace_add("write", filter_fonts)
        SIZES = [7,8,9,10,11,12,13,14,16,18,20,22,24,28,32,36,48,60,72]
        tk.Label(win, text="Size:").grid(row=0, column=2, padx=8, pady=(8,2), sticky="w")
        svar = tk.StringVar(value=str(cs))
        tk.Entry(win, textvariable=svar, width=6).grid(row=1, column=2, padx=8, sticky="w")
        ssb = tk.Scrollbar(win, orient=tk.VERTICAL)
        slb = tk.Listbox(win, yscrollcommand=ssb.set, height=12, width=6, exportselection=False)
        ssb.config(command=slb.yview)
        slb.grid(row=2, column=2, padx=(8,0), pady=4, sticky="ns")
        ssb.grid(row=2, column=3, pady=4, sticky="ns")
        for s in SIZES: slb.insert(tk.END, str(s))
        if cs in SIZES:
            i = SIZES.index(cs); slb.selection_set(i); slb.see(i)
        slb.bind("<<ListboxSelect>>", lambda e: svar.set(slb.get(slb.curselection()[0])) if slb.curselection() else None)
        tk.Label(win, text="Style:").grid(row=0, column=4, padx=8, pady=(8,2), sticky="w")
        styles = ["Regular","Bold","Italic","Bold Italic"]
        stlb = tk.Listbox(win, height=4, width=12, exportselection=False)
        stlb.grid(row=2, column=4, padx=8, pady=4, sticky="n")
        for s in styles: stlb.insert(tk.END, s)
        cur_style = ("Bold Italic" if cw=="bold" and cl=="italic" else
                     "Bold" if cw=="bold" else "Italic" if cl=="italic" else "Regular")
        stlb.selection_set(styles.index(cur_style))
        prev = tk.Label(win, text="AaBbCcDd 0123456789", relief=tk.GROOVE, width=42, height=2, anchor="w", padx=8)
        tk.Label(win, text="Sample:").grid(row=3, column=0, padx=8, pady=(6,2), sticky="w")
        prev.grid(row=4, column=0, columnspan=5, padx=8, pady=4, sticky="ew")
        def update_prev(*_):
            fam = flb.get(flb.curselection()[0]) if flb.curselection() else cf
            try: sz = int(svar.get())
            except ValueError: sz = cs
            s = styles[stlb.curselection()[0]] if stlb.curselection() else "Regular"
            prev.config(font=(fam, sz, "bold" if "Bold" in s else "normal",
                               "italic" if "Italic" in s else "roman"))
        flb.bind("<<ListboxSelect>>",  update_prev)
        slb.bind("<<ListboxSelect>>",  update_prev)
        stlb.bind("<<ListboxSelect>>", update_prev)
        svar.trace_add("write", update_prev)
        bf = tk.Frame(win)
        bf.grid(row=5, column=0, columnspan=5, pady=10, padx=8, sticky="e")
        def apply_font():
            fam = flb.get(flb.curselection()[0]) if flb.curselection() else cf
            try: sz = int(svar.get())
            except ValueError: sz = cs
            s  = styles[stlb.curselection()[0]] if stlb.curselection() else "Regular"
            self.editor_font.config(family=fam, size=sz,
                                    weight="bold" if "Bold" in s else "normal",
                                    slant="italic" if "Italic" in s else "roman")
            self.text.config(font=self.editor_font)
            self.line_nums.config(font=self.editor_font)
            win.destroy()
        tk.Button(bf, text="OK",     width=10, default=tk.ACTIVE, command=apply_font).pack(side=tk.LEFT, padx=4)
        tk.Button(bf, text="Cancel", width=10, command=win.destroy).pack(side=tk.LEFT, padx=4)
        win.bind("<Return>", lambda e: apply_font())
        win.bind("<Escape>", lambda e: win.destroy())

    def _toggle_statusbar(self):
        if self.show_statusbar.get():
            self.status_frame.pack(side=tk.BOTTOM, fill=tk.X, before=self.editor_frame)
        else:
            self.status_frame.pack_forget()

    def _about(self):
        messagebox.showinfo(f"About {self.APP_NAME}",
            f"{self.APP_NAME} — Linux Edition\n\n"
            "Notepad-style text editor · Python 3 + Tkinter · Zero dependencies\n"
            "Inspired by PlummersSoftwareLLC/TinyRetroPad (x86 ASM, ~2.5 KB)",
            parent=self.root)

    def _bind_shortcuts(self):
        b = self.root.bind
        b("<Control-n>", lambda e: self._new())
        b("<Control-o>", lambda e: self._open())
        b("<Control-s>", lambda e: self._save())
        b("<Control-S>", lambda e: self._save_as())
        b("<Control-z>", lambda e: self._undo())
        b("<Control-a>", lambda e: self._select_all())
        b("<Control-f>", lambda e: self._find_dialog())
        b("<Control-h>", lambda e: self._replace_dialog())
        b("<Control-g>", lambda e: self._goto_dialog())
        b("<F3>",        lambda e: self._find_next())
        b("<F5>",        lambda e: self._insert_datetime())

    def _on_close(self):
        if self._ask_save_if_dirty():
            self.root.destroy()


def main():
    root = tk.Tk()
    root.geometry("900x640")
    root.minsize(400, 300)
    app = TinyRetroPad(root)
    if len(sys.argv) > 1 and os.path.isfile(sys.argv[1]):
        app.current_file = sys.argv[1]
        try:
            with open(sys.argv[1], "r", encoding="utf-8", errors="replace") as f:
                app.text.insert("1.0", f.read())
            app.text.edit_reset()
            app._set_title()
        except OSError: pass
    root.mainloop()

if __name__ == "__main__":
    main()
