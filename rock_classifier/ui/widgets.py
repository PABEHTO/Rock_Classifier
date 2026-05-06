from __future__ import annotations

import tkinter as tk

from . import theme


def create_label(parent: tk.Misc, text: str = '', *, font=None, fg=None, bg=None, anchor='w', **kwargs) -> tk.Label:
    return tk.Label(
        parent,
        text=text,
        font=font or theme.FONT,
        fg=fg or theme.TEXT,
        bg=bg or parent.cget('bg'),
        anchor=anchor,
        **kwargs,
    )


class FlatButton(tk.Button):
    def __init__(self, parent: tk.Misc, text: str, command=None, kind: str = 'accent', **kwargs):
        color_map = {
            'accent': (theme.ACCENT, theme.TEXT),
            'secondary': (theme.PANEL, theme.TEXT),
            'danger': (theme.DANGER, theme.TEXT),
            'success': (theme.SUCCESS, theme.TEXT),
        }
        bg, fg = color_map.get(kind, color_map['accent'])
        super().__init__(
            parent,
            text=text,
            command=command,
            bg=bg,
            fg=fg,
            activebackground=bg,
            activeforeground=fg,
            relief='solid',
            bd=1,
            highlightthickness=0,
            cursor='hand2',
            font=theme.FONT_BUTTON,
            padx=10,
            pady=6,
            **kwargs,
        )


class SectionCard(tk.Frame):
    def __init__(self, parent: tk.Misc, title: str, subtitle: str | None = None, **kwargs):
        super().__init__(parent, bg=theme.PANEL, bd=1, relief='solid', **kwargs)
        header = tk.Frame(self, bg=theme.PANEL)
        header.pack(fill='x', padx=14, pady=(12, 6))
        create_label(header, title, font=theme.FONT_SECTION).pack(anchor='w')
        if subtitle:
            create_label(header, subtitle, font=theme.FONT_SMALL, fg=theme.MUTED).pack(anchor='w', pady=(3, 0))


class ScrollableFrame(tk.Frame):
    def __init__(self, parent: tk.Misc, bg: str):
        super().__init__(parent, bg=bg)
        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0)
        self.scrollbar = tk.Scrollbar(self, orient='vertical', command=self.canvas.yview)
        self.inner = tk.Frame(self.canvas, bg=bg)

        self.inner.bind('<Configure>', lambda _event: self.canvas.configure(scrollregion=self.canvas.bbox('all')))
        self.window_id = self.canvas.create_window((0, 0), window=self.inner, anchor='nw')
        self.canvas.bind('<Configure>', lambda event: self.canvas.itemconfigure(self.window_id, width=event.width))

        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side='left', fill='both', expand=True)
        self.scrollbar.pack(side='right', fill='y')
