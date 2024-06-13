import datetime
from typing import List
from typing import Annotated
from sqlalchemy import ForeignKey, String, Integer, BigInteger, text
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


intpk = Annotated[int, mapped_column(primary_key=True, index=True)]
created_at = Annotated[datetime.datetime, mapped_column(server_default=text("TIMEZONE('utc', now())"), index=True)]


class Base(AsyncAttrs, DeclarativeBase):
    pass


class UserModel(Base):
    __tablename__ = 'users'

    id: Mapped[intpk]
    telegram_id: Mapped[int] = mapped_column(BigInteger(), nullable=False, unique=True, index=True)
    user_name: Mapped[str] = mapped_column(String(250), nullable=True)
    first_name: Mapped[str] = mapped_column(String(250), nullable=True)
    last_name: Mapped[str] = mapped_column(String(250), nullable=True)
    joined_at: Mapped[created_at]

    actions: Mapped[List['ActionModel']] = relationship(back_populates='user',
                                                        cascade='all, delete-orphan')


class ActionModel(Base):
    __tablename__ = 'actions'

    id: Mapped[intpk]
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True)

    type: Mapped[str] = mapped_column(Integer(), nullable=False)
    created_at: Mapped[created_at]

    user: Mapped['UserModel'] = relationship(back_populates='actions')
