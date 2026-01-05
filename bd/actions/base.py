from dataclasses import dataclass
from typing import (
    Optional,
    Sequence,
    Tuple,
    TypeVar,
    TypeVarTuple,
    cast,
    Mapping
)

from fastapi import HTTPException, status
from sqlalchemy import Select
from sqlalchemy.exc import (
    IntegrityError,
    OperationalError,
    ProgrammingError,
    DBAPIError,
    TimeoutError,
)
from sqlalchemy.ext.asyncio import AsyncSession

from bd import Base

T = TypeVar("T", bound=Base)
S = TypeVar("S")
Ts = TypeVarTuple("Ts")


pgcode_to_status_and_detail: Mapping[str, Tuple[int, str]] = {
    "23502": (
        status.HTTP_400_BAD_REQUEST,
        "Missing required field",
    ),  # NOT NULL violation
    "23503": (
        status.HTTP_400_BAD_REQUEST,
        "Invalid reference to related resource",
    ),  # Foreign key violation
    "23505": (
        status.HTTP_409_CONFLICT,
        "Duplicate entry - resource already exists",
    ),  # Unique violation
    "23514": (
        status.HTTP_400_BAD_REQUEST,
        "Invalid value violates check constraint",
    ),  # Check violation
    "22001": (
        status.HTTP_400_BAD_REQUEST,
        "Data too long for column",
    ),  # String data right truncation
    "22P02": (
        status.HTTP_400_BAD_REQUEST,
        "Invalid data type",
    ),  # Invalid text representation
    "23000": (
        status.HTTP_400_BAD_REQUEST,
        "Restricted foreign key operation",
    ),  # Integrity constraint violation
    "23506": (
        status.HTTP_409_CONFLICT,
        "Restrict violation on database",
    ),  # Restrict violation
}

@dataclass
class Actions:
    """
    Базовый класс для выполнения операций с базой данных.
    Предоставляет методы для выполнения запросов и обработки ошибок.

    Attributes:
        session (AsyncSession): Асинхронная сессия SQLAlchemy для работы с базой данных.
    """

    session: AsyncSession

    async def get_scalar(self, query: Select[Tuple[S]]) -> Optional[S]:
        """
        Выполняет скалярный запрос и возвращает одно значение или None.

        Args:
            query (Select[Tuple[S]]): SQL-запрос, возвращающий одно значение.

        Returns:
            Optional[S]: Результат запроса или None, если результат не найден.

        Example:
            query = select(func.count(User.id))
            count = await actions.get_scalar(query)
        """
        return cast(Optional[S], await self.session.scalar(query))

    async def get_scalars(self, query: Select[Tuple[S]]) -> Sequence[S]:
        """
        Выполняет скалярный запрос и возвращает список значений.

        Args:
            query (Select[Tuple[S]]): SQL-запрос, возвращающий один столбец.

        Returns:
            Sequence[S]: Список результатов.

        Example:
            query = select(User.name)
            names = await actions.get_scalars(query)
        """
        result = await self.session.scalars(query)
        return result.all()

    async def get_tuple_scalars(self, query: Select[Tuple[*Ts]]) -> Sequence[Tuple[*Ts]]:
        """
        Выполняет запрос, возвращающий несколько столбцов в виде кортежей.

        Args:
            query (Select[Tuple[*Ts]]): SQL-запрос, возвращающий несколько столбцов.

        Returns:
            Sequence[Tuple[*Ts]]: Список кортежей с результатами.

        Example:
            query = select(User.id, User.name)
            rows = await actions.get_tuple_scalars(query)
            # rows = [(1, "Alice"), (2, "Bob")]
        """
        result = await self.session.execute(query)
        return [row.tuple() for row in result.all()]

    async def get_model(self, query: Select[Tuple[T]]) -> Optional[T]:
        """
        Выполняет запрос, возвращающий один экземпляр модели или None.

        Args:
            query (Select[Tuple[T]]): SQL-запрос для получения одной модели.

        Returns:
            Optional[T]: Экземпляр модели или None, если не найден.

        Example:
            query = select(User).where(User.id == 1)
            user = await actions.get_model(query)
        """
        return cast(Optional[T], await self.session.scalar(query))

    async def get_models(self, query: Select[Tuple[T]]) -> Sequence[T]:
        """
        Выполняет запрос, возвращающий список экземпляров моделей.

        Args:
            query (Select[Tuple[T]]): SQL-запрос для получения списка моделей.

        Returns:
            Sequence[T]: Список экземпляров моделей.

        Example:
            query = select(User).where(User.is_active == True)
            users = await actions.get_models(query)
        """
        result = await self.session.scalars(query)
        return cast(Sequence[T], result.all())

    async def get_tuple_models(self, query: Select[Tuple[*Ts]]) -> Sequence[Tuple[*Ts]]:
        """
        Выполняет запрос, возвращающий несколько моделей в виде кортежей.

        Args:
            query (Select[Tuple[*Ts]]): SQL-запрос для получения нескольких моделей.

        Returns:
            Sequence[Tuple[*Ts]]: Список кортежей с моделями.

        Example:
            query = select(User, Profile).join(Profile)
            results = await actions.get_tuple_models(query)
            # results = [(<User>, <Profile>), ...]
        """
        result = await self.session.execute(query)
        return [row.tuple() for row in result.all()]

    async def add(self, obj: Base) -> None:
        """
        Добавляет модель в базу данных.

        Args:
            obj (Base): Экземпляр модели для добавления.

        Example:
            await actions.add(User())
        """
        self.session.add(obj)

    async def delete(self, obj: Base) -> None:
        """
        Удаляет модель из базы данных.

        Args:
            obj (Base): Экземпляр модели для удаления.

        Example:
            await actions.delete(user)
        """
        await self.session.delete(obj)

    async def refresh(self, obj: T) -> T:
        """
        Обновляет состояние модели из базы данных.

        Args:
            obj (T): Экземпляр модели для обновления.

        Returns:
            T: Обновленный экземпляр модели.

        Example:
            user = await actions.refresh(user)
        """
        await self.session.refresh(obj)
        return obj

    async def commit(self) -> None:
        """
        Сохраняет изменения в базе данных.

        Raises:
            HTTPException: При возникновении ошибок в базе данных.

        Example:
            await actions.add(user)
            await actions.commit()
        """
        try:
            await self.session.flush()
            await self.session.commit()

        except IntegrityError as e:
            await self._handle_integrity_error(e)

        except OperationalError as e:
            await self._handle_operational_error(e)

        except (ProgrammingError, TimeoutError) as e:
            await self._handle_query_error(e)

        except Exception as e:
            await self._handle_generic_error(e)

    async def _handle_integrity_error(self, e: IntegrityError) -> None:
        """
        Обрабатывает ошибки нарушения целостности базы данных.

        Args:
            e (IntegrityError): Исключение целостности данных.

        Raises:
            HTTPException: С соответствующим статус-кодом и описанием ошибки.
        """
        await self.session.rollback()
        error_detail = "Database constraint violation"
        status_code = status.HTTP_400_BAD_REQUEST
        pgcode: Optional[str] = None

        if hasattr(e.orig, "pgcode"):
            pgcode = getattr(e.orig, "pgcode", None)
            try:
                status_code, error_detail = pgcode_to_status_and_detail[pgcode]
            except KeyError:
                status_code, error_detail = status.HTTP_400_BAD_REQUEST, "Bad request"
            except ValueError as _e:
                status_code, error_detail = status.HTTP_400_BAD_REQUEST, "Bad request"
            except Exception as _e:
                status_code, error_detail = status.HTTP_400_BAD_REQUEST, "Bad request"
        raise HTTPException(status_code=status_code, detail=error_detail)

    async def _handle_operational_error(self, e: OperationalError) -> None:
        """
        Обрабатывает операционные ошибки базы данных.

        Args:
            e (OperationalError): Операционное исключение.

        Raises:
            HTTPException: С кодом 503 и сообщением о недоступности сервиса.
        """
        await self.session.rollback()

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service unavailable",
        )

    async def _handle_query_error(self, e: DBAPIError | ProgrammingError | TimeoutError) -> None:
        """
        Обрабатывает ошибки выполнения запросов.

        Args:
            e (Union[DBAPIError, ProgrammingError, TimeoutError]): Исключение запроса.

        Raises:
            HTTPException: С кодом 400 и описанием ошибки.
        """
        await self.session.rollback()
        error_type = type(e).__name__

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Database operation failed: {error_type}",
        )

    async def _handle_generic_error(self, e: Exception) -> None:
        """
        Обрабатывает непредвиденные ошибки.

        Args:
            e (Exception): Любое непредвиденное исключение.

        Raises:
            HTTPException: С кодом 500 и сообщением о внутренней ошибке сервера.
        """
        await self.session.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )