from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from rock_classifier.models import parse_enum_values
from rock_classifier.ui import theme
from rock_classifier.ui.widgets import FlatButton, ScrollableFrame, SectionCard, create_label
from .base import BaseEditorPage


class RockValuesPage(BaseEditorPage):
    def __init__(self, parent: tk.Misc, app: 'RockClassifierApp') -> None:
        super().__init__(parent, app, 'Окно «Значения для вида»', 'Выбор породы, свойства и допустимых значений для конкретного вида.')
        self.selected_rock = tk.StringVar(value=app.state.rocks[0])
        self.selected_property = tk.StringVar(value=app.state.property_names()[0])
        self.num_from = tk.StringVar(value='2.60')
        self.num_to = tk.StringVar(value='2.75')
        self.enum_vars: dict[str, tk.BooleanVar] = {}
        self.save_enum_button: tk.Button | None = None
        self._build()
        self.refresh()

    def _build(self) -> None:
        top = SectionCard(self.body, 'Параметры редактирования')
        top.pack(fill='x', pady=(0, 12))
        form = tk.Frame(top, bg=theme.PANEL)
        form.pack(fill='x', padx=12, pady=12)

        create_label(form, 'Порода', bg=theme.PANEL).grid(row=0, column=0, sticky='w', pady=4)
        self.rock_box = ttk.Combobox(form, values=self.app.state.rocks, textvariable=self.selected_rock, state='readonly', style='Rock.TCombobox', width=30)
        self.rock_box.grid(row=0, column=1, sticky='ew', pady=4, padx=(8, 12))
        create_label(form, 'Свойство', bg=theme.PANEL).grid(row=0, column=2, sticky='w', pady=4)
        self.prop_box = ttk.Combobox(form, values=self.app.state.property_names(), textvariable=self.selected_property, state='readonly', style='Rock.TCombobox', width=30)
        self.prop_box.grid(row=0, column=3, sticky='ew', pady=4, padx=(8, 0))
        self.rock_box.bind('<<ComboboxSelected>>', lambda _event: self.refresh())
        self.prop_box.bind('<<ComboboxSelected>>', lambda _event: self.refresh())
        form.columnconfigure(1, weight=1)
        form.columnconfigure(3, weight=1)

        self.value_card = SectionCard(self.body, 'Редактирование значения')
        self.value_card.pack(fill='both', expand=True)

        self.number_editor = tk.Frame(self.value_card, bg=theme.PANEL)
        create_label(self.number_editor, 'Диапазон от', bg=theme.PANEL).grid(row=0, column=0, sticky='w', pady=4)
        tk.Entry(self.number_editor, textvariable=self.num_from, font=theme.FONT, relief='solid', bd=1).grid(row=0, column=1, sticky='ew', pady=4, padx=(8, 12), ipady=5)
        create_label(self.number_editor, 'до', bg=theme.PANEL).grid(row=0, column=2, sticky='w', pady=4)
        tk.Entry(self.number_editor, textvariable=self.num_to, font=theme.FONT, relief='solid', bd=1).grid(row=0, column=3, sticky='ew', pady=4, padx=(8, 0), ipady=5)
        FlatButton(self.number_editor, 'Сохранить диапазон', command=self.save_number, width=18).grid(row=1, column=0, columnspan=4, sticky='w', pady=(12, 0))
        self.number_editor.columnconfigure(1, weight=1)
        self.number_editor.columnconfigure(3, weight=1)

        self.enum_editor = tk.Frame(self.value_card, bg=theme.PANEL)
        self.enum_holder = ScrollableFrame(self.enum_editor, theme.PANEL)

    def refresh(self) -> None:
        rock_names = self.app.state.rocks
        property_names = self.app.state.selected_properties_for_rock(self.selected_rock.get()) or self.app.state.property_names()
        self.rock_box.configure(values=rock_names)
        self.prop_box.configure(values=property_names)

        if rock_names and self.selected_rock.get() not in rock_names:
            self.selected_rock.set(rock_names[0])
        if property_names and self.selected_property.get() not in property_names:
            self.selected_property.set(property_names[0])

        self.number_editor.pack_forget()
        self.enum_editor.pack_forget()

        definition = self.app.state.get_property(self.selected_property.get())
        current_value = self.app.state.get_rock_value(self.selected_rock.get(), self.selected_property.get())
        if definition.kind == 'number':
            self.number_editor.pack(fill='x', padx=12, pady=12)
            if '–' in current_value:
                left, right = current_value.split('–', 1)
                self.num_from.set(left)
                self.num_to.set(right)
            else:
                self.num_from.set('')
                self.num_to.set('')
        else:
            self.enum_editor.pack(fill='both', expand=True, padx=12, pady=12)
            if self.save_enum_button is not None:
                self.save_enum_button.destroy()
            for child in self.enum_holder.inner.winfo_children():
                child.destroy()
            self.enum_holder.pack(fill='both', expand=True)
            self.enum_vars.clear()
            current_selected = set(parse_enum_values(current_value))
            for value in definition.enum_values:
                row = tk.Frame(self.enum_holder.inner, bg=theme.LIST_BG, bd=1, relief='solid')
                row.pack(fill='x', pady=4)
                var = tk.BooleanVar(value=value in current_selected)
                self.enum_vars[value] = var
                tk.Checkbutton(row, text=value, variable=var, bg=theme.LIST_BG, font=theme.FONT).pack(anchor='w', padx=10, pady=8)
            self.save_enum_button = FlatButton(self.enum_editor, 'Сохранить выбранные значения', command=self.save_enum, width=26)
            self.save_enum_button.pack(anchor='w', pady=(12, 0))

    def save_number(self) -> None:
        try:
            self.app.editor_service.save_rock_number_value(
                self.selected_rock.get(),
                self.selected_property.get(),
                self.num_from.get(),
                self.num_to.get(),
            )
        except ValueError as exc:
            self.app.show_validation_warning(str(exc))
            return
        self.app.refresh_all_screens()

    def save_enum(self) -> None:
        selected = [value for value, var in self.enum_vars.items() if var.get()]
        self.app.editor_service.save_rock_enum_values(
            self.selected_rock.get(),
            self.selected_property.get(),
            selected,
        )
        self.app.refresh_all_screens()
