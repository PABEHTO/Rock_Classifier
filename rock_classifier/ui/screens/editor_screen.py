from __future__ import annotations

import tkinter as tk

from rock_classifier.ui import theme
from rock_classifier.ui.pages import (
    AllowedValuesPage,
    CompletenessPage,
    PropertiesPage,
    PropertyMappingPage,
    RockValuesPage,
    RocksPage,
)
from rock_classifier.ui.widgets import FlatButton, create_label


class EditorScreen(tk.Frame):
    PAGES = [
        ('Виды пород', 'rocks'),
        ('Свойства', 'properties'),
        ('Возможные значения', 'allowed'),
        ('Описание свойств вида', 'mapping'),
        ('Значения для вида', 'rock_values'),
        ('Проверка полноты знаний', 'check'),
    ]

    def __init__(self, parent: tk.Misc, app: 'RockClassifierApp') -> None:
        super().__init__(parent, bg=theme.BG)
        self.app = app
        self.current_page = tk.StringVar(value='rocks')
        self.nav_buttons: dict[str, tk.Button] = {}
        self.pages: dict[str, tk.Frame] = {}
        self.page_components: dict[str, object] = {}
        self._build()

    def _build(self) -> None:
        sidebar = tk.Frame(self, bg=theme.PANEL, bd=1, relief='solid')
        sidebar.pack(side='left', fill='y', padx=(0, 12))
        create_label(sidebar, 'Редактор базы знаний', font=theme.FONT_SECTION, bg=theme.PANEL).pack(anchor='w', padx=14, pady=(14, 6))
        create_label(
            sidebar,
            'Навигация по окнам, описанным в курсовой работе.',
            font=theme.FONT_SMALL,
            fg=theme.MUTED,
            bg=theme.PANEL,
            wraplength=220,
            justify='left',
        ).pack(anchor='w', padx=14, pady=(0, 14))

        for label, key in self.PAGES:
            button = FlatButton(sidebar, label, command=lambda page_key=key: self.show_page(page_key), width=24, anchor='w')
            button.pack(fill='x', padx=12, pady=4)
            self.nav_buttons[key] = button

        FlatButton(sidebar, 'Открыть ввод данных', command=lambda: self.app.show_mode('specialist'), kind='secondary', width=24, anchor='w').pack(fill='x', padx=12, pady=(18, 4))

        right = tk.Frame(self, bg=theme.BG)
        right.pack(side='left', fill='both', expand=True)

        for key in dict(self.PAGES).values():
            page = tk.Frame(right, bg=theme.BG)
            page.place(relx=0, rely=0, relwidth=1, relheight=1)
            self.pages[key] = page

        self.page_components['rocks'] = RocksPage(self.pages['rocks'], self.app)
        self.page_components['properties'] = PropertiesPage(self.pages['properties'], self.app)
        self.page_components['allowed'] = AllowedValuesPage(self.pages['allowed'], self.app)
        self.page_components['mapping'] = PropertyMappingPage(self.pages['mapping'], self.app)
        self.page_components['rock_values'] = RockValuesPage(self.pages['rock_values'], self.app)
        self.page_components['check'] = CompletenessPage(self.pages['check'], self.app)

        for component in self.page_components.values():
            component.pack(fill='both', expand=True)

        self.show_page('rocks')

    def show_page(self, key: str) -> None:
        self.current_page.set(key)
        self.pages[key].lift()
        for page_key, button in self.nav_buttons.items():
            button.configure(bg=theme.ACCENT if page_key == key else theme.PANEL)

    def refresh(self) -> None:
        for component in self.page_components.values():
            refresh_method = getattr(component, 'refresh', None)
            if callable(refresh_method):
                refresh_method()
