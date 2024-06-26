import datetime
from aiogram import html, Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.enums.chat_action import ChatAction
from db.utils import AsyncDataBase
from .callback_fabs import LeastDateCallbackFactory
from .filters import DateIntervalFilter, PositiveIntFilter
from .middlewares import OnlyForAdminMiddleware, OnePersonOperationMiddleware
from .keyboards import get_choose_date_intervals_keyboard
from .utils import users_to_excel
from .time_tools import UTC_TZ, MSK_TZ, time_range_to_str, FILE_NAME_FORMAT
from db.models import UserModel


admin_router = Router()
admin_router.message.outer_middleware(OnlyForAdminMiddleware())
admin_router.callback_query.outer_middleware(OnlyForAdminMiddleware())
admin_router.message.middleware(OnePersonOperationMiddleware())
admin_router.callback_query.middleware(OnePersonOperationMiddleware())


async def send_users_as_excel(message: Message,
                              users: list[UserModel, int],
                              from_date: datetime.datetime = None,
                              to_date: datetime.datetime = None,
                              file_name: str = 'users',
                              table_row_tz=MSK_TZ):
    if not users:
        return await message.answer('За указанный период нет активности')

    excel_buffer = users_to_excel(users, from_date, to_date, table_row_tz)

    document = BufferedInputFile(excel_buffer, filename=f'{file_name}.xlsx')

    await message.answer_document(document)


@admin_router.message(Command('menu'))
async def command_stats_handler(message: Message) -> None:

    commands = {'/stats':
                    'Открыть меню выгрузки статистики (за предопределённое количество дней или за всё время).',

                'Интервал в формате ДД.ММ.ГГГГ-ДД.ММ.ГГГГ':
                    f'Выгрузить данные за определённый интервал дат. Пример команды: {html.code("01.01.2024-31.12.2024")}',

                'Любое целое число N':
                    f'Выгрузить статистику за последние N дней. Пример команды: {html.code("30")}'}

    text = '\n\n'.join(f'{html.bold(html.italic(k))} - {v}' for k, v in commands.items())

    await message.answer(text)


@admin_router.message(Command('stats'))
async def command_stats_handler(message: Message) -> None:

    text = 'Выберите, за какой период отобразить статистику.\n' \
           f'Или введите его в формате: {html.bold("ДД.ММ.ГГГГ-ДД.ММ.ГГГГ")}\n' \
           f'Например: 01.01.2024-31.12.2024'

    await message.answer(text, reply_markup=get_choose_date_intervals_keyboard())


@admin_router.message(PositiveIntFilter(),
                      flags={'long_operation': ChatAction.UPLOAD_DOCUMENT,
                             'one_person_operation': 1})
async def get_stats_for_n_days(message: Message,
                               positive_int: int,
                               async_db: AsyncDataBase):

    to_date = datetime.datetime.now(UTC_TZ)
    from_date = to_date - datetime.timedelta(positive_int)

    msk_from_date: datetime.datetime = from_date.astimezone(MSK_TZ)
    msk_to_date: datetime.datetime = to_date.astimezone(MSK_TZ)

    users = await async_db.get_users_with_count_actions_by_date_range(from_date.replace(tzinfo=None), to_date.replace(tzinfo=None))
    file_name = f'{time_range_to_str(msk_from_date, msk_to_date, FILE_NAME_FORMAT)}'
    await send_users_as_excel(message, users, from_date, to_date, file_name)


@admin_router.callback_query(LeastDateCallbackFactory.filter(F.days),
                             flags={'long_operation': ChatAction.UPLOAD_DOCUMENT,
                                    'one_person_operation': 1})
async def get_stats_for_days(callback: CallbackQuery,
                             callback_data: LeastDateCallbackFactory,
                             async_db: AsyncDataBase):

    to_date = datetime.datetime.now(UTC_TZ)
    from_date = to_date - datetime.timedelta(days=callback_data.days)

    msk_from_date: datetime.datetime = from_date.astimezone(MSK_TZ)
    msk_to_date: datetime.datetime = to_date.astimezone(MSK_TZ)

    users = await async_db.get_users_with_count_actions_by_date_range(from_date.replace(tzinfo=None), to_date.replace(tzinfo=None))
    file_name = f'{time_range_to_str(msk_from_date, msk_to_date, FILE_NAME_FORMAT)}'
    await send_users_as_excel(callback.message, users, from_date, to_date, file_name)


@admin_router.callback_query(LeastDateCallbackFactory.filter(F.all_time),
                             flags={'long_operation': ChatAction.UPLOAD_DOCUMENT,
                                    'one_person_operation': 1})
async def get_all_stats(callback: CallbackQuery,
                        async_db: AsyncDataBase):

    users = await async_db.get_all_users_with_count_actions()

    current_time_msk = datetime.datetime.now(MSK_TZ)
    formatted_time = current_time_msk.strftime(FILE_NAME_FORMAT)
    file_name = f'all_{formatted_time}'

    await send_users_as_excel(callback.message, users, file_name=file_name)


@admin_router.message(F.text, DateIntervalFilter(),
                      flags={'long_operation': ChatAction.UPLOAD_DOCUMENT,
                             'one_person_operation': 1})
async def get_stats_for_interval(message: Message,
                                 from_date: datetime.datetime,
                                 to_date: datetime.datetime,
                                 async_db: AsyncDataBase):

    from_date = from_date.replace(hour=00, minute=00, second=00, microsecond=00000)
    to_date = to_date.replace(hour=23, minute=59, second=59, microsecond=999999)

    msk_from_date: datetime.datetime = MSK_TZ.localize(from_date)
    msk_to_date: datetime.datetime = MSK_TZ.localize(to_date)

    utc_from_date = msk_from_date.astimezone(UTC_TZ)
    utc_to_date = msk_to_date.astimezone(UTC_TZ)

    users = await async_db.get_users_with_count_actions_by_date_range(utc_from_date.replace(tzinfo=None), utc_to_date.replace(tzinfo=None))
    file_name = f'{time_range_to_str(msk_from_date, msk_to_date, FILE_NAME_FORMAT)}'
    await send_users_as_excel(message, users, utc_from_date, utc_to_date, file_name)


@admin_router.message(F.text)
async def invalid_time_interval(message: Message) -> None:
    await message.answer('Некорректный формат команды')

