import datetime
from contextlib import suppress
from sqlalchemy import select, update, and_, or_, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import contains_eager
from .models import Base, UserModel, ActionModel


class AsyncDataBase:
    def __init__(self, dsn: str):
        self.dsn = dsn
        self.engine = create_async_engine(dsn, echo=False)
        self.async_session: async_sessionmaker[AsyncSession] = async_sessionmaker(self.engine, expire_on_commit=False)

    async def create_tables_if_not_exist(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def disconnect(self):
        await self.engine.dispose()

    async def create_user(self,
                          telegram_id: int,
                          user_name: str = None,
                          first_name: str = None,
                          last_name: str = None):

        async with self.async_session() as session:
            async with session.begin():
                new_user = UserModel(telegram_id=telegram_id,
                                     user_name=user_name,
                                     first_name=first_name,
                                     last_name=last_name)

                session.add(new_user)

    async def get_user_by_tg_id(self, tg_id: int) -> UserModel | None:
        async with self.async_session() as session:
            query = select(UserModel).filter_by(telegram_id=tg_id)
            result = await session.execute(query)
            user = result.scalars().one_or_none()
            return user

    async def create_user_if_not_exist(self,
                                       telegram_id: int,
                                       user_name: str = None,
                                       first_name: str = None,
                                       last_name: str = None):

        with suppress(IntegrityError):
            await self.create_user(telegram_id=telegram_id,
                                   user_name=user_name,
                                   first_name=first_name,
                                   last_name=last_name)

    async def create_action(self, tg_id: int, type: int):
        user = await self.get_user_by_tg_id(tg_id)
        if user:
            async with self.async_session() as session:
                async with session.begin():
                    new_action = ActionModel(user_id=user.id, type=type)
                    session.add(new_action)

    async def update_tg_username(self, tg_id: int, new_username: str):
        async with self.async_session() as session:
            query = update(UserModel).filter_by(telegram_id=tg_id).values(user_name=new_username)
            await session.execute(query)
            await session.commit()

    async def get_all_actions_and_users_by_date(self, from_date: datetime.datetime, to_date: datetime.datetime) -> list[UserModel]:

        async with self.async_session() as session:

            query = (select(UserModel)
                     .outerjoin(UserModel.actions)
                     .options(contains_eager(UserModel.actions))
                     .where(or_(UserModel.joined_at.between(from_date, to_date),
                                ActionModel.created_at.between(from_date, to_date)))
                     .distinct())

            result = await session.execute(query)
            users = result.unique().scalars().all()

            return users

    async def get_all_users_with_count_actions(self) -> list[UserModel, int]:
        async with self.async_session() as session:
            query = select(UserModel,
                           func.count(ActionModel.id).label('actions_count')) \
                .outerjoin(ActionModel, ActionModel.user_id == UserModel.id) \
                .group_by(UserModel.id) \
                .order_by(UserModel.id)

            result = await session.execute(query)
            users = result.unique().all()
            return users

    async def get_users_with_count_actions_by_date_range(self,
                                                         from_date: datetime.datetime,  # need UTC without timezone
                                                         to_date: datetime.datetime  # need UTC without timezone
                                                         ) -> list[UserModel, int]:
        async with self.async_session() as session:
            query = select(UserModel,
                           func.count(ActionModel.id).label('actions_count')) \
                .outerjoin(ActionModel, and_(ActionModel.user_id == UserModel.id,
                                             ActionModel.created_at.between(from_date, to_date))) \
                .where(or_(UserModel.joined_at.between(from_date, to_date),
                           ActionModel.created_at.between(from_date, to_date))) \
                .group_by(UserModel.id) \
                .order_by(UserModel.id)

            result = await session.execute(query)
            users = result.unique().all()
            return users

