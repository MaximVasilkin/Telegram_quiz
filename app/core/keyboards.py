from functools import wraps
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from .callback_fabs import LeastDateCallbackFactory


def get_inlinebuilder_return_asmarkup(old_func):
    @wraps(old_func)
    def new_func(*args, **kwargs) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        old_func(builder, *args, **kwargs)
        return builder.as_markup()
    return new_func


@get_inlinebuilder_return_asmarkup
def get_start_button(builder: InlineKeyboardBuilder, button_text: str):
    builder.add(InlineKeyboardButton(text=button_text,
                                     callback_data='start'))


@get_inlinebuilder_return_asmarkup
def get_url_button(builder: InlineKeyboardBuilder, text: str, url: str):
    builder.add(InlineKeyboardButton(text=text, url=url))


@get_inlinebuilder_return_asmarkup
def get_choose_date_intervals_keyboard(builder: InlineKeyboardBuilder):
    periods = (1, 3, 5, 7, 10, 15, 30, 90)
    for period in periods:
        builder.button(text=f'{period} д.', callback_data=LeastDateCallbackFactory(days=period))
    builder.button(text='За всё время', callback_data=LeastDateCallbackFactory(all_time=1))
    builder.adjust(4)
