"""
СекретПост — GUI-приложение
Шифрование AES-256-GCM. Работает на macOS и Windows.
"""

import tkinter as tk
import threading

from crypto_core import encrypt, decrypt, validate_code


# ─── Палитра ──────────────────────────────────────────────────────────────────
BG         = "#0d0f14"
BG2        = "#141720"
BG3        = "#1c2030"
BORDER     = "#2a3050"
ACCENT     = "#00e5ff"
ACCENT2    = "#7c4dff"
SUCCESS    = "#00e676"
ERROR      = "#ff5252"
TEXT       = "#cdd6f4"
TEXT_DIM   = "#6c7086"

FLAG_WHITE = "#FFFFFF"
FLAG_BLUE  = "#0039A6"
FLAG_RED   = "#D52B1E"
GOLD       = "#FFD700"

FONT_MONO  = ("Courier New", 11)
FONT_LABEL = ("Courier New", 9)
FONT_TITLE = ("Courier New", 19, "bold")
FONT_SUB   = ("Courier New", 9)
FONT_BTN   = ("Courier New", 10, "bold")


class RussianFlag(tk.Canvas):
    """Флаг РФ с двуглавым орлом."""

    def __init__(self, parent, width=72, height=48, **kwargs):
        super().__init__(parent, width=width, height=height,
                         bg=BG, highlightthickness=0, **kwargs)
        self.w = width
        self.h = height
        self._draw()

    def _draw(self):
        w, h = self.w, self.h
        s = h // 3
        self.create_rectangle(0,     0, w, s,     fill=FLAG_WHITE, outline="")
        self.create_rectangle(0,     s, w, s * 2, fill=FLAG_BLUE,  outline="")
        self.create_rectangle(0, s * 2, w, h,     fill=FLAG_RED,   outline="")
        self.create_rectangle(0, 0, w - 1, h - 1, outline="#444", width=1)
        self._draw_eagle(w // 2, h // 2 - 1)

    def _draw_eagle(self, cx, cy):
        g = GOLD
        # Тело
        self.create_oval(cx - 6, cy - 4, cx + 6, cy + 7, fill=g, outline="")
        # Левое крыло
        self.create_polygon([cx-6,cy, cx-18,cy-8, cx-20,cy-2, cx-14,cy+4, cx-6,cy+3],
                            fill=g, outline="")
        # Правое крыло
        self.create_polygon([cx+6,cy, cx+18,cy-8, cx+20,cy-2, cx+14,cy+4, cx+6,cy+3],
                            fill=g, outline="")
        # Хвост
        self.create_polygon([cx-5,cy+7, cx,cy+13, cx+5,cy+7], fill=g, outline="")
        # Левая голова
        self.create_oval(cx-11, cy-13, cx-2, cy-5, fill=g, outline="")
        self.create_polygon([cx-10,cy-9, cx-14,cy-7, cx-10,cy-6], fill=FLAG_RED, outline="")
        # Левая корона
        self.create_polygon([cx-10,cy-14, cx-8,cy-17, cx-6,cy-14, cx-5,cy-17, cx-3,cy-14],
                            fill=g, outline="")
        # Правая голова
        self.create_oval(cx+2, cy-13, cx+11, cy-5, fill=g, outline="")
        self.create_polygon([cx+10,cy-9, cx+14,cy-7, cx+10,cy-6], fill=FLAG_RED, outline="")
        # Правая корона
        self.create_polygon([cx+3,cy-14, cx+5,cy-17, cx+7,cy-14, cx+8,cy-17, cx+10,cy-14],
                            fill=g, outline="")
        # Щит
        self.create_polygon([cx-4,cy-4, cx+4,cy-4, cx+5,cy+3, cx,cy+6, cx-5,cy+3],
                            fill=FLAG_RED, outline=g, width=1)
        # Скипетр и держава
        self.create_line(cx-16, cy+2, cx-12, cy-2, fill=g, width=2)
        self.create_oval(cx-14, cy-5, cx-10, cy-1, fill=g, outline="")
        self.create_line(cx+12, cy+2, cx+16, cy-2, fill=g, width=2)
        self.create_oval(cx+10, cy-5, cx+14, cy-1, fill=g, outline="")


class AnimatedButton(tk.Canvas):
    def __init__(self, parent, text, command, color=ACCENT, width=200, **kwargs):
        super().__init__(parent, width=width, height=42,
                         bg=BG, highlightthickness=0, **kwargs)
        self.command = command
        self.color   = color
        self.text    = text
        self._draw(False)
        self.bind("<Enter>",    lambda e: (self._draw(True),  self.config(cursor="hand2")))
        self.bind("<Leave>",    lambda e: (self._draw(False), self.config(cursor="")))
        self.bind("<Button-1>", lambda e: command() if command else None)

    def _draw(self, hover):
        self.delete("all")
        w    = int(self.cget("width"))
        fill = self.color if hover else BG3
        tc   = BG if hover else self.color
        self.create_rectangle(1, 1, w - 1, 41, outline=self.color, fill=fill, width=2)
        self.create_text(w // 2, 21, text=self.text, font=FONT_BTN, fill=tc)


class StatusBar(tk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=BG, **kwargs)
        self._lbl = tk.Label(self, text="● Готово", font=FONT_LABEL,
                             bg=BG, fg=TEXT_DIM, anchor="w")
        self._lbl.pack(side="left", padx=16)

    def set(self, msg, color=TEXT_DIM):
        self._lbl.config(text=msg, fg=color)
        self.after(4000, lambda: self._lbl.config(text="● Готово", fg=TEXT_DIM))


class CodeEntry(tk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=BG2, **kwargs)
        self._vars, self._entries = [], []
        for i in range(10):
            v = tk.StringVar()
            v.trace_add("write", lambda *a, idx=i: self._on_change(idx))
            e = tk.Entry(self, textvariable=v, width=2,
                         font=("Courier New", 18, "bold"),
                         bg=BG3, fg=ACCENT, insertbackground=ACCENT,
                         relief="flat", justify="center",
                         highlightthickness=2,
                         highlightbackground=BORDER,
                         highlightcolor=ACCENT)
            e.grid(row=0, column=i, padx=3, pady=8)
            e.bind("<BackSpace>", lambda ev, idx=i: self._on_back(idx))
            e.bind("<KeyPress>",  lambda ev, idx=i: self._on_keypress(ev, idx))
            self._vars.append(v)
            self._entries.append(e)

    def _on_change(self, idx):
        val = self._vars[idx].get()
        if len(val) > 1:
            self._vars[idx].set(val[-1]); val = val[-1]
        if val and not val.isdigit():
            self._vars[idx].set(""); return
        if val and idx < 9:
            self._entries[idx + 1].focus_set()

    def _on_back(self, idx):
        if not self._vars[idx].get() and idx > 0:
            self._entries[idx - 1].focus_set()
            self._vars[idx - 1].set("")

    def _on_keypress(self, ev, idx):
        if ev.keysym in ("Tab", "Return"): return
        if self._vars[idx].get() and ev.char.isdigit():
            self._vars[idx].set(ev.char)
            if idx < 9: self._entries[idx + 1].focus_set()
            return "break"

    def get(self):   return "".join(v.get() for v in self._vars)
    def clear(self):
        for v in self._vars: v.set("")
        self._entries[0].focus_set()

    def set_highlight(self, ok):
        c = SUCCESS if ok else ERROR
        for e in self._entries:
            e.config(highlightcolor=c, highlightbackground=c if ok else BORDER)


class SecretPostApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("СекретПост")
        self.configure(bg=BG)
        self.resizable(False, False)
        self._build_ui()
        self._center_window()
        self.after(200, self._typewriter)

    def _center_window(self):
        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"+{(sw-w)//2}+{(sh-h)//2}")

    def _build_ui(self):
        # ── Шапка ─────────────────────────────────────────────────────────────
        header = tk.Frame(self, bg=BG, pady=18)
        header.pack(fill="x")

        RussianFlag(header, width=72, height=48).pack(side="left", padx=(24, 0))

        center = tk.Frame(header, bg=BG)
        center.pack(side="left", expand=True)
        self._title_var = tk.StringVar(value="")
        tk.Label(center, textvariable=self._title_var,
                 font=FONT_TITLE, bg=BG, fg=ACCENT).pack()
        tk.Label(center, text="защищённая переписка · AES-256-GCM",
                 font=FONT_SUB, bg=BG, fg=TEXT_DIM).pack(pady=(3, 0))

        RussianFlag(header, width=72, height=48).pack(side="right", padx=(0, 24))

        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=20)

        # ── Режим ─────────────────────────────────────────────────────────────
        mode_frame = tk.Frame(self, bg=BG2, pady=12)
        mode_frame.pack(fill="x", padx=20, pady=(14, 0))

        tk.Label(mode_frame, text="РЕЖИМ", font=("Courier New", 8, "bold"),
                 bg=BG2, fg=TEXT_DIM).pack(side="left", padx=(16, 10))

        self._mode = tk.StringVar(value="encrypt")
        for val, label in [("encrypt", "⬡  ЗАШИФРОВАТЬ"), ("decrypt", "⬡  РАСШИФРОВАТЬ")]:
            rb = tk.Radiobutton(mode_frame, text=label, variable=self._mode,
                                value=val, command=self._on_mode_change,
                                font=("Courier New", 10, "bold"),
                                bg=BG2, fg=TEXT_DIM, selectcolor=BG2,
                                activebackground=BG2, activeforeground=ACCENT,
                                indicatoron=False, relief="flat",
                                padx=14, pady=6, highlightthickness=0)
            rb.pack(side="left", padx=4)

        self._mode.trace_add("write", self._update_mode_btns)
        self._rb_list = [w for w in mode_frame.winfo_children()
                         if isinstance(w, tk.Radiobutton)]
        self._update_mode_btns()

        # ── Ключ ──────────────────────────────────────────────────────────────
        key_frame = tk.Frame(self, bg=BG2, padx=16, pady=10,
                             highlightthickness=1, highlightbackground=BORDER)
        key_frame.pack(fill="x", padx=20, pady=(12, 0))
        tk.Label(key_frame, text="СЕКРЕТНЫЙ КЛЮЧ  (10 цифр)",
                 font=("Courier New", 8, "bold"), bg=BG2, fg=TEXT_DIM).pack(anchor="w")
        self._code_entry = CodeEntry(key_frame)
        self._code_entry.pack(anchor="w", pady=(2, 0))

        # ── Сообщение ─────────────────────────────────────────────────────────
        msg_frame = tk.Frame(self, bg=BG2, padx=16, pady=10,
                             highlightthickness=1, highlightbackground=BORDER)
        msg_frame.pack(fill="x", padx=20, pady=(10, 0))
        self._msg_label = tk.Label(msg_frame, text="ИСХОДНОЕ СООБЩЕНИЕ",
                                   font=("Courier New", 8, "bold"), bg=BG2, fg=TEXT_DIM)
        self._msg_label.pack(anchor="w")
        self._msg_text = tk.Text(msg_frame, height=6, font=FONT_MONO,
                                 bg=BG3, fg=TEXT, insertbackground=ACCENT,
                                 relief="flat", padx=10, pady=8,
                                 wrap="word", bd=0,
                                 highlightthickness=1,
                                 highlightbackground=BORDER,
                                 highlightcolor=ACCENT)
        self._msg_text.pack(fill="x", pady=(6, 0))
        # Явный биндинг вставки для Mac (Cmd+V) и Windows (Ctrl+V)
        self._msg_text.bind("<Command-v>", self._paste_to_msg)
        self._msg_text.bind("<Control-v>", self._paste_to_msg)
        # Контекстное меню по правой кнопке мыши
        self._msg_text.bind("<Button-2>", self._show_context_menu)
        self._msg_text.bind("<Button-3>", self._show_context_menu)

        # ── Кнопки ────────────────────────────────────────────────────────────
        btn_frame = tk.Frame(self, bg=BG, pady=14)
        btn_frame.pack()
        self._run_btn = AnimatedButton(btn_frame, "▶  ЗАШИФРОВАТЬ",
                                       self._run, ACCENT, 210)
        self._run_btn.pack(side="left", padx=8)
        AnimatedButton(btn_frame, "✕  ОЧИСТИТЬ",
                       self._clear, TEXT_DIM, 140).pack(side="left", padx=8)

        # ── Результат ─────────────────────────────────────────────────────────
        res_frame = tk.Frame(self, bg=BG2, padx=16, pady=10,
                             highlightthickness=1, highlightbackground=BORDER)
        res_frame.pack(fill="x", padx=20, pady=(0, 14))

        res_hdr = tk.Frame(res_frame, bg=BG2)
        res_hdr.pack(fill="x")
        self._res_label = tk.Label(res_hdr, text="РЕЗУЛЬТАТ",
                                   font=("Courier New", 8, "bold"), bg=BG2, fg=TEXT_DIM)
        self._res_label.pack(side="left")
        copy_lbl = tk.Label(res_hdr, text="[ КОПИРОВАТЬ ]",
                            font=("Courier New", 8, "bold"), bg=BG2, fg=ACCENT2,
                            cursor="hand2")
        copy_lbl.pack(side="right")
        copy_lbl.bind("<Button-1>", self._copy_result)

        self._result_text = tk.Text(res_frame, height=5, font=FONT_MONO,
                                    bg=BG3, fg=SUCCESS,
                                    relief="flat", padx=10, pady=8,
                                    wrap="word", bd=0,
                                    highlightthickness=1,
                                    highlightbackground=BORDER,
                                    state="disabled")
        self._result_text.pack(fill="x", pady=(6, 0))

        # ── Статус ────────────────────────────────────────────────────────────
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=20)
        self._status = StatusBar(self)
        self._status.pack(fill="x", pady=6)

    def _update_mode_btns(self, *_):
        mode = self._mode.get()
        for rb in self._rb_list:
            rb.config(fg=ACCENT if rb.cget("value") == mode else TEXT_DIM)

    def _on_mode_change(self):
        mode = self._mode.get()
        if mode == "encrypt":
            self._msg_label.config(text="ИСХОДНОЕ СООБЩЕНИЕ")
            self._res_label.config(text="РЕЗУЛЬТАТ  (зашифровано)")
            self._run_btn.text  = "▶  ЗАШИФРОВАТЬ"
            self._run_btn.color = ACCENT
            self._result_text.config(fg=SUCCESS)
        else:
            self._msg_label.config(text="ЗАШИФРОВАННОЕ СООБЩЕНИЕ  (вставьте сюда)")
            self._res_label.config(text="РЕЗУЛЬТАТ  (расшифровано)")
            self._run_btn.text  = "▶  РАСШИФРОВАТЬ"
            self._run_btn.color = ACCENT2
            self._result_text.config(fg=ACCENT)
        self._run_btn._draw(False)
        self._clear_result()

    def _run(self):
        code = self._code_entry.get()
        if not validate_code(code):
            self._code_entry.set_highlight(False)
            self._status.set("✖  Ключ должен содержать ровно 10 цифр", ERROR)
            return
        self._code_entry.set_highlight(True)
        message = self._msg_text.get("1.0", "end-1c").strip()
        if not message:
            self._status.set("✖  Введите сообщение", ERROR)
            return
        self._status.set("⏳  Обработка…", TEXT_DIM)
        threading.Thread(target=self._run_crypto, args=(code, message), daemon=True).start()

    def _run_crypto(self, code, message):
        try:
            if self._mode.get() == "encrypt":
                result = encrypt(message, code)
                label, color = "✔  Сообщение зашифровано", SUCCESS
            else:
                result = decrypt(message, code)
                label, color = "✔  Сообщение расшифровано", SUCCESS
        except ValueError as e:
            self.after(0, lambda: self._status.set(f"✖  {e}", ERROR))
            return
        self.after(0, lambda: self._set_result(result, label, color))

    def _set_result(self, text, msg, color):
        self._result_text.config(state="normal")
        self._result_text.delete("1.0", "end")
        self._result_text.insert("1.0", text)
        self._result_text.config(state="disabled")
        self._status.set(msg, color)

    def _clear_result(self):
        self._result_text.config(state="normal")
        self._result_text.delete("1.0", "end")
        self._result_text.config(state="disabled")

    def _clear(self):
        self._msg_text.delete("1.0", "end")
        self._clear_result()
        self._code_entry.clear()
        self._status.set("● Очищено", TEXT_DIM)

    def _paste_to_msg(self, event=None):
        """Явная вставка из буфера — решает проблему с Cmd+V на Mac."""
        try:
            text = self.clipboard_get()
            self._msg_text.insert(tk.INSERT, text)
        except tk.TclError:
            pass
        return "break"  # предотвращаем двойную вставку

    def _show_context_menu(self, event):
        """Контекстное меню по правой кнопке мыши."""
        menu = tk.Menu(self, tearoff=0, bg=BG3, fg=TEXT,
                       activebackground=ACCENT, activeforeground=BG,
                       font=("Courier New", 10))
        menu.add_command(label="Вставить", command=lambda: self._paste_to_msg())
        menu.add_command(label="Копировать",
                         command=lambda: self.event_generate("<<Copy>>"))
        menu.add_separator()
        menu.add_command(label="Выделить всё",
                         command=lambda: self._msg_text.tag_add("sel", "1.0", "end"))
        menu.add_separator()
        menu.add_command(label="Очистить поле",
                         command=lambda: self._msg_text.delete("1.0", "end"))
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def _copy_result(self, _=None):
        text = self._result_text.get("1.0", "end-1c").strip()
        if not text:
            self._status.set("✖  Нечего копировать", TEXT_DIM)
            return
        # Используем системный буфер — Tkinter теряет данные при потере фокуса
        import sys, subprocess
        try:
            if sys.platform == "darwin":
                # Mac: pbcopy — надёжный системный буфер
                proc = subprocess.Popen("pbcopy", stdin=subprocess.PIPE)
                proc.communicate(text.encode("utf-8"))
            elif sys.platform == "win32":
                # Windows: clip
                proc = subprocess.Popen("clip", stdin=subprocess.PIPE, shell=True)
                proc.communicate(text.encode("utf-16"))
            else:
                # Linux fallback
                self.clipboard_clear()
                self.clipboard_append(text)
                self.update()
            self._status.set("✔  Скопировано! Вставляй в письмо (Cmd+V)", SUCCESS)
        except Exception as e:
            # Если системный буфер недоступен — пробуем Tkinter
            self.clipboard_clear()
            self.clipboard_append(text)
            self.update()
            self._status.set("✔  Скопировано в буфер обмена", SUCCESS)

    def _typewriter(self):
        full = "СекретПост"
        cur  = self._title_var.get().replace("█", "")
        if len(cur) < len(full):
            self._title_var.set(full[:len(cur) + 1] + "█")
            self.after(90, self._typewriter)
        else:
            self._title_var.set(full)


if __name__ == "__main__":
    SecretPostApp().mainloop()
