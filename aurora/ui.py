"""Desktop chat — offline, tkinter only. Aurora speaks from LC files on disk."""

from __future__ import annotations

import tkinter as tk
from tkinter import font as tkfont
from tkinter import messagebox, ttk

from aurora.engine import Aurora

NIGHT = "#070b14"
PANEL = "#10182a"
PANEL_ALT = "#0c1322"
AURORA = "#7ee0d6"
VIOLET = "#c4b0ff"
TEXT = "#e8eefc"
MUTED = "#8b97b3"
USER_BG = "#1a2744"
LINE = "#243049"


class AuroraApp(tk.Tk):
    def __init__(self, aurora: Aurora) -> None:
        super().__init__()
        self.aurora = aurora
        self.title("Аврора · офлайн")
        self.geometry("760x560")
        self.minsize(520, 420)
        self.configure(bg=NIGHT)
        self._busy = False
        self._build_fonts()
        self._build()
        self.after(200, self._hello)

    def _build_fonts(self) -> None:
        family = "Segoe UI"
        available = set(tkfont.families(self))
        if family not in available:
            family = "DejaVu Sans" if "DejaVu Sans" in available else "TkDefaultFont"
        self.font_ui = tkfont.Font(family=family, size=11)
        self.font_title = tkfont.Font(family=family, size=16, weight="bold")
        self.font_small = tkfont.Font(family=family, size=9)
        self.font_mono = tkfont.Font(family="Consolas", size=9)
        if "Consolas" not in available:
            self.font_mono = tkfont.Font(family="TkFixedFont", size=9)

    def _build(self) -> None:
        header = tk.Frame(self, bg=NIGHT)
        header.pack(fill="x", padx=18, pady=(16, 8))

        tk.Label(
            header,
            text="Аврора",
            fg=AURORA,
            bg=NIGHT,
            font=self.font_title,
        ).pack(side="left")
        tk.Label(
            header,
            text="  Аврора  ·  LC  ·  без облака",
            fg=VIOLET,
            bg=NIGHT,
            font=self.font_small,
        ).pack(side="left", pady=(6, 0))

        self.status = tk.Label(
            header,
            text="офлайн · persona + memory · brain/*.avr",
            fg=MUTED,
            bg=NIGHT,
            font=self.font_small,
        )
        self.status.pack(side="right", pady=(6, 0))

        shell = tk.Frame(self, bg=LINE, bd=0)
        shell.pack(fill="both", expand=True, padx=18, pady=(0, 10))
        inner = tk.Frame(shell, bg=PANEL)
        inner.pack(fill="both", expand=True, padx=1, pady=1)

        self.log = tk.Text(
            inner,
            wrap="word",
            bg=PANEL,
            fg=TEXT,
            insertbackground=AURORA,
            relief="flat",
            bd=0,
            padx=14,
            pady=12,
            font=self.font_ui,
            state="disabled",
            highlightthickness=0,
            cursor="arrow",
        )
        scroll = ttk.Scrollbar(inner, command=self.log.yview)
        self.log.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.log.pack(side="left", fill="both", expand=True)

        self.log.tag_configure("who_aurora", foreground=AURORA, font=self.font_small, spacing1=10)
        self.log.tag_configure("who_user", foreground=VIOLET, font=self.font_small, spacing1=10)
        self.log.tag_configure("msg", foreground=TEXT, lmargin1=8, lmargin2=8, spacing3=8)
        self.log.tag_configure("system", foreground=MUTED, font=self.font_small, spacing3=8)

        bottom = tk.Frame(self, bg=NIGHT)
        bottom.pack(fill="x", padx=18, pady=(0, 16))

        entry_shell = tk.Frame(bottom, bg=LINE)
        entry_shell.pack(side="left", fill="x", expand=True)
        self.entry = tk.Text(
            entry_shell,
            height=3,
            wrap="word",
            bg=PANEL_ALT,
            fg=TEXT,
            insertbackground=AURORA,
            relief="flat",
            font=self.font_ui,
            padx=10,
            pady=8,
            highlightthickness=0,
        )
        self.entry.pack(fill="both", expand=True, padx=1, pady=1)
        self.entry.bind("<Return>", self._on_enter)
        self.entry.bind("<Shift-Return>", lambda e: None)
        self.entry.focus_set()

        send = tk.Button(
            bottom,
            text="сказать",
            command=self._send,
            bg="#16302c",
            fg=AURORA,
            activebackground="#1c3d38",
            activeforeground=AURORA,
            relief="flat",
            font=self.font_ui,
            padx=16,
            pady=10,
            cursor="hand2",
        )
        send.pack(side="right", padx=(10, 0), fill="y")

        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Vertical.TScrollbar", background=PANEL, troughcolor=NIGHT, bordercolor=NIGHT)

    def _hello(self) -> None:
        self._append_system(
            "Я на твоём диске. Облачных мозгов нет — только LC, persona и memory. Напиши «привет»."
        )

    def _append_system(self, text: str) -> None:
        self.log.configure(state="normal")
        self.log.insert("end", text + "\n", ("system",))
        self.log.configure(state="disabled")
        self.log.see("end")

    def _append(self, who: str, text: str) -> None:
        tag = "who_aurora" if who == "Аврора" else "who_user"
        self.log.configure(state="normal")
        self.log.insert("end", who + "\n", (tag,))
        self.log.insert("end", text + "\n\n", ("msg",))
        self.log.configure(state="disabled")
        self.log.see("end")

    def _on_enter(self, event: tk.Event) -> str:
        if event.state & 0x1:  # Shift
            return ""
        self._send()
        return "break"

    def _send(self) -> None:
        if self._busy:
            return
        text = self.entry.get("1.0", "end").strip()
        if not text:
            return
        self.entry.delete("1.0", "end")
        self._append("ты", text)
        self._busy = True
        self.status.configure(text="думает на LC…")
        self.update_idletasks()
        try:
            reply = self.aurora.reply(text)
        except Exception as exc:  # noqa: BLE001 — show in UI, keep app alive
            messagebox.showerror("Аврора", str(exc))
            reply = "Что-то сломалось в LC. Это локальная ошибка, не сеть."
        self._append("Аврора", reply)
        self.status.configure(text="офлайн · persona + memory · brain/*.avr")
        self._busy = False


def run_app(aurora: Aurora) -> None:
    app = AuroraApp(aurora)
    app.mainloop()
