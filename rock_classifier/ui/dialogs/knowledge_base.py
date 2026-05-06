from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from rock_classifier.models import AppState
from rock_classifier.ui import theme
from rock_classifier.ui.widgets import FlatButton, SectionCard


class KnowledgeBaseDialog(tk.Toplevel):
    def __init__(self, app: tk.Tk, state: AppState) -> None:
        super().__init__(app)
        self.title('База знаний')
        self.geometry('980x560')
        self.configure(bg=theme.BG)
        self.transient(app)
        self.grab_set()

        card = SectionCard(self, 'Окно «База знаний»', 'Просмотр текущей таблицы правил из базы знаний.')
        card.pack(fill='both', expand=True, padx=16, pady=16)

        property_names = state.property_names()
        columns = ('Порода', *property_names)
        tree = ttk.Treeview(card, columns=columns, show='headings', style='Knowledge.Treeview')
        for column in columns:
            tree.heading(column, text=column)
            width = 180 if column == 'Порода' else 150
            tree.column(column, width=width, anchor='w')
        tree.pack(fill='both', expand=True, padx=12, pady=(0, 12))

        for rock in state.rocks:
            values = state.rock_property_values.get(rock, {})
            tree.insert('', 'end', values=(rock, *[values.get(name, '—') for name in property_names]))

        bottom = tk.Frame(card, bg=theme.PANEL)
        bottom.pack(fill='x', padx=12, pady=(0, 12))
        FlatButton(bottom, 'Закрыть', command=self.destroy, width=12).pack(side='right')
