from __future__ import annotations

from rock_classifier.models import (
    AppState,
    PropertyDefinition,
    format_range,
    normalize_text,
    parse_enum_values,
    parse_number_range,
)


class EditorService:
    """Редактирование базы знаний в памяти приложения."""

    def __init__(self, state: AppState) -> None:
        self.state = state

    def add_rock(self, rock_name: str) -> bool:
        normalized = rock_name.strip()
        if not normalized:
            return False
        existing = {normalize_text(item) for item in self.state.rocks}
        if normalize_text(normalized) in existing:
            return False
        self.state.add_rock(normalized)
        return True

    def delete_rock(self, rock_name: str) -> bool:
        if rock_name not in self.state.rocks:
            return False
        self.state.remove_rock(rock_name)
        return True

    def add_property(self, property_name: str) -> bool:
        normalized = property_name.strip()
        if not normalized or self.state.has_property(normalized):
            return False
        self.state.add_property_definition(PropertyDefinition(name=normalized, kind='enum', enum_values=[]))
        return True

    def delete_property(self, property_name: str) -> bool:
        if not self.state.has_property(property_name):
            return False
        self.state.remove_property_definition(property_name)
        return True

    def set_property_as_number(
        self,
        property_name: str,
        range_start: str,
        range_end: str,
        integer_only: bool,
    ) -> None:
        definition = self.state.get_property(property_name)
        start, end = parse_number_range(f'{range_start}-{range_end}')
        definition.kind = 'number'
        definition.number_range = (f'{start:.2f}', f'{end:.2f}')
        definition.integer_only = integer_only
        definition.enum_values = []

    def clear_number_range(self, property_name: str) -> None:
        definition = self.state.get_property(property_name)
        definition.kind = 'number'
        definition.number_range = ('', '')
        definition.integer_only = False

    def add_enum_value(self, property_name: str, value: str) -> bool:
        normalized = value.strip()
        if not normalized:
            return False
        definition = self.state.get_property(property_name)
        if definition.kind != 'enum':
            definition.kind = 'enum'
            definition.enum_values = []
            definition.number_range = ('', '')
            definition.integer_only = False
        if normalize_text(normalized) in {normalize_text(item) for item in definition.enum_values}:
            return False
        definition.enum_values.append(normalized)
        return True

    def delete_enum_value(self, property_name: str, value: str) -> bool:
        definition = self.state.get_property(property_name)
        before = len(definition.enum_values)
        definition.enum_values = [item for item in definition.enum_values if normalize_text(item) != normalize_text(value)]
        if len(definition.enum_values) == before:
            return False
        for rock in self.state.rocks:
            current_values = parse_enum_values(self.state.get_rock_value(rock, property_name))
            current_values = [item for item in current_values if normalize_text(item) != normalize_text(value)]
            self.state.set_rock_value(rock, property_name, ', '.join(current_values))
        return True

    def set_selected_properties_for_rock(self, rock_name: str, selected_properties: list[str]) -> None:
        self.state.set_selected_properties_for_rock(rock_name, selected_properties)

    def save_rock_number_value(self, rock_name: str, property_name: str, range_start: str, range_end: str) -> None:
        start, end = parse_number_range(f'{range_start}-{range_end}')
        self.state.set_rock_value(rock_name, property_name, format_range(start, end))

    def save_rock_enum_values(self, rock_name: str, property_name: str, selected_values: list[str]) -> None:
        self.state.set_rock_value(rock_name, property_name, ', '.join(selected_values))

    def run_completeness_check(self) -> list[str]:
        errors: list[str] = []

        if not self.state.rocks:
            errors.append('Список видов пород пуст. Перейдите в окно «Виды пород».')
        if not self.state.properties:
            errors.append('Список свойств пуст. Перейдите в окно «Свойства».')

        for definition in self.state.properties:
            if definition.kind == 'enum':
                if not definition.enum_values:
                    errors.append(
                        f'Для свойства «{definition.name}» не заданы возможные значения. Перейдите в окно «Возможные значения».',
                    )
            else:
                start, end = definition.number_range
                if not start or not end:
                    errors.append(
                        f'Для числового свойства «{definition.name}» не задан допустимый диапазон. Перейдите в окно «Возможные значения».',
                    )
                else:
                    try:
                        parse_number_range(f'{start}-{end}')
                    except ValueError:
                        errors.append(
                            f'Для числового свойства «{definition.name}» задан некорректный диапазон возможных значений.',
                        )

        property_names = set(self.state.property_names())
        for rock in self.state.rocks:
            selected_properties = self.state.selected_properties_for_rock(rock)
            if not selected_properties:
                errors.append(
                    f'Для породы «{rock}» описание свойств пусто. Перейдите в окно «Описание свойств вида».',
                )
                continue

            for property_name in selected_properties:
                if property_name not in property_names:
                    errors.append(
                        f'Для породы «{rock}» выбрано неизвестное свойство «{property_name}».',
                    )
                    continue

                definition = self.state.get_property(property_name)
                value_text = self.state.get_rock_value(rock, property_name)
                if not value_text.strip():
                    errors.append(
                        f'Для породы «{rock}» не заполнено значение свойства «{property_name}». Перейдите в окно «Значения для вида».',
                    )
                    continue

                if definition.kind == 'enum':
                    selected_values = parse_enum_values(value_text)
                    if not selected_values:
                        errors.append(
                            f'Для породы «{rock}» свойство «{property_name}» не содержит выбранных перечислимых значений.',
                        )
                        continue
                    allowed = {normalize_text(item) for item in definition.enum_values}
                    for item in selected_values:
                        if normalize_text(item) not in allowed:
                            errors.append(
                                f'Для породы «{rock}» свойство «{property_name}» содержит недопустимое значение «{item}».',
                            )
                else:
                    try:
                        rock_start, rock_end = parse_number_range(value_text)
                        allowed_start, allowed_end = parse_number_range('-'.join(definition.number_range))
                    except ValueError:
                        errors.append(
                            f'Для породы «{rock}» свойство «{property_name}» содержит некорректный числовой диапазон.',
                        )
                        continue
                    if rock_start < allowed_start or rock_end > allowed_end:
                        errors.append(
                            f'Для породы «{rock}» диапазон свойства «{property_name}» выходит за пределы допустимых значений.',
                        )

        self.state.completeness_errors = errors
        return errors
