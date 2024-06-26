import pytz
from datetime import datetime


MSK_TZ = pytz.timezone('Europe/Moscow')
UTC_TZ = pytz.timezone('UTC')

FILE_NAME_FORMAT = '%d_%m_%Y_%H_%M'
ROW_TABLE_FILE_FORMAT = '%d.%m.%Y.%H:%M'


def time_range_to_str(from_date: datetime, to_date: datetime, formatter: str, sep='-') -> str:
    return f'{from_date.strftime(formatter)}{sep}{to_date.strftime(formatter)}'
