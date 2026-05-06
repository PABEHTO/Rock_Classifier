from __future__ import annotations

from pathlib import Path

from rock_classifier.models import (
    AppState,
    ClassificationResult,
    normalize_text,
    parse_enum_values,
    parse_number_range,
)
from .ml_service import MlRockClassifier


class ClassifierService:
    """Решатель задачи классификации по правилам и отдельный ML-классификатор."""

    def __init__(self, state: AppState, model_path: str | Path | None = None) -> None:
        self.state = state
        self.model_path = Path(model_path) if model_path else Path(__file__).resolve().parents[2] / 'models' / 'rock_classifier_mlp.joblib'
        self.ml_classifier = MlRockClassifier(self.model_path)

    def reload_model(self) -> None:
        self.ml_classifier = MlRockClassifier(self.model_path)

    def feature_row_from_inputs(self, inputs: dict[str, str]) -> dict[str, object]:
        """Готовит строку признаков для ML по актуальным свойствам базы знаний.

        Раньше ML получал только четыре фиксированных поля. Теперь список полей
        берётся из состояния приложения, поэтому после добавления нового свойства
        и переобучения модели оно участвует и в обучении, и в прогнозе.
        """
        feature_row: dict[str, object] = {}
        for definition in self.state.properties:
            property_name = definition.name
            raw_value = inputs.get(property_name, '').strip()
            if definition.kind == 'number':
                feature_row[property_name] = float(raw_value.replace(',', '.')) if raw_value else None
            else:
                feature_row[property_name] = raw_value or None
        return feature_row

    def _validate_input_value(self, property_name: str, raw_value: str) -> str | None:
        definition = self.state.get_property(property_name)
        value = raw_value.strip()
        if not value:
            return None

        if definition.kind == 'enum':
            allowed = {normalize_text(item) for item in definition.enum_values}
            if normalize_text(value) not in allowed:
                return f'Значение «{value}» для свойства «{property_name}» отсутствует среди возможных значений.'
            return None

        try:
            numeric_value = float(value.replace(',', '.'))
        except ValueError:
            return f'Для свойства «{property_name}» нужно ввести число.'

        start, end = parse_number_range('-'.join(definition.number_range))
        if not (start <= numeric_value <= end):
            return (
                f'Значение «{value}» для свойства «{property_name}» выходит за пределы допустимого диапазона '
                f'{definition.number_range[0]}–{definition.number_range[1]}.'
            )
        return None

    def _validate_inputs(self, normalized_inputs: dict[str, str]) -> list[str]:
        provided = {key: value for key, value in normalized_inputs.items() if value}
        return [
            error for property_name, value in provided.items() if (error := self._validate_input_value(property_name, value))
        ]

    def _match_rock(self, rock_name: str, inputs: dict[str, str]) -> str | None:
        selected_properties = self.state.selected_properties_for_rock(rock_name)
        for property_name, raw_value in inputs.items():
            value = raw_value.strip()
            if not value:
                continue
            if property_name not in selected_properties:
                return (
                    f'вид породы «{rock_name}» опровергнут, так как свойство «{property_name}» '
                    f'не входит в описание этого вида породы.'
                )

            definition = self.state.get_property(property_name)
            expected_text = self.state.get_rock_value(rock_name, property_name)
            if definition.kind == 'enum':
                allowed_values = parse_enum_values(expected_text)
                if normalize_text(value) not in {normalize_text(item) for item in allowed_values}:
                    expected = ', '.join(allowed_values) if allowed_values else 'не задано'
                    return (
                        f'значение «{value}» свойства «{property_name}» не соответствует описанию вида породы '
                        f'(ожидается: {expected}).'
                    )
            else:
                numeric_value = float(value.replace(',', '.'))
                start, end = parse_number_range(expected_text)
                if not (start <= numeric_value <= end):
                    return (
                        f'значение «{value}» свойства «{property_name}» не соответствует описанию вида породы '
                        f'(допустимо: {start:.2f}–{end:.2f}).'
                    )
        return None

    def _expert_filter(self, inputs: dict[str, str]) -> tuple[list[str], list[tuple[str, str]]]:
        matched: list[str] = []
        rejected: list[tuple[str, str]] = []
        for rock in self.state.rocks:
            reason = self._match_rock(rock, inputs)
            if reason is None:
                matched.append(rock)
            else:
                rejected.append((rock, reason))
        return matched, rejected

    def classify(self, inputs: dict[str, str]) -> ClassificationResult:
        """Классификация только по экспертным правилам, без автоматического запуска ML."""
        normalized_inputs = {key: value.strip() for key, value in inputs.items()}
        provided = {key: value for key, value in normalized_inputs.items() if value}

        if not provided:
            return ClassificationResult(
                headline='Вид породы пока не определён.',
                explanation='Введите хотя бы одно значение свойства, затем нажмите кнопку «Определить вид породы».',
                inputs=normalized_inputs,
            )

        validation_errors = self._validate_inputs(normalized_inputs)
        if validation_errors:
            return ClassificationResult(
                headline='Входные данные содержат ошибки.',
                explanation='\n'.join(f'• {item}' for item in validation_errors),
                inputs=normalized_inputs,
            )

        matched, rejected = self._expert_filter(provided)

        if not matched:
            return ClassificationResult(
                headline='Вид породы не определён.',
                explanation=(
                    'Знания об этом виде горных пород не занесены в систему. '
                    'Обратитесь к эксперту для разрешения проблемы.'
                ),
                inputs=normalized_inputs,
                matched_rocks=[],
                rejected_reasons=rejected,
            )

        if len(matched) == 1:
            return ClassificationResult(
                headline=f'Подходящие виды пород: «{matched[0]}».',
                explanation='Другие виды пород опровергнуты по указанным ниже причинам.',
                inputs=normalized_inputs,
                matched_rocks=matched,
                rejected_reasons=rejected,
            )

        return ClassificationResult(
            headline=f'Подходящие виды пород: {", ".join(f"«{item}»" for item in matched)}.',
            explanation=(
                'По правилам найдено несколько подходящих видов пород. '
                'Для выбора с точки зрения ML нажмите отдельную кнопку «Спросить ML-модель».'
            ),
            inputs=normalized_inputs,
            matched_rocks=matched,
            rejected_reasons=rejected,
        )

    def classify_with_ml(self, inputs: dict[str, str]) -> ClassificationResult:
        """Отдельный запрос к ML-модели по текущим введённым признакам."""
        normalized_inputs = {key: value.strip() for key, value in inputs.items()}
        provided = {key: value for key, value in normalized_inputs.items() if value}

        if not provided:
            return ClassificationResult(
                headline='ML-модель не получила данные для классификации.',
                explanation='Введите хотя бы одно значение свойства, затем нажмите кнопку «Спросить ML-модель».',
                inputs=normalized_inputs,
            )

        validation_errors = self._validate_inputs(normalized_inputs)
        if validation_errors:
            return ClassificationResult(
                headline='Входные данные содержат ошибки.',
                explanation='\n'.join(f'• {item}' for item in validation_errors),
                inputs=normalized_inputs,
            )

        if not self.ml_classifier.is_ready:
            return ClassificationResult(
                headline='ML-модель недоступна.',
                explanation=self.ml_classifier.error_message or 'Файл модели не загружен. Вернитесь в окно выбора режима и нажмите «Переобучить модель».',
                inputs=normalized_inputs,
            )

        try:
            predicted_label, top_scores = self.ml_classifier.predict(
                self.feature_row_from_inputs(normalized_inputs),
                allowed_labels=None,
                top_n=5,
            )
            return ClassificationResult(
                headline=f'ML-модель считает, что это «{predicted_label}».',
                explanation=(
                    'Это отдельная классификация с точки зрения ML-модели. '
                    'Она не заменяет результат экспертного решателя и доступна независимо от того, '
                    'однозначно ли сработали правила.'
                ),
                inputs=normalized_inputs,
                matched_rocks=[],
                rejected_reasons=[],
                ml_used=True,
                ml_prediction=predicted_label,
                ml_scores=top_scores,
            )
        except Exception as exc:
            return ClassificationResult(
                headline='ML-модель не смогла выполнить классификацию.',
                explanation=str(exc),
                inputs=normalized_inputs,
            )
