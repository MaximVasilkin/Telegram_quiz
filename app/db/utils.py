from contextlib import suppress
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
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

