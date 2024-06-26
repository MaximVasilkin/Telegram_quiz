from aiogram.filters import BaseFilter
from aiogram.types import Message
import datetime


class DateIntervalFilter(BaseFilter):

    async def __call__(self, message: Message) -> bool | dict:

        try:
            date_format = '%d.%m.%Y'
            from_date, to_date = message.text.split('-')
            from_date = datetime.datetime.strptime(from_date.strip(), date_format)
            to_date = datetime.datetime.strptime(to_date.strip(), date_format)
            if from_date > to_date:
                return False
        except ValueError:
            return False

        return {'from_date': from_date, 'to_date': to_date}


class PositiveIntFilter(BaseFilter):

    async def __call__(self, message: Message) -> bool | dict:

        try:
            num = int(message.text.strip())
            if num < 1:
                return False
        except ValueError:
            return False

        return {'positive_int': num}
