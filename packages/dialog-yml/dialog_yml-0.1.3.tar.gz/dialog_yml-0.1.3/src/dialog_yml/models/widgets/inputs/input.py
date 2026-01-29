from typing import Union, Self

from aiogram.enums import ContentType
from aiogram_dialog.widgets.input import MessageInput
from pydantic import field_validator

from dialog_yml.models.base import WidgetModel
from dialog_yml.models.funcs.func import FuncField
from dialog_yml.utils import clean_empty


class MessageInputModel(WidgetModel):
    func: FuncField
    filter: FuncField = None
    content_types: list[ContentType] = [ContentType.ANY]

    def to_object(self) -> MessageInput:
        kwargs = clean_empty(
            {
                "func": self.func.func if self.func else None,
                "filter": self.filter.func if self.filter else None,
                "content_types": self.content_types,
            }
        )
        return MessageInput(**kwargs)

    @field_validator("content_types", mode="before")
    def validate_content_types(cls, value):
        if not value:
            return [ContentType.ANY]

        if isinstance(value, str):
            value = [value]

        result = []
        if isinstance(value, list):
            for v in value:
                if isinstance(v, ContentType):
                    result.append(v)
                elif isinstance(v, str):
                    try:
                        result.append(ContentType[v.upper()])
                    except KeyError:
                        raise ValueError(f"Invalid content type: {v}")
                else:
                    raise ValueError(f"Invalid content type value: {v}")

        return result

    @classmethod
    def to_model(cls, data: Union[dict, Self]) -> Self:
        if isinstance(data, cls):
            return data
        return cls(**data)
