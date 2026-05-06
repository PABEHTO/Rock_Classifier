from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

PropertyKind = Literal['enum', 'number']


@dataclass(slots=True)
class PropertyDefinition:
    name: str
    kind: PropertyKind
    enum_values: list[str] = field(default_factory=list)
    number_range: tuple[str, str] = ('', '')
    integer_only: bool = False

    def copy(self) -> 'PropertyDefinition':
        return PropertyDefinition(
            name=self.name,
            kind=self.kind,
            enum_values=self.enum_values[:],
            number_range=tuple(self.number_range),
            integer_only=self.integer_only,
        )

    def display_allowed_values(self) -> str:
        if self.kind == 'number':
            start, end = self.number_range
            suffix = ' (целые)' if self.integer_only else ''
            return f'{start} – {end}{suffix}' if start or end else f'—{suffix}'
        return ', '.join(self.enum_values) if self.enum_values else '—'


@dataclass(slots=True)
class ClassificationResult:
    headline: str
    explanation: str
    inputs: dict[str, str]
    matched_rocks: list[str] = field(default_factory=list)
    rejected_reasons: list[tuple[str, str]] = field(default_factory=list)
    ml_used: bool = False
    ml_prediction: str | None = None
    ml_scores: list[tuple[str, float]] = field(default_factory=list)


@dataclass(slots=True)
class AppState:
    rocks: list[str]
    properties: list[PropertyDefinition]
    property_selection_by_rock: dict[str, list[str]]
    rock_property_values: dict[str, dict[str, str]]
    completeness_errors: list[str]
    input_values: dict[str, str] = field(default_factory=dict)

    def property_names(self) -> list[str]:
        return [prop.name for prop in self.properties]

    def get_property(self, name: str) -> PropertyDefinition:
        for prop in self.properties:
            if prop.name == name:
                return prop
        raise KeyError(name)

    def has_property(self, name: str) -> bool:
        return any(prop.name == name for prop in self.properties)

    def add_property_definition(self, definition: PropertyDefinition) -> None:
        self.properties.append(definition)
        for rock in self.rocks:
            self.property_selection_by_rock.setdefault(rock, []).append(definition.name)
            self.rock_property_values.setdefault(rock, {}).setdefault(definition.name, '')
        self.input_values.setdefault(definition.name, '')

    def remove_property_definition(self, property_name: str) -> None:
        self.properties = [prop for prop in self.properties if prop.name != property_name]
        for rock in self.rocks:
            self.property_selection_by_rock.setdefault(rock, [])
            self.property_selection_by_rock[rock] = [name for name in self.property_selection_by_rock[rock] if name != property_name]
            self.rock_property_values.setdefault(rock, {}).pop(property_name, None)
        self.input_values.pop(property_name, None)

    def add_rock(self, rock_name: str) -> None:
        self.rocks.append(rock_name)
        property_names = self.property_names()
        self.property_selection_by_rock.setdefault(rock_name, property_names[:])
        self.rock_property_values.setdefault(rock_name, {property_name: '' for property_name in property_names})

    def remove_rock(self, rock_name: str) -> None:
        self.rocks = [rock for rock in self.rocks if rock != rock_name]
        self.property_selection_by_rock.pop(rock_name, None)
        self.rock_property_values.pop(rock_name, None)

    def selected_properties_for_rock(self, rock_name: str) -> list[str]:
        return self.property_selection_by_rock.get(rock_name, [])[:]

    def set_selected_properties_for_rock(self, rock_name: str, property_names: list[str]) -> None:
        self.property_selection_by_rock[rock_name] = property_names[:]

    def get_rock_value(self, rock_name: str, property_name: str) -> str:
        return self.rock_property_values.get(rock_name, {}).get(property_name, '')

    def set_rock_value(self, rock_name: str, property_name: str, value: str) -> None:
        self.rock_property_values.setdefault(rock_name, {})[property_name] = value


ROCKS = [
    'Гранит',
    'Базальт',
    'Андезит',
    'Диорит',
    'Песчаник',
    'Известняк',
    'Конгломерат',
    'Глинистый сланец',
    'Мрамор',
    'Кварцит',
    'Габбро',
    'Риолит',
    'Туф',
    'Доломит',
    'Обсидиан',
    'Серпентинит',
    'Кремень',
    'Гнейс',
    'Аргиллит',
    'Дунит',
]


PROPERTY_DEFINITIONS = [
    PropertyDefinition(
        name='Происхождение',
        kind='enum',
        enum_values=['Магматическая', 'Осадочная', 'Метаморфическая'],
    ),
    PropertyDefinition(
        name='Структура',
        kind='enum',
        enum_values=['Кристаллическая', 'Аморфная', 'Слоистая', 'Зернистая'],
    ),
    PropertyDefinition(
        name='Минеральный состав',
        kind='enum',
        enum_values=['Кварцевый', 'Полевошпатовый', 'Карбонатный', 'Глинистый', 'Обсидиановый'],
    ),
    PropertyDefinition(
        name='Плотность',
        kind='number',
        number_range=('1.00', '4.00'),
        integer_only=False,
    ),
]


ROCK_KNOWLEDGE = {
    'Гранит': {'Происхождение': 'Магматическая', 'Структура': 'Кристаллическая', 'Минеральный состав': 'Полевошпатовый', 'Плотность': '2.60–2.75'},
    'Базальт': {'Происхождение': 'Магматическая', 'Структура': 'Кристаллическая', 'Минеральный состав': 'Полевошпатовый', 'Плотность': '2.80–3.00'},
    'Андезит': {'Происхождение': 'Магматическая', 'Структура': 'Кристаллическая', 'Минеральный состав': 'Полевошпатовый', 'Плотность': '2.40–2.80'},
    'Диорит': {'Происхождение': 'Магматическая', 'Структура': 'Кристаллическая', 'Минеральный состав': 'Полевошпатовый', 'Плотность': '2.80–2.85'},
    'Песчаник': {'Происхождение': 'Осадочная', 'Структура': 'Зернистая', 'Минеральный состав': 'Кварцевый', 'Плотность': '2.20–2.60'},
    'Известняк': {'Происхождение': 'Осадочная', 'Структура': 'Слоистая', 'Минеральный состав': 'Карбонатный', 'Плотность': '2.60–2.75'},
    'Конгломерат': {'Происхождение': 'Осадочная', 'Структура': 'Зернистая', 'Минеральный состав': 'Кварцевый', 'Плотность': '2.20–2.50'},
    'Глинистый сланец': {'Происхождение': 'Осадочная', 'Структура': 'Слоистая', 'Минеральный состав': 'Глинистый', 'Плотность': '2.40–2.80'},
    'Мрамор': {'Происхождение': 'Метаморфическая', 'Структура': 'Кристаллическая', 'Минеральный состав': 'Карбонатный', 'Плотность': '2.40–2.70'},
    'Кварцит': {'Происхождение': 'Метаморфическая', 'Структура': 'Кристаллическая', 'Минеральный состав': 'Кварцевый', 'Плотность': '2.60–2.70'},
    'Габбро': {'Происхождение': 'Магматическая', 'Структура': 'Кристаллическая', 'Минеральный состав': 'Полевошпатовый', 'Плотность': '2.70–3.30'},
    'Риолит': {'Происхождение': 'Магматическая', 'Структура': 'Кристаллическая', 'Минеральный состав': 'Полевошпатовый', 'Плотность': '2.50–2.55'},
    'Туф': {'Происхождение': 'Осадочная', 'Структура': 'Зернистая', 'Минеральный состав': 'Полевошпатовый', 'Плотность': '1.80–2.60'},
    'Доломит': {'Происхождение': 'Осадочная', 'Структура': 'Кристаллическая', 'Минеральный состав': 'Карбонатный', 'Плотность': '2.80–2.90'},
    'Обсидиан': {'Происхождение': 'Магматическая', 'Структура': 'Аморфная', 'Минеральный состав': 'Обсидиановый', 'Плотность': '2.30–2.60'},
    'Серпентинит': {'Происхождение': 'Метаморфическая', 'Структура': 'Кристаллическая', 'Минеральный состав': 'Глинистый', 'Плотность': '2.55–2.75'},
    'Кремень': {'Происхождение': 'Осадочная', 'Структура': 'Аморфная', 'Минеральный состав': 'Кварцевый', 'Плотность': '2.55–2.65'},
    'Гнейс': {'Происхождение': 'Метаморфическая', 'Структура': 'Кристаллическая', 'Минеральный состав': 'Полевошпатовый', 'Плотность': '2.60–2.90'},
    'Аргиллит': {'Происхождение': 'Осадочная', 'Структура': 'Слоистая', 'Минеральный состав': 'Глинистый', 'Плотность': '2.60–2.80'},
    'Дунит': {'Происхождение': 'Магматическая', 'Структура': 'Кристаллическая', 'Минеральный состав': 'Полевошпатовый', 'Плотность': '3.10–3.30'},
}


def normalize_text(value: str) -> str:
    return str(value).strip().lower().replace('ё', 'е')


def normalize_range_text(value: str) -> str:
    return str(value).replace('—', '-').replace('–', '-').replace('−', '-').replace(',', '.').replace(' ', '')


def parse_number_range(value: str) -> tuple[float, float]:
    cleaned = normalize_range_text(value)
    if not cleaned:
        raise ValueError('Пустой диапазон.')
    if '-' in cleaned:
        left, right = cleaned.split('-', 1)
        start = float(left)
        end = float(right)
    else:
        start = float(cleaned)
        end = start
    if start > end:
        raise ValueError('Левая граница диапазона больше правой.')
    return start, end


def parse_enum_values(value: str) -> list[str]:
    items = []
    for item in str(value).split(','):
        normalized = item.strip()
        if normalized:
            items.append(normalized)
    return items


def format_number(value: float) -> str:
    return f'{value:.2f}'


def format_range(start: float, end: float) -> str:
    return f'{format_number(start)}–{format_number(end)}'


def create_default_state() -> AppState:
    properties = [definition.copy() for definition in PROPERTY_DEFINITIONS]
    rocks = ROCKS[:]
    property_names = [prop.name for prop in properties]
    return AppState(
        rocks=rocks,
        properties=properties,
        property_selection_by_rock={rock: property_names[:] for rock in rocks},
        rock_property_values={rock: values.copy() for rock, values in ROCK_KNOWLEDGE.items()},
        completeness_errors=[],
        input_values={property_name: '' for property_name in property_names},
    )


# Совместимость с предыдущей версией проекта.
ClassificationPreview = ClassificationResult
create_demo_state = create_default_state
