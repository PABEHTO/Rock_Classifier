from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import queue
import threading
import tkinter as tk
from tkinter import messagebox

from rock_classifier.data import build_demo_state
from rock_classifier.services import ClassifierService, EditorService, train_and_save_model
from rock_classifier.ui import theme
from rock_classifier.ui.screens import EditorScreen, SpecialistScreen
from rock_classifier.ui.styles import configure_ttk
from rock_classifier.ui.widgets import FlatButton, SectionCard, create_label


BASE_DIR = Path(__file__).resolve().parents[1]
MODEL_PATH = BASE_DIR / 'models' / 'rock_classifier_mlp.joblib'
EXPERT_CSV_PATH = BASE_DIR / 'models' / 'expert_knowledge_base.csv'
METRICS_PATH = BASE_DIR / 'models' / 'training_metrics.txt'


class ModeSelectionScreen(tk.Frame):
    """Первое окно приложения: главное меню и переобучение модели."""

    def __init__(self, parent: tk.Misc, app: 'RockClassifierApp') -> None:
        super().__init__(parent, bg=theme.BG)
        self.app = app
        self.retrain_button: tk.Button | None = None
        self.model_status_label: tk.Label | None = None
        self._build()
        self.refresh_model_status()

    def _build(self) -> None:
        wrapper = tk.Frame(self, bg=theme.BG)
        wrapper.pack(expand=True)

        card = SectionCard(
            wrapper,
            'Главное меню',
            'Выберите действие: перейти в редактор базы знаний, открыть классификацию пород или переобучить модель.',
        )
        card.pack(fill='both', expand=True, padx=20, pady=20)

        create_label(
            card,
            'Система классификации горных пород',
            font=theme.FONT_TITLE,
            bg=theme.PANEL,
        ).pack(anchor='w', padx=18, pady=(6, 2))
        create_label(
            card,
            'Редактор знаний и классификация разведены по отдельным режимам. '
            'Переобучение ML-модели запускается отсюда, до перехода к вводу исходных данных.',
            font=theme.FONT_SMALL,
            fg=theme.MUTED,
            bg=theme.PANEL,
            justify='left',
            wraplength=720,
        ).pack(anchor='w', padx=18, pady=(0, 18))

        button_row = tk.Frame(card, bg=theme.PANEL)
        button_row.pack(fill='x', padx=18, pady=(0, 18))
        FlatButton(
            button_row,
            'Редактор базы знаний',
            command=lambda: self.app.show_mode('expert'),
            width=26,
        ).pack(side='left', padx=(0, 10), ipady=4)
        FlatButton(
            button_row,
            'Классификация пород',
            command=lambda: self.app.show_mode('specialist'),
            width=24,
        ).pack(side='left', padx=10, ipady=4)
        self.retrain_button = FlatButton(
            button_row,
            'Переобучить модель',
            command=self.app.retrain_model,
            kind='secondary',
            width=22,
        )
        self.retrain_button.pack(side='left', padx=10, ipady=4)

        status_card = SectionCard(card, 'Состояние ML-модели')
        status_card.pack(fill='x', padx=18, pady=(0, 18))
        self.model_status_label = create_label(status_card, '', bg=theme.PANEL, justify='left', wraplength=760)
        self.model_status_label.pack(anchor='w', padx=12, pady=(0, 12))

    def refresh_model_status(self) -> None:
        if self.model_status_label is None:
            return
        if self.app.model_training:
            text = 'ML-модель переобучается на текущей базе знаний...'
        elif self.app.classifier_service.ml_classifier.is_ready:
            text = 'ML-модель загружена. В режиме классификации её можно запросить отдельной кнопкой «Спросить ML-модель».'
        else:
            text = 'ML-модель не загружена. Нажмите «Переобучить модель», чтобы создать файл модели по текущей базе знаний.'
        self.model_status_label.configure(text=text)

    def set_training_state(self, is_training: bool, status_text: str | None = None) -> None:
        if self.retrain_button is not None:
            self.retrain_button.configure(state='disabled' if is_training else 'normal')
        if self.model_status_label is not None:
            if status_text is not None:
                self.model_status_label.configure(text=status_text)
            else:
                self.refresh_model_status()


class RockClassifierApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title('Классификация горных пород')
        self.geometry('1380x840')
        self.minsize(1180, 760)
        self.configure(bg=theme.BG)

        configure_ttk(self)

        self.state = build_demo_state()
        self.editor_service = EditorService(self.state)
        self.classifier_service = ClassifierService(self.state, model_path=MODEL_PATH)
        self.model_training = False
        self.current_mode = tk.StringVar(value='menu')
        self.input_vars: dict[str, tk.StringVar] = {
            property_name: tk.StringVar(value=value)
            for property_name, value in self.state.input_values.items()
        }

        self._build_shell()

    def _build_shell(self) -> None:
        header = tk.Frame(self, bg=theme.PANEL, bd=1, relief='solid')
        header.pack(fill='x', padx=16, pady=(16, 8))
        title_block = tk.Frame(header, bg=theme.PANEL)
        title_block.pack(side='left', fill='y', padx=14, pady=8)
        create_label(title_block, 'Система классификации горных пород', font=theme.FONT_TITLE, bg=theme.PANEL).pack(anchor='w')
        create_label(
            title_block,
            'Главное меню открывает редактор знаний, классификацию пород и переобучение ML-модели.',
            font=theme.FONT_SMALL,
            fg=theme.MUTED,
            bg=theme.PANEL,
        ).pack(anchor='w', pady=(3, 0))

        self.header_actions = tk.Frame(header, bg=theme.PANEL)
        self.header_actions.pack(side='right', padx=14, pady=12)
        self.home_button = FlatButton(
            self.header_actions,
            'Главное меню',
            command=self.show_mode_selection,
            kind='secondary',
            width=18,
        )

        self.content = tk.Frame(self, bg=theme.BG)
        self.content.pack(fill='both', expand=True, padx=16, pady=(0, 16))

        self.mode_selection_screen = ModeSelectionScreen(self.content, self)
        self.editor_screen = EditorScreen(self.content, self)
        self.specialist_screen = SpecialistScreen(self.content, self)

        self.mode_selection_screen.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.editor_screen.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.specialist_screen.place(relx=0, rely=0, relwidth=1, relheight=1)

        self.show_mode_selection()

    def get_input_var(self, property_name: str) -> tk.StringVar:
        if property_name not in self.input_vars:
            self.input_vars[property_name] = tk.StringVar(value='')
        return self.input_vars[property_name]

    def _update_header_actions(self) -> None:
        if self.current_mode.get() == 'menu':
            self.home_button.pack_forget()
        elif not self.home_button.winfo_ismapped():
            self.home_button.pack(side='left')

    def show_mode_selection(self) -> None:
        self.current_mode.set('menu')
        self.mode_selection_screen.refresh_model_status()
        self.mode_selection_screen.lift()
        self._update_header_actions()

    def show_mode(self, mode: str) -> None:
        self.current_mode.set(mode)
        if mode == 'expert':
            self.editor_screen.refresh()
            self.editor_screen.lift()
        else:
            self.specialist_screen.refresh()
            self.specialist_screen.lift()
        self._update_header_actions()

    def refresh_all_screens(self) -> None:
        self.mode_selection_screen.refresh_model_status()
        self.editor_screen.refresh()
        self.specialist_screen.refresh()

    def show_stub(self, title: str, text: str) -> None:
        messagebox.showinfo(title, text, parent=self)

    def show_validation_warning(self, text: str) -> None:
        messagebox.showwarning('Проверка', text, parent=self)

    def set_training_state(self, is_training: bool, status_text: str | None = None) -> None:
        self.mode_selection_screen.set_training_state(is_training, status_text)
        self.specialist_screen.set_training_state(is_training, status_text)

    def retrain_model(self) -> None:
        if self.model_training:
            return

        if not self.state.properties:
            self.show_validation_warning('Переобучение не запущено: в базе знаний нет ни одного свойства.')
            return

        completeness_errors = self.editor_service.run_completeness_check()
        if completeness_errors:
            self.refresh_all_screens()
            self.show_validation_warning(
                'Переобучение не запущено: сначала заполните базу знаний без ошибок. '
                'Список проблем доступен в окне «Проверка полноты знаний».',
            )
            return

        self.model_training = True
        self.set_training_state(True, 'ML-модель переобучается на текущей базе знаний...')
        state_snapshot = deepcopy(self.state)

        result_queue: queue.SimpleQueue[tuple[dict[str, object] | None, Exception | None]] = queue.SimpleQueue()

        def worker() -> None:
            try:
                result = train_and_save_model(
                    state=state_snapshot,
                    model_path=MODEL_PATH,
                    expert_csv_path=EXPERT_CSV_PATH,
                    metrics_path=METRICS_PATH,
                    n_per_class=350,
                    random_state=42,
                )
                result_queue.put((result, None))
            except Exception as exc:  # pragma: no cover - защита от ошибок окружения или данных
                result_queue.put((None, exc))

        def poll_result() -> None:
            try:
                result, error = result_queue.get_nowait()
            except queue.Empty:
                self.after(100, poll_result)
                return
            self._finish_model_retraining(result=result, error=error)

        threading.Thread(target=worker, daemon=True).start()
        self.after(100, poll_result)

    def _finish_model_retraining(self, result: dict[str, object] | None, error: Exception | None) -> None:
        self.model_training = False
        if error is not None:
            self.set_training_state(False)
            messagebox.showerror('Переобучение модели', f'Не удалось переобучить модель:\n{error}', parent=self)
            return

        self.classifier_service.reload_model()
        self.set_training_state(False)
        self.refresh_all_screens()
        accuracy = float(result.get('accuracy', 0.0)) if result else 0.0
        rows = int(result.get('rows', 0)) if result else 0
        features = result.get('features', []) if result else []
        features_count = len(features) if isinstance(features, list) else 0
        messagebox.showinfo(
            'Переобучение модели',
            f'ML-модель успешно переобучена.\nТочность на контрольной выборке: {accuracy:.4f}.\n'
            f'Строк в синтетической выборке: {rows}.\n'
            f'Использовано свойств-признаков: {features_count}.',
            parent=self,
        )


def run_app() -> None:
    app = RockClassifierApp()
    app.mainloop()
