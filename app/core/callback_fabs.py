from typing import Optional

from aiogram.filters.callback_data import CallbackData


class LeastDateCallbackFactory(CallbackData, prefix='fabdate'):

    days: Optional[int] = None
    all_time: Optional[int] = None
