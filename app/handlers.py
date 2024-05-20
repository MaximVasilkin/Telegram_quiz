import asyncio
import logging
import random
from aiogram import Router, Bot, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ErrorEvent, User, CallbackQuery, FSInputFile
from quiz import KINESTHETIC, VISUAL, AUDIAL, QUIZ_LEN, PSYCHOTYPES
from states import QuizStates
from utils import get_question_content, collect_answer
from redis import Redis


router = Router()
logger = logging.getLogger()


#  обработка ошибок хендлеров роутера
@router.error()
async def error_handler(event: ErrorEvent, bot: Bot, event_from_user: User):
    logger.critical('Error caused by %s', event.exception, exc_info=True)
    await bot.send_message(event_from_user.id,
                           'Во время запроса произошла ошибка, попробуйте ещё раз или начните заново - /start')


@router.message(CommandStart())
async def command_start_handler(message: Message, state: FSMContext, bot: Bot) -> None:
    user_data = await state.get_data()
    previous_message_id = user_data.get('previous_message_id')

    if previous_message_id is not None:
        try:
            await bot.delete_message(message.chat.id, previous_message_id)
        except TelegramBadRequest:
            pass

    scores = {KINESTHETIC: 0, VISUAL: 0, AUDIAL: 0}
    await state.set_data({'scores': scores})
    await state.set_state(QuizStates.quiz_in_progress)

    question, keyboard = get_question_content(0)
    sent_message = await message.answer(question, reply_markup=keyboard)
    await state.update_data(previous_message_id=sent_message.message_id)


@router.callback_query(F.data, StateFilter(QuizStates.quiz_in_progress))
async def answering(callback: CallbackQuery,
                    state: FSMContext,
                    bot: Bot,
                    redis_cache: Redis) -> None:

    answer = callback.data
    await collect_answer(answer, state)

    user_data = await state.get_data()

    previous_message_id = user_data.get('previous_message_id')
    current_question_index = user_data.get('current_question_position', 0)
    next_question_index = current_question_index + 1

    if next_question_index > QUIZ_LEN - 1:
        chat_id = callback.message.chat.id
        message_id = callback.message.message_id

        scores = sorted(user_data['scores'].items(), key=lambda x: x[1], reverse=True)
        max_scored_psychotype, max_score = scores[0]

        scored_psychotypes = '\n'.join(f'{PSYCHOTYPES[psychotype]["rus"].title()} - {(score * 100) // QUIZ_LEN}%'
                                       for psychotype, score in scores)

        users_psychotype_eng = random.choice(tuple(filter(lambda x: x[1] == max_score, scores)))[0]
        users_psychotype = PSYCHOTYPES[users_psychotype_eng]
        psychotype_rus = users_psychotype['rus']
        p_s_ = '<tg-spoiler>А тут спряталась наша к Вам любовь ❤️🤗☺️</tg-spoiler>'
        result = f'Вы <b>{psychotype_rus.upper()}</b> \n\n' \
                 f'Результаты: \n\n' \
                 f'{scored_psychotypes}\n\n' \
                 f'Пройти заново: /start\n\n' \
                 f'{p_s_}'

        await bot.delete_message(callback.message.chat.id, previous_message_id)
        await asyncio.sleep(0.33)

        cached_photo_id = redis_cache.get(users_psychotype_eng)

        if cached_photo_id is None:
            # Отправка файла из файловой системы

            image_from_pc = FSInputFile(users_psychotype['image'])

            sent_message = await bot.send_photo(chat_id=chat_id,
                                                photo=image_from_pc,
                                                caption=result)

            widest_photo_id = max(sent_message.photo, key=lambda f: f.width).file_id
            redis_cache.set(users_psychotype_eng, widest_photo_id)
        else:
            sent_message = await bot.send_photo(chat_id=chat_id,
                                                photo=cached_photo_id,
                                                caption=result)

        await state.update_data(previous_message_id=sent_message.message_id)
        await state.set_state(state=None)
        return

    question, keyboard = get_question_content(next_question_index)
    await bot.edit_message_text(question, callback.message.chat.id, previous_message_id, reply_markup=keyboard)
    await state.update_data(current_question_position=next_question_index)


@router.callback_query()
async def on_restart(callback: CallbackQuery, bot: Bot):
    message = callback.message
    await bot.delete_message(message.chat.id, message.message_id)
    await asyncio.sleep(0.33)
    await message.answer('Ой! Что-то пошло не так! Начните заново /start')
