import operator
from typing import Union, Self

from aiogram_dialog.widgets.kbd import Checkbox, Select, Radio, Multiselect

from dialog_yml.models.base import WidgetModel
from dialog_yml.models.funcs.func import FuncModel, FuncField
from dialog_yml.models.widgets.texts.text import TextField, FormatModel
from dialog_yml.utils import clean_empty


class CheckboxModel(WidgetModel):
    id: str
    on_state_changed: FuncField = None
    checked: TextField = TextField(val="[✓] Checked")
    unchecked: TextField = TextField(val="[ ] Unchecked")
    default: bool = True

    def to_object(self) -> Checkbox:
        args = (
            self.checked.to_object(),
            self.unchecked.to_object(),
        )
        kwargs = clean_empty(
            {
                "id": self.id,
                "when": self.when.func if self.when else None,
                "on_state_changed": self.on_state_changed.func
                if self.on_state_changed
                else None,
                "default": self.default,
            }
        )
        return Checkbox(*args, **kwargs)

    @classmethod
    def to_model(cls, data: Union[str, dict, Self]) -> Self:
        if isinstance(data, cls):
            return data
        return cls(**data)


class SelectModel(WidgetModel):
    text: TextField = None
    id: str
    items: Union[str, list, dict]
    item_id_getter: Union[int, str]
    on_click: FuncField = None

    def to_object(self) -> Select:
        item_id_getter = self.item_id_getter
        if isinstance(item_id_getter, int):
            item_id_getter = operator.itemgetter(item_id_getter)
        if isinstance(item_id_getter, str):
            item_id_getter = FuncModel.to_model(item_id_getter).func
        kwargs = clean_empty(
            {
                "text": self.text.to_object(),
                "id": self.id,
                "items": self.items,
                "item_id_getter": item_id_getter,
                "on_click": self.on_click.func if self.on_click else None,
                "when": self.when.func if self.when else None,
            }
        )
        return Select(**kwargs)

    @classmethod
    def to_model(cls, data: Union[str, dict, Self]) -> Self:
        if isinstance(data, cls):
            return data
        if isinstance(data, dict):
            if formatted_text := data.pop("format", {}):
                data["text"] = FormatModel.to_model(formatted_text)
        return cls(**data)


class RadioModel(WidgetModel):
    id: str
    items: Union[str, list, dict]
    on_state_changed: FuncField = None
    checked: TextField = TextField(val="✓ {item}")
    unchecked: TextField = TextField(val="{item}")
    item_id_getter: Union[int, str, FuncField]

    def to_object(self) -> Radio:
        args = [
            self.checked.to_object(),
            self.unchecked.to_object(),
        ]
        item_id_getter = self.item_id_getter
        if isinstance(item_id_getter, int):
            item_id_getter = operator.itemgetter(item_id_getter)
        if isinstance(item_id_getter, str):
            item_id_getter = FuncModel.to_model(item_id_getter).func
        kwargs = clean_empty(
            {
                "id": self.id,
                "when": self.when.func if self.when else None,
                "items": self.items,
                "item_id_getter": item_id_getter,
                "on_state_changed": self.on_state_changed.func
                if self.on_state_changed
                else None,
            }
        )
        return Radio(*args, **kwargs)

    @classmethod
    def to_model(cls, data: Union[str, dict, Self]) -> Self:
        if isinstance(data, cls):
            return data
        return cls(**data)


class MultiSelectModel(SelectModel, CheckboxModel):
    min_selected: int = 0
    max_selected: int = 0
    checked: TextField = TextField(val="✓ {item[0]}", formatted=True)
    unchecked: TextField = TextField(val="{item[0]}", formatted=True)

    def to_object(self) -> Multiselect:
        item_id_getter = self.item_id_getter
        if isinstance(item_id_getter, int):
            item_id_getter = operator.itemgetter(item_id_getter)
        if isinstance(item_id_getter, str):
            item_id_getter = FuncModel.to_model(item_id_getter).func
        kwargs = clean_empty(
            {
                "checked_text": self.checked.to_object(),
                "unchecked_text": self.unchecked.to_object(),
                "id": self.id,
                "items": self.items,
                "item_id_getter": item_id_getter,
                "on_state_changed": self.on_state_changed.func
                if self.on_state_changed
                else None,
                "on_click": self.on_click.func if self.on_click else None,
                "when": self.when.func if self.when else None,
            }
        )
        return Multiselect(**kwargs)

    @classmethod
    def to_model(cls, data: Union[str, dict, Self]) -> Self:
        if isinstance(data, cls):
            return data
        return cls(**data)
