"""
Модуль управления транзакциями DuckDB.
"""

import threading
from contextlib import contextmanager
from enum import Enum
from typing import Optional, Any, Callable, List
import duckdb

from .connection_manager import ConnectionManager


class IsolationLevel(Enum):
    """Уровни изоляции транзакций."""
    # DuckDB использует SNAPSHOT изоляцию по умолчанию
    SNAPSHOT = "SNAPSHOT"


class TransactionState(Enum):
    """Состояния транзакции."""
    PENDING = "pending"
    ACTIVE = "active"
    COMMITTED = "committed"
    ROLLED_BACK = "rolled_back"


class Transaction:
    """
    Класс для управления транзакциями DuckDB.
    
    Поддерживает явное управление транзакциями с возможностью
    commit и rollback операций.
    """
    
    def __init__(
        self,
        connection: duckdb.DuckDBPyConnection,
        auto_commit: bool = False
    ):
        """
        Инициализация транзакции.
        
        Args:
            connection: Соединение DuckDB
            auto_commit: Автоматический коммит после каждой операции
        """
        self._connection = connection
        self._auto_commit = auto_commit
        self._state = TransactionState.PENDING
        self._lock = threading.Lock()
        self._savepoints: List[str] = []
        self._savepoint_counter = 0
    
    def begin(self) -> "Transaction":
        """
        Начинает транзакцию.
        
        Returns:
            self для цепочки вызовов
        """
        with self._lock:
            if self._state != TransactionState.PENDING:
                raise RuntimeError(f"Невозможно начать транзакцию в состоянии {self._state}")
            
            self._connection.execute("BEGIN TRANSACTION")
            self._state = TransactionState.ACTIVE
            return self
    
    def commit(self) -> None:
        """Фиксирует транзакцию."""
        with self._lock:
            if self._state != TransactionState.ACTIVE:
                raise RuntimeError(f"Невозможно зафиксировать транзакцию в состоянии {self._state}")
            
            self._connection.execute("COMMIT")
            self._state = TransactionState.COMMITTED
            self._savepoints.clear()
    
    def rollback(self, to_savepoint: Optional[str] = None) -> None:
        """
        Откатывает транзакцию.
        
        Args:
            to_savepoint: Имя savepoint для частичного отката
        """
        with self._lock:
            if self._state != TransactionState.ACTIVE:
                raise RuntimeError(f"Невозможно откатить транзакцию в состоянии {self._state}")
            
            if to_savepoint:
                if to_savepoint not in self._savepoints:
                    raise ValueError(f"Savepoint '{to_savepoint}' не найден")
                self._connection.execute(f"ROLLBACK TO SAVEPOINT {to_savepoint}")
                # Удаляем savepoints после точки отката
                idx = self._savepoints.index(to_savepoint)
                self._savepoints = self._savepoints[:idx + 1]
            else:
                self._connection.execute("ROLLBACK")
                self._state = TransactionState.ROLLED_BACK
                self._savepoints.clear()
    
    def savepoint(self, name: Optional[str] = None) -> str:
        """
        Создаёт savepoint.
        
        Args:
            name: Имя savepoint (генерируется автоматически если не указано)
            
        Returns:
            Имя созданного savepoint
        """
        with self._lock:
            if self._state != TransactionState.ACTIVE:
                raise RuntimeError(f"Невозможно создать savepoint в состоянии {self._state}")
            
            if name is None:
                self._savepoint_counter += 1
                name = f"sp_{self._savepoint_counter}"
            
            self._connection.execute(f"SAVEPOINT {name}")
            self._savepoints.append(name)
            return name
    
    def release_savepoint(self, name: str) -> None:
        """
        Освобождает savepoint.
        
        Args:
            name: Имя savepoint для освобождения
        """
        with self._lock:
            if self._state != TransactionState.ACTIVE:
                raise RuntimeError(f"Невозможно освободить savepoint в состоянии {self._state}")
            
            if name not in self._savepoints:
                raise ValueError(f"Savepoint '{name}' не найден")
            
            self._connection.execute(f"RELEASE SAVEPOINT {name}")
            self._savepoints.remove(name)
    
    def execute(self, query: str, parameters: Optional[Any] = None) -> duckdb.DuckDBPyRelation:
        """
        Выполняет запрос в контексте транзакции.
        
        Args:
            query: SQL запрос
            parameters: Параметры запроса
            
        Returns:
            Результат запроса
        """
        with self._lock:
            if self._state not in (TransactionState.PENDING, TransactionState.ACTIVE):
                raise RuntimeError(f"Невозможно выполнить запрос в состоянии {self._state}")
            
            # Автоматически начинаем транзакцию при первом запросе
            if self._state == TransactionState.PENDING:
                self._connection.execute("BEGIN TRANSACTION")
                self._state = TransactionState.ACTIVE
            
            if parameters:
                result = self._connection.execute(query, parameters)
            else:
                result = self._connection.execute(query)
            
            if self._auto_commit:
                self.commit()
            
            return result
    
    def fetchall(self, query: str, parameters: Optional[Any] = None) -> List[tuple]:
        """
        Выполняет запрос и возвращает все результаты.
        
        Args:
            query: SQL запрос
            parameters: Параметры запроса
            
        Returns:
            Список кортежей с результатами
        """
        result = self.execute(query, parameters)
        return result.fetchall()
    
    def fetchone(self, query: str, parameters: Optional[Any] = None) -> Optional[tuple]:
        """
        Выполняет запрос и возвращает первую строку.
        
        Args:
            query: SQL запрос
            parameters: Параметры запроса
            
        Returns:
            Кортеж с результатом или None
        """
        result = self.execute(query, parameters)
        return result.fetchone()
    
    @property
    def state(self) -> TransactionState:
        """Текущее состояние транзакции."""
        return self._state
    
    @property
    def is_active(self) -> bool:
        """Активна ли транзакция."""
        return self._state == TransactionState.ACTIVE
    
    @property
    def connection(self) -> duckdb.DuckDBPyConnection:
        """Соединение транзакции."""
        return self._connection


class TransactionContext:
    """
    Контекстный менеджер для автоматического управления транзакциями.
    
    Автоматически выполняет commit при успешном завершении
    и rollback при возникновении исключения.
    """
    
    def __init__(
        self,
        connection_manager: ConnectionManager,
        auto_begin: bool = True,
        on_commit: Optional[Callable[[], None]] = None,
        on_rollback: Optional[Callable[[Exception], None]] = None
    ):
        """
        Инициализация контекста транзакции.
        
        Args:
            connection_manager: Менеджер соединений
            auto_begin: Автоматически начинать транзакцию
            on_commit: Callback при успешном коммите
            on_rollback: Callback при откате
        """
        self._connection_manager = connection_manager
        self._auto_begin = auto_begin
        self._on_commit = on_commit
        self._on_rollback = on_rollback
        self._connection: Optional[duckdb.DuckDBPyConnection] = None
        self._transaction: Optional[Transaction] = None
    
    def __enter__(self) -> Transaction:
        self._connection = self._connection_manager.get_connection()
        self._transaction = Transaction(self._connection)
        
        if self._auto_begin:
            self._transaction.begin()
        
        return self._transaction
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type is None:
                # Успешное завершение - коммитим
                if self._transaction and self._transaction.is_active:
                    self._transaction.commit()
                    if self._on_commit:
                        self._on_commit()
            else:
                # Ошибка - откатываем
                if self._transaction and self._transaction.is_active:
                    self._transaction.rollback()
                    if self._on_rollback:
                        self._on_rollback(exc_val)
        finally:
            # Возвращаем соединение в пул
            if self._connection:
                self._connection_manager.release_connection(self._connection)
        
        return False  # Не подавляем исключения


@contextmanager
def transaction(
    connection_manager: ConnectionManager,
    auto_begin: bool = True
):
    """
    Функция-хелпер для создания транзакции.
    
    Args:
        connection_manager: Менеджер соединений
        auto_begin: Автоматически начинать транзакцию
        
    Yields:
        Объект транзакции
        
    Example:
        with transaction(conn_manager) as tx:
            tx.execute("INSERT INTO users VALUES (?, ?)", (1, "John"))
            tx.execute("INSERT INTO orders VALUES (?, ?)", (1, 100))
    """
    ctx = TransactionContext(connection_manager, auto_begin=auto_begin)
    with ctx as tx:
        yield tx


