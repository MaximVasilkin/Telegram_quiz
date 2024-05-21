from aiogram import html, types
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from quiz import get_question_by_position, QUIZ_LEN


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

