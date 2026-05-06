from __future__ import annotations

from pathlib import Path

import pandas as pd
from joblib import load


DEFAULT_FEATURE_COLUMNS = ['Происхождение', 'Структура', 'Минеральный состав', 'Плотность']


class MlRockClassifier:
    def __init__(self, model_path: str | Path) -> None:
        self.model_path = Path(model_path)
        self.pipeline = None
        self.feature_columns: list[str] = DEFAULT_FEATURE_COLUMNS[:]
        self.categorical_features: list[str] = []
        self.numeric_features: list[str] = []
        self.error_message = ''
        self._load()

    def _load(self) -> None:
        if not self.model_path.exists():
            self.error_message = f'Файл модели не найден: {self.model_path}'
            return
        try:
            loaded = load(self.model_path)
            if isinstance(loaded, dict) and 'pipeline' in loaded:
                self.pipeline = loaded['pipeline']
                self.feature_columns = list(loaded.get('feature_columns') or DEFAULT_FEATURE_COLUMNS)
                self.categorical_features = list(loaded.get('categorical_features') or [])
                self.numeric_features = list(loaded.get('numeric_features') or [])
            else:
                # Совместимость со старым файлом модели, где сохранялся только Pipeline.
                self.pipeline = loaded
                self.feature_columns = DEFAULT_FEATURE_COLUMNS[:]
                self.categorical_features = ['Происхождение', 'Структура', 'Минеральный состав']
                self.numeric_features = ['Плотность']
        except Exception as exc:  # pragma: no cover - защита на случай повреждённого файла
            self.error_message = f'Не удалось загрузить ML-модель: {exc}'

    @property
    def is_ready(self) -> bool:
        return self.pipeline is not None

    def _prepare_sample(self, features: dict[str, object]) -> pd.DataFrame:
        row: dict[str, object] = {}
        for property_name in self.feature_columns:
            value = features.get(property_name)
            if property_name in self.numeric_features:
                row[property_name] = value if value not in ('', None) else None
            else:
                row[property_name] = '' if value is None else value
        return pd.DataFrame([row], columns=self.feature_columns)

    def predict(
        self,
        features: dict[str, object],
        allowed_labels: list[str] | None = None,
        top_n: int = 3,
    ) -> tuple[str, list[tuple[str, float]]]:
        if not self.is_ready:
            raise RuntimeError(self.error_message or 'ML-модель недоступна.')

        sample = self._prepare_sample(features)
        probabilities = self.pipeline.predict_proba(sample)[0]
        labels = list(self.pipeline.classes_)
        scored = list(zip(labels, probabilities, strict=True))

        if allowed_labels is not None:
            allowed_set = set(allowed_labels)
            scored = [item for item in scored if item[0] in allowed_set]

        if not scored:
            raise RuntimeError('ML-модель не смогла оценить подходящие классы.')

        scored.sort(key=lambda item: item[1], reverse=True)
        predicted_label = str(scored[0][0])

        # В интерфейсе вероятность выводится с точностью до сотых процента.
        # Поэтому убираем оценки, которые выглядели бы как 0.00%, чтобы результат
        # ML-модели не засорялся фактически нулевыми строками.
        visible_scores = [item for item in scored if round(float(item[1]) * 100, 2) > 0]
        top_scores = [(str(label), float(score)) for label, score in visible_scores[:top_n]]
        if not top_scores:
            top_scores = [(predicted_label, float(scored[0][1]))]
        return predicted_label, top_scores
