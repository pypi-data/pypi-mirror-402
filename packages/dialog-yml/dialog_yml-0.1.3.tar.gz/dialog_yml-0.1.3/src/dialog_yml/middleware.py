from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject


class DialogYAMLMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        data["dialog_yml"] = self.dialog_yml
        return await handler(event, data)

    def __init__(self, dialog_yml):
        self.dialog_yml = dialog_yml
