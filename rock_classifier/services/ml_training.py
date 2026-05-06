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

from rock_classifier.models import AppState, parse_number_range


FEATURE_COLUMNS = ['Происхождение', 'Структура', 'Минеральный состав', 'Плотность']
LABEL_COLUMN = 'Вид породы'


def build_expert_dataframe(state: AppState) -> pd.DataFrame:
    rows: list[dict[str, str]] = []
    for rock in state.rocks:
        selected_properties = state.selected_properties_for_rock(rock)
        row = {LABEL_COLUMN: rock}
        for property_name in FEATURE_COLUMNS:
            if property_name not in selected_properties:
                row[property_name] = ''
            else:
                row[property_name] = state.get_rock_value(rock, property_name)
        rows.append(row)
    return pd.DataFrame(rows, columns=[LABEL_COLUMN, *FEATURE_COLUMNS])


def _sample_from_range(range_text: str, rng: random.Random) -> float:
    start, end = parse_number_range(range_text)
    if start == end:
        return round(start, 3)
    return round(rng.uniform(start, end), 3)


def generate_synthetic_dataset(state: AppState, n_per_class: int = 350, random_state: int = 42) -> pd.DataFrame:
    rng = random.Random(random_state)
    rows: list[dict[str, object]] = []
    for rock in state.rocks:
        values = state.rock_property_values.get(rock, {})
        for _ in range(n_per_class):
            rows.append(
                {
                    'Происхождение': values.get('Происхождение', ''),
                    'Структура': values.get('Структура', ''),
                    'Минеральный состав': values.get('Минеральный состав', ''),
                    'Плотность': _sample_from_range(values.get('Плотность', '1.00–4.00'), rng),
                    LABEL_COLUMN: rock,
                },
            )
    return pd.DataFrame(rows, columns=[*FEATURE_COLUMNS, LABEL_COLUMN])


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

    expert_df = build_expert_dataframe(state)
    expert_df.to_csv(expert_csv_path, index=False, encoding='utf-8-sig')

    dataset = generate_synthetic_dataset(state, n_per_class=n_per_class, random_state=random_state)
    train_df, test_df = train_test_split(
        dataset,
        test_size=0.25,
        stratify=dataset[LABEL_COLUMN],
        random_state=random_state,
    )

    categorical_features = ['Происхождение', 'Структура', 'Минеральный состав']
    numeric_features = ['Плотность']

    preprocessing = ColumnTransformer(
        transformers=[
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
        ],
    )

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

    X_train = train_df[FEATURE_COLUMNS]
    y_train = train_df[LABEL_COLUMN]
    X_test = test_df[FEATURE_COLUMNS]
    y_test = test_df[LABEL_COLUMN]

    pipeline.fit(X_train, y_train)
    predictions = pipeline.predict(X_test)
    accuracy = float(accuracy_score(y_test, predictions))
    report = classification_report(y_test, predictions)

    dump(pipeline, model_path)

    if metrics_file:
        metrics_file.parent.mkdir(parents=True, exist_ok=True)
        metrics_file.write_text(
            f'Accuracy: {accuracy:.4f}\n\n{report}',
            encoding='utf-8',
        )

    return {
        'accuracy': accuracy,
        'model_path': str(model_path),
        'expert_csv_path': str(expert_csv_path),
        'rows': int(dataset.shape[0]),
    }
