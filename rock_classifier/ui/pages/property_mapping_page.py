from __future__ import annotations

import tkinter as tk

from rock_classifier.ui import theme
from rock_classifier.ui.widgets import FlatButton, ScrollableFrame, SectionCard, create_label
from .base import BaseEditorPage


class PropertyMappingPage(BaseEditorPage):
    def __init__(self, parent: tk.Misc, app: 'RockClassifierApp') -> None:
        super().__init__(parent, app, 'Окно «Описание свойств вида»', 'Слева выбирается порода, справа отмечаются свойства флажками.')
        self.selected_rock = tk.StringVar(value=app.state.rocks[0])
        self.property_vars: dict[str, tk.BooleanVar] = {}
        self._build()
        self.refresh()

    def _build(self) -> None:
        left = SectionCard(self.body, 'Виды пород')
        left.pack(side='left', fill='both', expand=False, padx=(0, 6))
        right = SectionCard(self.body, 'Список свойств')
        right.pack(side='left', fill='both', expand=True, padx=(6, 0))

        listbox_frame = tk.Frame(left, bg=theme.PANEL)
        listbox_frame.pack(fill='both', expand=True, padx=12, pady=12)
        self.rock_listbox = tk.Listbox(
            listbox_frame,
            font=theme.FONT,
            bg=theme.WHITE,
            relief='solid',
            bd=1,
            activestyle='none',
            exportselection=False,
            width=28,
            height=22,
        )
        self.rock_listbox.pack(fill='both', expand=True)
        self.rock_listbox.bind('<<ListboxSelect>>', self.on_select_rock)

        controls = tk.Frame(right, bg=theme.PANEL)
        controls.pack(fill='x', padx=12, pady=12)
        create_label(controls, 'Выбранная порода:', bg=theme.PANEL).pack(side='left')
        create_label(controls, textvariable=self.selected_rock, bg=theme.PANEL, font=theme.FONT_SUBTITLE).pack(side='left', padx=(8, 0))
        FlatButton(controls, 'Выбрать все', command=self.select_all, width=14).pack(side='right')

        self.check_container = ScrollableFrame(right, theme.PANEL)
        self.check_container.pack(fill='both', expand=True, padx=12, pady=(0, 12))

    def refresh(self) -> None:
        self.rock_listbox.delete(0, tk.END)
        for rock in self.app.state.rocks:
            self.rock_listbox.insert(tk.END, rock)
        if self.app.state.rocks:
            try:
                current_index = self.app.state.rocks.index(self.selected_rock.get())
            except ValueError:
                current_index = 0
                self.selected_rock.set(self.app.state.rocks[0])
            self.rock_listbox.selection_clear(0, tk.END)
            self.rock_listbox.selection_set(current_index)
            self.rock_listbox.see(current_index)
        self.refresh_checkboxes()

    def on_select_rock(self, _event=None) -> None:
        selection = self.rock_listbox.curselection()
        if not selection:
            return
        self.selected_rock.set(self.rock_listbox.get(selection[0]))
        self.refresh_checkboxes()

    def select_all(self) -> None:
        for var in self.property_vars.values():
            var.set(True)
        self.save_selection()

    def refresh_checkboxes(self) -> None:
        for child in self.check_container.inner.winfo_children():
            child.destroy()
        self.property_vars.clear()

        selected_properties = set(self.app.state.property_selection_by_rock.get(self.selected_rock.get(), []))
        for prop in self.app.state.property_names():
            row = tk.Frame(self.check_container.inner, bg=theme.LIST_BG, bd=1, relief='solid')
            row.pack(fill='x', pady=4)
            var = tk.BooleanVar(value=prop in selected_properties)
            self.property_vars[prop] = var
            tk.Checkbutton(row, text=prop, variable=var, bg=theme.LIST_BG, font=theme.FONT, command=self.save_selection).pack(anchor='w', padx=10, pady=8)

    def save_selection(self) -> None:
        selected = [name for name, var in self.property_vars.items() if var.get()]
        self.app.editor_service.set_selected_properties_for_rock(self.selected_rock.get(), selected)
