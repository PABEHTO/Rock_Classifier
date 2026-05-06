from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from . import theme


def configure_ttk(root: tk.Misc) -> None:
    style = ttk.Style(root)
    try:
        style.theme_use('clam')
    except tk.TclError:
        pass

    style.configure(
        'Rock.TCombobox',
        fieldbackground=theme.WHITE,
        background=theme.WHITE,
        foreground=theme.TEXT,
        borderwidth=1,
        arrowsize=14,
        padding=6,
    )
    style.map(
        'Rock.TCombobox',
        fieldbackground=[('readonly', theme.WHITE)],
        selectbackground=[('readonly', theme.WHITE)],
        selectforeground=[('readonly', theme.TEXT)],
    )

    style.configure(
        'Knowledge.Treeview',
        background=theme.WHITE,
        fieldbackground=theme.WHITE,
        foreground=theme.TEXT,
        bordercolor=theme.BORDER,
        rowheight=28,
        relief='flat',
    )
    style.configure(
        'Knowledge.Treeview.Heading',
        background=theme.ACCENT_LIGHT,
        foreground=theme.TEXT,
        borderwidth=1,
        relief='solid',
        font=theme.FONT_BUTTON,
    )
    style.map('Knowledge.Treeview.Heading', background=[('active', theme.ACCENT)])
