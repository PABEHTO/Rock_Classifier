from __future__ import annotations

from pathlib import Path

import pandas as pd
from joblib import load


class MlRockClassifier:
    def __init__(self, model_path: str | Path) -> None:
        self.model_path = Path(model_path)
        self.pipeline = None
        self.error_message = ''
        self._load()

    def _load(self) -> None:
        if not self.model_path.exists():
            self.error_message = f'Файл модели не найден: {self.model_path}'
            return
        try:
            self.pipeline = load(self.model_path)
        except Exception as exc:  # pragma: no cover - защита на случай повреждённого файла
            self.error_message = f'Не удалось загрузить ML-модель: {exc}'

    @property
    def is_ready(self) -> bool:
        return self.pipeline is not None

    def predict(self, features: dict[str, object], allowed_labels: list[str] | None = None, top_n: int = 3) -> tuple[str, list[tuple[str, float]]]:
        if not self.is_ready:
            raise RuntimeError(self.error_message or 'ML-модель недоступна.')

        sample = pd.DataFrame(
            [features],
            columns=['Происхождение', 'Структура', 'Минеральный состав', 'Плотность'],
        )
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
