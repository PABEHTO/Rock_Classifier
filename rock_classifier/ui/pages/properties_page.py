from __future__ import annotations

from .base import EditableListPage


class PropertiesPage(EditableListPage):
    def __init__(self, parent, app: 'RockClassifierApp') -> None:
        super().__init__(parent, app, 'Окно «Свойства»', 'Отдельное окно для списка свойств породы.')
        self.refresh()

    def get_items(self) -> list[str]:
        return self.app.state.property_names()

    def add_item(self, value: str) -> bool:
        return self.app.editor_service.add_property(value)

    def delete_item(self, value: str) -> bool:
        return self.app.editor_service.delete_property(value)
