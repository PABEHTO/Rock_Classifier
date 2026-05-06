from __future__ import annotations

import tkinter as tk

from rock_classifier.models import ClassificationResult
from rock_classifier.ui import theme
from rock_classifier.ui.widgets import FlatButton, SectionCard, create_label


class ClassificationResultDialog(tk.Toplevel):
    def __init__(self, app: tk.Tk, result: ClassificationResult) -> None:
        super().__init__(app)
        self.title('Результат классификации')
        self.geometry('840x620')
        self.configure(bg=theme.BG)
        self.transient(app)
        self.grab_set()

        card = SectionCard(self, 'Окно «Результат классификации вида породы»')
        card.pack(fill='both', expand=True, padx=16, pady=16)

        has_positive_result = bool(result.matched_rocks or result.ml_prediction)
        banner_bg = theme.SUCCESS if has_positive_result else theme.ACCENT_LIGHT
        banner = tk.Frame(card, bg=banner_bg, bd=1, relief='solid')
        banner.pack(fill='x', padx=12, pady=12)
        create_label(banner, result.headline, bg=banner_bg, font=theme.FONT_SUBTITLE, wraplength=740).pack(anchor='w', padx=10, pady=(10, 4))
        create_label(banner, result.explanation, bg=banner_bg, justify='left', wraplength=740).pack(anchor='w', padx=10, pady=(0, 10))

        body = tk.Text(card, font=theme.FONT, bg=theme.WHITE, relief='solid', bd=1)
        body.pack(fill='both', expand=True, padx=12, pady=(0, 12))
        body.insert('1.0', 'Введённые данные:\n\n')
        for key, value in result.inputs.items():
            body.insert(tk.END, f'• {key}: {value or "—"}\n')

        if result.matched_rocks:
            body.insert(tk.END, '\nПодходящие виды пород по экспертным правилам:\n')
            for rock in result.matched_rocks:
                body.insert(tk.END, f'• {rock}\n')

        if result.ml_used and result.ml_prediction:
            body.insert(tk.END, f'\nОтвет ML-модели: {result.ml_prediction}\n')

        if result.ml_used and result.ml_scores:
            visible_scores = [
                (rock, score)
                for rock, score in result.ml_scores
                if round(score * 100, 2) > 0
            ]
            if visible_scores:
                body.insert(tk.END, '\nОценки ML-модели:\n')
                for rock, score in visible_scores:
                    body.insert(tk.END, f'• {rock}: {score * 100:.2f}%\n')

        if result.rejected_reasons:
            body.insert(tk.END, '\nДругие виды пород опровергнуты по следующим причинам:\n')
            for rock, reason in result.rejected_reasons:
                body.insert(tk.END, f'• Вид породы «{rock}» опровергнут, так как {reason}\n')

        body.configure(state='disabled')

        button_row = tk.Frame(card, bg=theme.PANEL)
        button_row.pack(fill='x', padx=12, pady=(0, 12))
        FlatButton(button_row, 'Закрыть', command=self.destroy, width=12).pack(side='right')
