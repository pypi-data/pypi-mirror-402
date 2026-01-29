from typing import Union, Self

from aiogram_dialog.widgets.kbd import Counter
from aiogram_dialog.widgets.text import Progress

from dialog_yml.models.base import WidgetModel
from dialog_yml.models.funcs.func import FuncField
from dialog_yml.models.widgets.texts.text import TextField
from dialog_yml.utils import clean_empty


class ProgressModel(WidgetModel):
    field: TextField
    width: int = None
    filled: TextField = None
    empty: TextField = None

    def to_object(self) -> Progress:
        kwargs = clean_empty(
            {
                "field": self.field.val,
                "width": self.width,
                "filled": self.filled.val,
                "empty": self.empty.val,
                "when": self.when.func if self.when else None,
            }
        )
        return Progress(**kwargs)

    @classmethod
    def to_model(cls, data: Union[str, dict, Self]) -> Self:
        if isinstance(data, cls):
            return data
        if isinstance(data, str):
            data = {"field": {"val": data, "formatted": True}}
        return cls(**data)


class CounterModel(WidgetModel):
    id: str
    plus: TextField = None
    minus: TextField = None
    text: TextField = None
    min_value: float = None
    max_value: float = None
    increment: float = None
    default: float = None
    cycle: bool = None
    on_text_click: FuncField = None
    on_value_changed: FuncField = None

    def to_object(self) -> Counter:
        kwargs = clean_empty(
            {
                "id": self.id,
                "plus": self.plus.to_object() if self.plus else None,
                "minus": self.minus.to_object() if self.minus else None,
                "text": self.text.to_object() if self.text else None,
                "min_value": self.min_value,
                "max_value": self.max_value,
                "increment": self.increment,
                "default": self.default,
                "cycle": self.cycle,
                "on_click": self.on_text_click.func if self.on_text_click else None,
                "on_value_changed": self.on_value_changed.func
                if self.on_value_changed
                else None,
                "when": self.when.func if self.when else None,
            }
        )
        return Counter(**kwargs)

    @classmethod
    def to_model(cls, data: Union[str, dict, Self]) -> Self:
        if isinstance(data, cls):
            return data
        if isinstance(data, str):
            data = {"id": data}
        return cls(**data)
