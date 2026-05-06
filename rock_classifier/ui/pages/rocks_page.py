from __future__ import annotations

from .base import EditableListPage


class RocksPage(EditableListPage):
    def __init__(self, parent, app: 'RockClassifierApp') -> None:
        super().__init__(parent, app, 'Окно «Виды пород»', 'Добавление и удаление видов пород согласно сценарию из курсовой работы.')
        self.refresh()

    def get_items(self) -> list[str]:
        return self.app.state.rocks

    def add_item(self, value: str) -> bool:
        return self.app.editor_service.add_rock(value)

    def delete_item(self, value: str) -> bool:
        return self.app.editor_service.delete_rock(value)
