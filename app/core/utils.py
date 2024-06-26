import asyncio
import datetime
from contextlib import suppress
from io import BytesIO
from os import getenv
from aiogram import html, types
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from .quiz import get_question_by_position, QUIZ_LEN
from db.models import UserModel
import pandas as pd
from .time_tools import time_range_to_str, UTC_TZ, MSK_TZ, ROW_TABLE_FILE_FORMAT


NUMS_EMOJI = dict(zip(tuple(range(10)), ('0️⃣', '1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣')))


def get_question_content(question_position: int) -> tuple[str, InlineKeyboardMarkup]:
    question, answers = get_question_by_position(question_position)
    question_num = html.italic(f'Вопрос {question_position + 1}/{QUIZ_LEN}')
    question = html.bold(question)
    hint = html.italic('Выберите вариант 1️⃣, 2️⃣ или 3️⃣, нажав на соответствующую кнопку ниже')
    formatted_question = f'{question_num}\n\n{question}\n\n'

    inline_keyboard = InlineKeyboardBuilder()

    for index_, (role, answer) in enumerate(answers.items(), start=1):
        formatted_question += f'{NUMS_EMOJI[index_]} {answer}\n'
        inline_keyboard.add(types.InlineKeyboardButton(text=NUMS_EMOJI[index_],
                                                       callback_data=f'{role}'))

    formatted_question += f'\n{hint}'

    return formatted_question, inline_keyboard.as_markup()


async def collect_answer(answer: str,  state: FSMContext) -> None:
    user_data = await state.get_data()
    scores = user_data['scores']
    scores[answer] += 1
    await state.update_data(scores=scores)


async def replace_old_question(message: Message, next_question_index: int, previous_message_id: int) -> Message:
    question, keyboard = get_question_content(next_question_index)
    return await message.bot.edit_message_text(question, message.chat.id, previous_message_id, reply_markup=keyboard)


async def del_previous_msg(msg_ids, message):
    for msg_id in msg_ids:
        await asyncio.sleep(0.33)
        with suppress(TelegramBadRequest):
            await message.bot.delete_message(message.chat.id, int(msg_id))


def get_admins() -> set[int]:
    return {int(admin_id) for admin_id in getenv('ADMINS').split(',')}


def users_to_excel(users: list[UserModel, int],  # need ordered by id users!
                   from_date: datetime.datetime = None,  # need UTC with timezone
                   to_date: datetime.datetime = None,  # need UTC with timezone
                   tz=MSK_TZ):

    all_time = not from_date and not to_date

    if all_time:
        start_date = UTC_TZ.localize(users[0][0].joined_at).astimezone(tz)
        end_date = datetime.datetime.now(tz)
        time_interval = time_range_to_str(start_date, end_date, ROW_TABLE_FILE_FORMAT)
    else:
        time_interval = time_range_to_str(from_date.astimezone(tz), to_date.astimezone(tz), ROW_TABLE_FILE_FORMAT)

    file_buffer = BytesIO()

    tables = {'Только присоединились': [],
              'Присоединились и прошли тест': [],
              'Только прошли тест': []}

    test_finished_count = 0

    for user, action_count in users:
        test_finished_count += action_count
        user_data = user.as_dict()
        del user_data['joined_at']
        if not action_count:
            tables['Только присоединились'].append(user_data)
        elif (all_time or (from_date <= UTC_TZ.localize(user.joined_at) <= to_date)) and action_count:
            tables['Присоединились и прошли тест'].append(user_data | {'Тест пройден раз': action_count})
        elif not all_time and action_count:
            tables['Только прошли тест'].append(user_data | {'Тест пройден раз': action_count})

    joined_count = len(tables['Только присоединились'])
    joined_and_tested_count = len(tables['Присоединились и прошли тест'])
    tested_count = len(tables['Только прошли тест'])
    all_joined_count = joined_count + joined_and_tested_count
    total_count = joined_count + joined_and_tested_count + tested_count
    percentage = ((joined_and_tested_count / all_joined_count) * 100) if all_joined_count else 100

    summary_info = {'Период': [time_interval],
                    'Активных человек': [total_count],
                    'Людей только присоединилось': [joined_count],
                    'Людей присоединились и прошли тест': [joined_and_tested_count],
                    'Людей только прошли тест': [tested_count],
                    'Процент людей, прошедших тест': [f'{percentage:.2f}%'],
                    'Тест пройден раз': test_finished_count}

    if all_time:
        del summary_info['Людей только прошли тест']

    summary_df = pd.DataFrame(summary_info)
    writer = pd.ExcelWriter(file_buffer, engine='xlsxwriter')
    summary_df.to_excel(writer, sheet_name='Статистика', index=False)

    # Записываем каждый DataFrame на отдельный лист в файле Excel
    for table_name, data in tables.items():
        if data:
            data = pd.DataFrame(data)
            data.to_excel(writer, sheet_name=table_name, index=False)

    # Закрываем writer для сохранения файла
    writer.close()
    result = file_buffer.getvalue()
    file_buffer.close()

    return result




