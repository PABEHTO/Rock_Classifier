from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from rock_classifier.ui import theme
from rock_classifier.ui.dialogs import ClassificationResultDialog, KnowledgeBaseDialog
from rock_classifier.ui.widgets import FlatButton, SectionCard, create_label


class SpecialistScreen(tk.Frame):
    def __init__(self, parent: tk.Misc, app: 'RockClassifierApp') -> None:
        super().__init__(parent, bg=theme.BG)
        self.app = app
        self.value_controls: dict[str, tuple[str, tk.Widget | tk.Misc]] = {}
        self.model_status_label: tk.Label | None = None
        self._build()
        self.refresh()

    def _build(self) -> None:
        left = tk.Frame(self, bg=theme.BG)
        left.pack(side='left', fill='both', expand=True, padx=(0, 6))
        right = tk.Frame(self, bg=theme.BG)
        right.pack(side='left', fill='both', expand=True, padx=(6, 0))

        intro = SectionCard(left, 'Окно «Ввод исходных данных»', 'Введите известные значения свойств образца и выберите способ классификации.')
        intro.pack(fill='x', pady=(0, 12))
        buttons = tk.Frame(intro, bg=theme.PANEL)
        buttons.pack(fill='x', padx=12, pady=(0, 12))
        FlatButton(buttons, 'Главное меню', command=self.app.show_mode_selection, kind='secondary', width=18).pack(side='left')
        FlatButton(buttons, 'Редактор базы знаний', command=lambda: self.app.show_mode('expert'), kind='secondary', width=20).pack(side='left', padx=8)
        FlatButton(buttons, 'Посмотреть базу знаний', command=self.open_knowledge_base, width=22).pack(side='left')

        input_card = SectionCard(left, 'Значения свойств')
        input_card.pack(fill='both', expand=True)
        self.form = tk.Frame(input_card, bg=theme.PANEL)
        self.form.pack(fill='both', expand=True, padx=12, pady=12)

        action_row = tk.Frame(left, bg=theme.BG)
        action_row.pack(fill='x', pady=(12, 0))
        FlatButton(action_row, 'Определить вид породы', command=self.open_result_dialog, width=22).pack(side='left')
        FlatButton(action_row, 'Спросить ML-модель', command=self.open_ml_result_dialog, kind='success', width=20).pack(side='left', padx=8)
        FlatButton(action_row, 'Очистить поля', command=self.clear_inputs, kind='secondary', width=16).pack(side='left')

        help_card = SectionCard(right, 'Подсистема вывода результата и объяснений')
        help_card.pack(fill='x', pady=(0, 12))
        self.model_status_label = create_label(help_card, '', bg=theme.PANEL, justify='left', wraplength=460)
        self.model_status_label.pack(anchor='w', padx=12, pady=(0, 12))
        create_label(
            help_card,
            'Кнопка «Определить вид породы» запускает только экспертный решатель. '
            'Кнопка «Спросить ML-модель» отдельно запрашивает прогноз модели.',
            font=theme.FONT_SMALL,
            fg=theme.MUTED,
            bg=theme.PANEL,
            justify='left',
            wraplength=460,
        ).pack(anchor='w', padx=12, pady=(0, 12))

        summary_card = SectionCard(right, 'Текущие введённые данные')
        summary_card.pack(fill='both', expand=True)
        self.summary_text = tk.Text(summary_card, font=theme.FONT_MONO, bg=theme.WHITE, relief='solid', bd=1, height=16)
        self.summary_text.pack(fill='both', expand=True, padx=12, pady=(0, 12))
        self.summary_text.configure(state='disabled')

    def refresh(self) -> None:
        self.refresh_property_controls()
        self.refresh_model_status()

    def refresh_model_status(self) -> None:
        if self.model_status_label is None:
            return
        if self.app.model_training:
            text = 'ML-модель переобучается на текущей базе знаний...'
        elif self.app.classifier_service.ml_classifier.is_ready:
            text = 'ML-модель загружена. Её можно запросить отдельной кнопкой независимо от результата экспертных правил.'
        else:
            text = 'ML-модель не загружена. Экспертный решатель продолжает работать по правилам опровержения гипотез.'
        self.model_status_label.configure(text=text)

    def set_training_state(self, _is_training: bool, status_text: str | None = None) -> None:
        if self.model_status_label is not None and status_text is not None:
            self.model_status_label.configure(text=status_text)
        elif self.model_status_label is not None:
            self.refresh_model_status()

    def refresh_property_controls(self) -> None:
        for child in self.form.winfo_children():
            child.destroy()
        self.value_controls.clear()

        for row_index, definition in enumerate(self.app.state.properties):
            property_name = definition.name
            create_label(self.form, property_name, bg=theme.PANEL).grid(row=row_index, column=0, sticky='w', pady=8)
            variable = self.app.get_input_var(property_name)

            if definition.kind == 'number':
                entry = tk.Entry(self.form, textvariable=variable, font=theme.FONT, relief='solid', bd=1)
                entry.grid(row=row_index, column=1, sticky='ew', pady=8, ipady=5)
                entry.bind('<KeyRelease>', lambda _event: self.refresh_summary())
                self.value_controls[property_name] = ('number', entry)
            else:
                combo = ttk.Combobox(
                    self.form,
                    values=definition.enum_values,
                    textvariable=variable,
                    state='readonly',
                    style='Rock.TCombobox',
                )
                combo.grid(row=row_index, column=1, sticky='ew', pady=8)
                combo.bind('<<ComboboxSelected>>', lambda _event: self.refresh_summary())
                self.value_controls[property_name] = ('enum', combo)

        self.form.columnconfigure(1, weight=1)
        self.refresh_summary()

    def refresh_summary(self) -> None:
        lines = ['Вводимые свойства:\n']
        for property_name in self.app.state.property_names():
            value = self.app.get_input_var(property_name).get().strip() or '—'
            lines.append(f'{property_name:20} : {value}')
        self.summary_text.configure(state='normal')
        self.summary_text.delete('1.0', tk.END)
        self.summary_text.insert('1.0', '\n'.join(lines))
        self.summary_text.configure(state='disabled')

    def clear_inputs(self) -> None:
        for property_name in self.app.state.property_names():
            self.app.get_input_var(property_name).set('')
        self.refresh_summary()

    def collect_inputs(self) -> dict[str, str]:
        return {name: self.app.get_input_var(name).get().strip() for name in self.app.state.property_names()}

    def open_result_dialog(self) -> None:
        result = self.app.classifier_service.classify(self.collect_inputs())
        ClassificationResultDialog(self.app, result)

    def open_ml_result_dialog(self) -> None:
        result = self.app.classifier_service.classify_with_ml(self.collect_inputs())
        ClassificationResultDialog(self.app, result)

    def open_knowledge_base(self) -> None:
        KnowledgeBaseDialog(self.app, self.app.state)
