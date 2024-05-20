from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from quiz import get_question_by_position, QUIZ_LEN


NUMS_EMOJI = dict(zip(tuple(range(10)), ('0️⃣', '1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣')))


def get_question_content(question_position: int):
    question, answers = get_question_by_position(question_position)
    question_num = f'<i>Вопрос {question_position + 1}/{QUIZ_LEN}</i>'
    question = f'<b>{question}</b>'
    hint = f'<i>Выберите вариант 1️⃣, 2️⃣ или 3️⃣, нажав на соответствующую кнопку ниже</i>'
    formatted_question = f'{question_num}\n\n{question}\n\n'

    inline_keyboard = InlineKeyboardBuilder()

    for index_, (role, answer) in enumerate(answers.items(), start=1):
        formatted_question += f'{NUMS_EMOJI[index_]} {answer}\n'
        inline_keyboard.add(types.InlineKeyboardButton(text=NUMS_EMOJI[index_],
                                                       callback_data=f'{role}'))

    formatted_question += f'\n{hint}'

    return formatted_question, inline_keyboard.as_markup()


async def collect_answer(answer: str,  state: FSMContext):
    user_data = await state.get_data()
    scores = user_data['scores']
    scores[answer] += 1
    await state.update_data(scores=scores)
