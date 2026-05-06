from __future__ import annotations

import tkinter as tk

from rock_classifier.ui import theme
from rock_classifier.ui.widgets import FlatButton, ScrollableFrame, SectionCard, create_label


class BaseEditorPage(tk.Frame):
    def __init__(self, parent: tk.Misc, app: 'RockClassifierApp', title: str, subtitle: str) -> None:
        super().__init__(parent, bg=theme.BG)
        self.app = app
        header = SectionCard(self, title, subtitle)
        header.pack(fill='x', pady=(0, 12))
        self.body = tk.Frame(self, bg=theme.BG)
        self.body.pack(fill='both', expand=True)


class EditableListPage(BaseEditorPage):
    def __init__(self, parent: tk.Misc, app: 'RockClassifierApp', title: str, subtitle: str) -> None:
        super().__init__(parent, app, title, subtitle)

        list_card = SectionCard(self.body, 'Список элементов')
        list_card.pack(fill='both', expand=True)

        self.list_area = ScrollableFrame(list_card, theme.PANEL)
        self.list_area.pack(fill='both', expand=True, padx=12, pady=(0, 12))

        bottom = tk.Frame(list_card, bg=theme.PANEL)
        bottom.pack(fill='x', padx=12, pady=(0, 12))
        self.entry = tk.Entry(bottom, font=theme.FONT, relief='solid', bd=1)
        self.entry.pack(side='left', fill='x', expand=True, padx=(0, 8), ipady=6)
        FlatButton(bottom, 'Добавить', command=self.handle_add, width=14).pack(side='left')

    def get_items(self) -> list[str]:
        raise NotImplementedError

    def add_item(self, value: str) -> bool:
        raise NotImplementedError

    def delete_item(self, value: str) -> bool:
        raise NotImplementedError

    def refresh(self) -> None:
        for child in self.list_area.inner.winfo_children():
            child.destroy()

        for index, item in enumerate(self.get_items(), start=1):
            row = tk.Frame(self.list_area.inner, bg=theme.LIST_BG, bd=1, relief='solid')
            row.pack(fill='x', pady=4)
            create_label(row, f'{index}. {item}', bg=theme.LIST_BG).pack(side='left', padx=10, pady=10)
            FlatButton(
                row,
                'Удалить',
                command=lambda value=item: self.handle_delete(value),
                kind='danger',
                width=12,
            ).pack(side='right', padx=8, pady=6)

    def handle_add(self) -> None:
        value = self.entry.get().strip()
        if not value:
            self.app.show_validation_warning('Поле не должно быть пустым.')
            return
        if not self.add_item(value):
            self.app.show_validation_warning('Элемент уже существует или не может быть добавлен.')
            return
        self.entry.delete(0, tk.END)
        self.app.refresh_all_screens()

    def handle_delete(self, value: str) -> None:
        if not self.delete_item(value):
            self.app.show_validation_warning('Не удалось удалить элемент.')
            return
        self.app.refresh_all_screens()
