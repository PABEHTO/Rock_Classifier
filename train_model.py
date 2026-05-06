from __future__ import annotations

from pathlib import Path

from rock_classifier.data import build_default_state
from rock_classifier.services import train_and_save_model


BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / 'models' / 'rock_classifier_mlp.joblib'
EXPERT_CSV_PATH = BASE_DIR / 'models' / 'expert_knowledge_base.csv'
METRICS_PATH = BASE_DIR / 'models' / 'training_metrics.txt'


def main() -> None:
    state = build_default_state()
    result = train_and_save_model(
        state=state,
        model_path=MODEL_PATH,
        expert_csv_path=EXPERT_CSV_PATH,
        metrics_path=METRICS_PATH,
        n_per_class=350,
        random_state=42,
    )
    print('ML-модель обучена и сохранена.')
    print(f"Accuracy: {result['accuracy']:.4f}")
    print(f"Строк в синтетической выборке: {result['rows']}")
    print(f"Файл модели: {result['model_path']}")
    print(f"CSV базы знаний: {result['expert_csv_path']}")


if __name__ == '__main__':
    main()
