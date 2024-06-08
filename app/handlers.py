import asyncio
import logging
import random
from aiogram import html, Router, Bot, F
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ErrorEvent, User, CallbackQuery, FSInputFile
from keyboards import get_start_button, get_url_button
from quiz import KINESTHETIC, VISUAL, AUDIAL, QUIZ_LEN, PSYCHOTYPES
from states import QuizStates
from utils import collect_answer, replace_old_question, del_previous_msg
import redis.asyncio as async_redis


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
        await del_previous_msg(str(previous_message_id).split(' '), message)

    scores = {KINESTHETIC: 0, VISUAL: 0, AUDIAL: 0}
    await state.set_data({'scores': scores})
    await state.set_state(QuizStates.quiz_in_progress)

    start_message = f'{html.bold(html.quote(message.from_user.first_name))}, приветствуем вас!\n\n' \
                    f'🌿 Мы предлагаем пройти вам небольшой тест: ' \
                    f'узнайте, какой сад подойдет именно Вам и получите визуализацию соответствующего пространства! \n' \
                    f'Начинаем?'

    keyboard = get_start_button('Конечно!')

    sent_message = await message.answer(start_message, reply_markup=keyboard)

    await state.update_data(previous_message_id=sent_message.message_id)


@router.callback_query(F.data == 'start', StateFilter(QuizStates.quiz_in_progress))
async def start_quiz(callback: CallbackQuery,
                     state: FSMContext) -> None:
    user_data = await state.get_data()
    previous_message_id = user_data.get('previous_message_id')
    await replace_old_question(callback.message, 0, previous_message_id)


@router.callback_query(F.data, StateFilter(QuizStates.quiz_in_progress))
async def answering(callback: CallbackQuery,
                    state: FSMContext,
                    bot: Bot,
                    event_from_user: User,
                    redis_client: async_redis.Redis) -> None:

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

        scored_psychotypes = '\n'.join(f'{PSYCHOTYPES[psychotype]["garden"].title()} - {(score * 100) // QUIZ_LEN}%'
                                       for psychotype, score in scores)

        users_psychotype_eng = random.choice(tuple(filter(lambda x: x[1] == max_score, scores)))[0]
        users_psychotype = PSYCHOTYPES[users_psychotype_eng]
        psychotype_garden = users_psychotype['garden']
        psychotype_description = users_psychotype['description']

        link = 'https://school.garden-group.online/marathon_landesign'

        p_s_ = html.italic((f'{html.bold(html.quote(event_from_user.first_name))}, '
                            f'станьте профессионалом в области ландшафтного дизайна на нашем двухдневном марафоне '
                            f'“Как начать карьеру в ландшафтном дизайне 2024 году”.\n'
                            f'{html.bold("Ландшафтный дизайн - это профессия будущего.")} '
                            f'Спрос на квалифицированных специалистов растёт с каждым днём.\n\n'
                            f'{html.underline(html.bold(html.link("Зарегистрируйся на наш марафон", link)))} '
                            f'{html.bold("сегодня")} и сделай первый шаг к своей мечте!\n\n'
                            'С любовью, \n'
                            f'{html.bold("Garden Group")}🍀'))

        result = (f'{html.italic(html.bold(f"Ваш сад - {psychotype_garden}"))}'
                  f'{psychotype_description}\n\n'
                  f'{html.underline("Результаты:")} \n\n'
                  f'{scored_psychotypes}\n\n'
                  f'Пройти заново: /start')

        await del_previous_msg(str(previous_message_id).split(' '), callback.message)

        cached_photo_id = await redis_client.get(users_psychotype_eng)

        if cached_photo_id is None:
            # Отправка файла из файловой системы

            image_from_pc = FSInputFile(users_psychotype['image'])

            sent_message = await bot.send_photo(chat_id=chat_id,
                                                photo=image_from_pc,
                                                caption=result)

            widest_photo_id = max(sent_message.photo, key=lambda f: f.width).file_id
            await redis_client.set(users_psychotype_eng, widest_photo_id)
        else:

            sent_message = await bot.send_photo(chat_id=chat_id,
                                                photo=cached_photo_id,
                                                caption=result)

        url_button = get_url_button('Зарегистрироваться', link)

        await asyncio.sleep(1)
        sent_ps = await callback.message.answer(p_s_, reply_markup=url_button)

        await state.update_data(previous_message_id=f'{sent_message.message_id} {sent_ps.message_id}')

        await state.set_state(state=None)
        return

    await replace_old_question(callback.message, next_question_index, previous_message_id)
    await state.update_data(current_question_position=next_question_index)


@router.callback_query()
async def on_restart(callback: CallbackQuery, bot: Bot):
    message = callback.message
    await bot.delete_message(message.chat.id, message.message_id)
    await asyncio.sleep(0.33)
    await message.answer('Ой! Что-то пошло не так! Начните заново /start')
