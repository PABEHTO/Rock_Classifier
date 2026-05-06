from __future__ import annotations

from pathlib import Path
import random

import pandas as pd
from joblib import dump
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from rock_classifier.models import AppState, parse_enum_values, parse_number_range


LABEL_COLUMN = 'Вид породы'


def feature_columns_from_state(state: AppState) -> list[str]:
    """Возвращает актуальный список признаков из базы знаний.

    Важно: список признаков больше не фиксированный. Если эксперт добавил новое
    свойство в редакторе базы знаний, то после переобучения оно попадёт и в
    экспертную CSV-таблицу, и в синтетическую обучающую выборку, и в модель.
    """
    return state.property_names()


def split_feature_columns(state: AppState) -> tuple[list[str], list[str]]:
    categorical_features: list[str] = []
    numeric_features: list[str] = []
    for definition in state.properties:
        if definition.kind == 'number':
            numeric_features.append(definition.name)
        else:
            categorical_features.append(definition.name)
    return categorical_features, numeric_features


def build_expert_dataframe(state: AppState) -> pd.DataFrame:
    feature_columns = feature_columns_from_state(state)
    rows: list[dict[str, object]] = []
    for rock in state.rocks:
        selected_properties = state.selected_properties_for_rock(rock)
        row: dict[str, object] = {LABEL_COLUMN: rock}
        for property_name in feature_columns:
            row[property_name] = state.get_rock_value(rock, property_name) if property_name in selected_properties else ''
        rows.append(row)
    return pd.DataFrame(rows, columns=[LABEL_COLUMN, *feature_columns])


def _sample_from_range(range_text: str, rng: random.Random) -> float:
    start, end = parse_number_range(range_text)
    if start == end:
        return round(start, 3)
    return round(rng.uniform(start, end), 3)


def _sample_enum_value(value_text: str, rng: random.Random) -> str:
    values = parse_enum_values(value_text)
    if not values:
        return ''
    return rng.choice(values)


def _sample_property_value(state: AppState, rock: str, property_name: str, rng: random.Random) -> object:
    if property_name not in state.selected_properties_for_rock(rock):
        return ''

    value_text = state.get_rock_value(rock, property_name).strip()
    if not value_text:
        return ''

    definition = state.get_property(property_name)
    if definition.kind == 'number':
        return _sample_from_range(value_text, rng)
    return _sample_enum_value(value_text, rng)


def generate_synthetic_dataset(state: AppState, n_per_class: int = 350, random_state: int = 42) -> pd.DataFrame:
    feature_columns = feature_columns_from_state(state)
    rng = random.Random(random_state)
    rows: list[dict[str, object]] = []
    for rock in state.rocks:
        for _ in range(n_per_class):
            row = {
                property_name: _sample_property_value(state, rock, property_name, rng)
                for property_name in feature_columns
            }
            row[LABEL_COLUMN] = rock
            rows.append(row)
    return pd.DataFrame(rows, columns=[*feature_columns, LABEL_COLUMN])


def build_preprocessing_pipeline(categorical_features: list[str], numeric_features: list[str]) -> ColumnTransformer:
    transformers = []
    if categorical_features:
        transformers.append(
            (
                'cat',
                Pipeline(
                    steps=[
                        ('imputer', SimpleImputer(strategy='most_frequent')),
                        ('encoder', OneHotEncoder(handle_unknown='ignore')),
                    ],
                ),
                categorical_features,
            ),
        )
    if numeric_features:
        transformers.append(
            (
                'num',
                Pipeline(
                    steps=[
                        ('imputer', SimpleImputer(strategy='median')),
                        ('scaler', StandardScaler()),
                    ],
                ),
                numeric_features,
            ),
        )

    if not transformers:
        raise ValueError('Нельзя обучить ML-модель: в базе знаний нет свойств-признаков.')

    return ColumnTransformer(transformers=transformers)


def train_and_save_model(
    state: AppState,
    model_path: str | Path,
    expert_csv_path: str | Path,
    metrics_path: str | Path | None = None,
    n_per_class: int = 350,
    random_state: int = 42,
) -> dict[str, object]:
    model_path = Path(model_path)
    expert_csv_path = Path(expert_csv_path)
    metrics_file = Path(metrics_path) if metrics_path else None
    model_path.parent.mkdir(parents=True, exist_ok=True)
    expert_csv_path.parent.mkdir(parents=True, exist_ok=True)

    feature_columns = feature_columns_from_state(state)
    categorical_features, numeric_features = split_feature_columns(state)
    if not feature_columns:
        raise ValueError('Нельзя обучить ML-модель: список свойств пуст.')

    expert_df = build_expert_dataframe(state)
    expert_df.to_csv(expert_csv_path, index=False, encoding='utf-8-sig')

    dataset = generate_synthetic_dataset(state, n_per_class=n_per_class, random_state=random_state)
    train_df, test_df = train_test_split(
        dataset,
        test_size=0.25,
        stratify=dataset[LABEL_COLUMN],
        random_state=random_state,
    )

    preprocessing = build_preprocessing_pipeline(categorical_features, numeric_features)

    pipeline = Pipeline(
        steps=[
            ('preprocess', preprocessing),
            (
                'classifier',
                MLPClassifier(
                    hidden_layer_sizes=(96, 48),
                    activation='relu',
                    solver='adam',
                    alpha=0.0001,
                    max_iter=900,
                    random_state=random_state,
                ),
            ),
        ],
    )

    X_train = train_df[feature_columns]
    y_train = train_df[LABEL_COLUMN]
    X_test = test_df[feature_columns]
    y_test = test_df[LABEL_COLUMN]

    pipeline.fit(X_train, y_train)
    predictions = pipeline.predict(X_test)
    accuracy = float(accuracy_score(y_test, predictions))
    report = classification_report(y_test, predictions, zero_division=0)

    model_bundle = {
        'pipeline': pipeline,
        'feature_columns': feature_columns,
        'categorical_features': categorical_features,
        'numeric_features': numeric_features,
        'label_column': LABEL_COLUMN,
    }
    dump(model_bundle, model_path)

    if metrics_file:
        metrics_file.parent.mkdir(parents=True, exist_ok=True)
        metrics_file.write_text(
            'Использованные признаки: '\
            f'{", ".join(feature_columns)}\n'
            f'Категориальные признаки: {", ".join(categorical_features) or "—"}\n'
            f'Числовые признаки: {", ".join(numeric_features) or "—"}\n\n'
            f'Accuracy: {accuracy:.4f}\n\n{report}',
            encoding='utf-8',
        )

    return {
        'accuracy': accuracy,
        'model_path': str(model_path),
        'expert_csv_path': str(expert_csv_path),
        'rows': int(dataset.shape[0]),
        'features': feature_columns,
    }
