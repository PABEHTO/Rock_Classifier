from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from rock_classifier.ui import theme
from rock_classifier.ui.widgets import FlatButton, ScrollableFrame, SectionCard, create_label
from .base import BaseEditorPage


class AllowedValuesPage(BaseEditorPage):
    def __init__(self, parent: tk.Misc, app: 'RockClassifierApp') -> None:
        super().__init__(
            parent,
            app,
            'Окно «Возможные значения»',
            'Добавление числовых диапазонов и перечислимых значений для каждого свойства.',
        )
        self.selected_property = tk.StringVar(value=app.state.property_names()[0])
        self.value_type = tk.StringVar(value='enum')
        self.number_from = tk.StringVar(value='1.00')
        self.number_to = tk.StringVar(value='4.00')
        self.integer_only = tk.BooleanVar(value=False)
        self.enum_value = tk.StringVar(value='')
        self._build()
        self.refresh()

    def _build(self) -> None:
        left = SectionCard(self.body, 'Параметры свойства')
        left.pack(side='left', fill='both', expand=True, padx=(0, 6))
        right = SectionCard(self.body, 'Уже заданные значения')
        right.pack(side='left', fill='both', expand=True, padx=(6, 0))

        form = tk.Frame(left, bg=theme.PANEL)
        form.pack(fill='x', padx=12, pady=12)

        create_label(form, 'Свойство', bg=theme.PANEL).grid(row=0, column=0, sticky='w', pady=4)
        self.property_box = ttk.Combobox(
            form,
            values=self.app.state.property_names(),
            textvariable=self.selected_property,
            state='readonly',
            style='Rock.TCombobox',
            width=34,
        )
        self.property_box.grid(row=0, column=1, sticky='ew', pady=4)
        self.property_box.bind('<<ComboboxSelected>>', lambda _event: self.refresh())

        create_label(form, 'Тип значений', bg=theme.PANEL).grid(row=1, column=0, sticky='w', pady=4)
        radio_row = tk.Frame(form, bg=theme.PANEL)
        radio_row.grid(row=1, column=1, sticky='w')
        tk.Radiobutton(radio_row, text='Числовой', variable=self.value_type, value='number', bg=theme.PANEL, font=theme.FONT_SMALL, command=self.switch_to_number).pack(side='left', padx=(0, 10))
        tk.Radiobutton(radio_row, text='Перечислимый', variable=self.value_type, value='enum', bg=theme.PANEL, font=theme.FONT_SMALL, command=self.switch_to_enum).pack(side='left')

        self.number_frame = tk.Frame(left, bg=theme.PANEL)
        create_label(self.number_frame, 'От', bg=theme.PANEL).grid(row=0, column=0, sticky='w', pady=4)
        tk.Entry(self.number_frame, textvariable=self.number_from, font=theme.FONT, relief='solid', bd=1).grid(row=0, column=1, sticky='ew', pady=4, padx=(8, 12), ipady=5)
        create_label(self.number_frame, 'До', bg=theme.PANEL).grid(row=0, column=2, sticky='w', pady=4)
        tk.Entry(self.number_frame, textvariable=self.number_to, font=theme.FONT, relief='solid', bd=1).grid(row=0, column=3, sticky='ew', pady=4, padx=(8, 0), ipady=5)
        tk.Checkbutton(self.number_frame, text='Только целые', variable=self.integer_only, bg=theme.PANEL, font=theme.FONT_SMALL).grid(row=1, column=0, columnspan=4, sticky='w', pady=(6, 0))
        FlatButton(self.number_frame, 'Сохранить диапазон', command=self.add_number_value, width=18).grid(row=2, column=0, columnspan=4, sticky='w', pady=(10, 0))
        self.number_frame.columnconfigure(1, weight=1)
        self.number_frame.columnconfigure(3, weight=1)

        self.enum_frame = tk.Frame(left, bg=theme.PANEL)
        create_label(self.enum_frame, 'Название значения', bg=theme.PANEL).pack(anchor='w', pady=(0, 4))
        tk.Entry(self.enum_frame, textvariable=self.enum_value, font=theme.FONT, relief='solid', bd=1).pack(fill='x', ipady=5)
        FlatButton(self.enum_frame, 'Добавить значение', command=self.add_enum_value, width=18).pack(anchor='w', pady=(10, 0))

        self.values_area = ScrollableFrame(right, theme.PANEL)
        self.values_area.pack(fill='both', expand=True, padx=12, pady=(0, 12))

    def switch_to_number(self) -> None:
        self.value_type.set('number')
        self._update_editor_visibility()

    def switch_to_enum(self) -> None:
        self.value_type.set('enum')
        self._update_editor_visibility()

    def _update_editor_visibility(self) -> None:
        if self.value_type.get() == 'number':
            self.number_frame.pack(fill='x', padx=12, pady=(0, 10))
            self.enum_frame.pack_forget()
        else:
            self.number_frame.pack_forget()
            self.enum_frame.pack(fill='x', padx=12, pady=(0, 12))

    def refresh(self) -> None:
        property_names = self.app.state.property_names()
        self.property_box.configure(values=property_names)
        if property_names and self.selected_property.get() not in property_names:
            self.selected_property.set(property_names[0])

        current = self.app.state.get_property(self.selected_property.get())
        self.value_type.set(current.kind)

        if current.kind == 'number':
            self.number_from.set(current.number_range[0])
            self.number_to.set(current.number_range[1])
            self.integer_only.set(current.integer_only)

        self._update_editor_visibility()

        for child in self.values_area.inner.winfo_children():
            child.destroy()

        if current.kind == 'number':
            row = tk.Frame(self.values_area.inner, bg=theme.LIST_BG, bd=1, relief='solid')
            row.pack(fill='x', pady=4)
            create_label(row, f'Диапазон: {current.display_allowed_values()}', bg=theme.LIST_BG).pack(side='left', padx=10, pady=10)
            FlatButton(row, 'Удалить', command=self.delete_number_value, kind='danger', width=12).pack(side='right', padx=8, pady=6)
        else:
            for item in current.enum_values:
                row = tk.Frame(self.values_area.inner, bg=theme.LIST_BG, bd=1, relief='solid')
                row.pack(fill='x', pady=4)
                create_label(row, item, bg=theme.LIST_BG).pack(side='left', padx=10, pady=10)
                FlatButton(row, 'Удалить', command=lambda value=item: self.delete_enum_value(value), kind='danger', width=12).pack(side='right', padx=8, pady=6)

    def add_number_value(self) -> None:
        try:
            self.app.editor_service.set_property_as_number(
                self.selected_property.get(),
                self.number_from.get(),
                self.number_to.get(),
                self.integer_only.get(),
            )
        except ValueError as exc:
            self.app.show_validation_warning(str(exc))
            return
        self.app.refresh_all_screens()

    def delete_number_value(self) -> None:
        self.app.editor_service.clear_number_range(self.selected_property.get())
        self.app.refresh_all_screens()

    def add_enum_value(self) -> None:
        created = self.app.editor_service.add_enum_value(self.selected_property.get(), self.enum_value.get())
        if not created:
            self.app.show_validation_warning('Значение не может быть пустым или уже существует.')
            return
        self.enum_value.set('')
        self.app.refresh_all_screens()

    def delete_enum_value(self, value: str) -> None:
        self.app.editor_service.delete_enum_value(self.selected_property.get(), value)
        self.app.refresh_all_screens()
