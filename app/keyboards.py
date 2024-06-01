from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_start_button(button_text: str):
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text=button_text,
                                     callback_data='start'))
    return builder.as_markup()


def get_url_button(text: str, url: str):
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text=text, url=url))
    return builder.as_markup()
