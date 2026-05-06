from __future__ import annotations

import tkinter as tk

from rock_classifier.ui import theme
from rock_classifier.ui.widgets import FlatButton, SectionCard, create_label
from .base import BaseEditorPage


class CompletenessPage(BaseEditorPage):
    def __init__(self, parent: tk.Misc, app: 'RockClassifierApp') -> None:
        super().__init__(parent, app, 'Окно «Проверка полноты знаний»', 'Проверка заполненности и целостности базы знаний.')
        self._build()
        self.refresh()

    def _build(self) -> None:
        top = tk.Frame(self.body, bg=theme.BG)
        top.pack(fill='x')
        FlatButton(top, 'Запустить проверку', command=self.run_check, width=18).pack(anchor='w')

        card = SectionCard(self.body, 'Обнаруженные проблемы')
        card.pack(fill='both', expand=True, pady=(12, 0))
        warn = tk.Frame(card, bg=theme.ACCENT_LIGHT, bd=1, relief='solid')
        warn.pack(fill='x', padx=12, pady=12)
        create_label(
            warn,
            'Если список пуст, база знаний заполнена корректно и соответствует текущим ограничениям целостности.',
            bg=theme.ACCENT_LIGHT,
            wraplength=980,
            justify='left',
        ).pack(anchor='w', padx=10, pady=10)

        self.listbox = tk.Listbox(card, font=theme.FONT, bg=theme.WHITE, relief='solid', bd=1, activestyle='none')
        self.listbox.pack(fill='both', expand=True, padx=12, pady=(0, 12))
        self.listbox.bind('<Double-Button-1>', self.open_issue)

    def refresh(self) -> None:
        self.listbox.delete(0, tk.END)
        if not self.app.state.completeness_errors:
            self.listbox.insert(tk.END, 'Ошибок не обнаружено.')
            return
        for item in self.app.state.completeness_errors:
            self.listbox.insert(tk.END, item)

    def run_check(self) -> None:
        self.app.state.completeness_errors = self.app.editor_service.run_completeness_check()
        self.refresh()
        if self.app.state.completeness_errors:
            self.app.show_validation_warning('Проверка завершена: найдены незаполненные или некорректные элементы базы знаний.')
        else:
            self.app.show_stub('Проверка полноты', 'Проверка завершена: база знаний заполнена корректно.')

    def open_issue(self, _event=None) -> None:
        selection = self.listbox.curselection()
        if selection:
            self.app.show_stub('Выбранная проблема', self.listbox.get(selection[0]))
