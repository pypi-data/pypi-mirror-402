"""
Основной движок DuckPTE для работы с DuckDB.
"""

import threading
from concurrent.futures import ThreadPoolExecutor, Future
from typing import Optional, Any, List, Dict, Callable, Union
from contextlib import contextmanager
import duckdb

from .connection_manager import ConnectionManager
from .transaction import Transaction, TransactionContext, transaction


class DuckPTEngine:
    """
    Основной движок для работы с DuckDB с поддержкой
    транзакций и конкурентных операций.
    
    Предоставляет высокоуровневый API для:
    - Выполнения запросов
    - Управления транзакциями
    - Параллельного выполнения операций
    - Пакетной обработки данных
    """
    
    def __init__(
        self,
        database: str = ":memory:",
        pool_size: int = 5,
        max_workers: int = 4,
        read_only: bool = False,
        config: Optional[dict] = None
    ):
        """
        Инициализация движка.
        
        Args:
            database: Путь к файлу базы данных или ":memory:"
            pool_size: Размер пула соединений
            max_workers: Максимальное количество рабочих потоков
            read_only: Режим только для чтения
            config: Дополнительная конфигурация DuckDB
        """
        self._connection_manager = ConnectionManager(
            database=database,
            pool_size=pool_size,
            read_only=read_only,
            config=config
        )
        self._max_workers = max_workers
        self._executor: Optional[ThreadPoolExecutor] = None
        self._lock = threading.Lock()
        self._closed = False
    
    def _get_executor(self) -> ThreadPoolExecutor:
        """Получает или создаёт пул потоков."""
        if self._executor is None:
            with self._lock:
                if self._executor is None:
                    self._executor = ThreadPoolExecutor(max_workers=self._max_workers)
        return self._executor
    
    # ==================== Базовые операции ====================
    
    def execute(self, query: str, parameters: Optional[Any] = None) -> duckdb.DuckDBPyRelation:
        """
        Выполняет SQL запрос.
        
        Args:
            query: SQL запрос
            parameters: Параметры запроса
            
        Returns:
            Результат запроса
        """
        return self._connection_manager.execute(query, parameters)
    
    def fetchall(self, query: str, parameters: Optional[Any] = None) -> List[tuple]:
        """
        Выполняет запрос и возвращает все результаты.
        
        Args:
            query: SQL запрос
            parameters: Параметры запроса
            
        Returns:
            Список кортежей с результатами
        """
        with self._connection_manager.connection() as conn:
            if parameters:
                result = conn.execute(query, parameters)
            else:
                result = conn.execute(query)
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
        with self._connection_manager.connection() as conn:
            if parameters:
                result = conn.execute(query, parameters)
            else:
                result = conn.execute(query)
            return result.fetchone()
    
    def fetchdf(self, query: str, parameters: Optional[Any] = None):
        """
        Выполняет запрос и возвращает результат как pandas DataFrame.
        
        Args:
            query: SQL запрос
            parameters: Параметры запроса
            
        Returns:
            pandas DataFrame с результатами
        """
        with self._connection_manager.connection() as conn:
            if parameters:
                result = conn.execute(query, parameters)
            else:
                result = conn.execute(query)
            return result.fetchdf()
    
    # ==================== Транзакции ====================
    
    @contextmanager
    def transaction(self, auto_begin: bool = True):
        """
        Создаёт контекст транзакции.
        
        Args:
            auto_begin: Автоматически начинать транзакцию
            
        Yields:
            Объект транзакции
            
        Example:
            with engine.transaction() as tx:
                tx.execute("INSERT INTO users VALUES (?, ?)", (1, "John"))
                tx.execute("UPDATE accounts SET balance = balance - 100 WHERE user_id = ?", (1,))
        """
        with transaction(self._connection_manager, auto_begin=auto_begin) as tx:
            yield tx
    
    def begin_transaction(self) -> Transaction:
        """
        Создаёт и начинает новую транзакцию.
        
        ВАЖНО: Вызывающий код отвечает за вызов commit() или rollback()
        и возврат соединения в пул.
        
        Returns:
            Объект транзакции
        """
        conn = self._connection_manager.get_connection()
        tx = Transaction(conn)
        tx.begin()
        return tx
    
    def commit_transaction(self, tx: Transaction) -> None:
        """
        Фиксирует транзакцию и возвращает соединение в пул.
        
        Args:
            tx: Транзакция для фиксации
        """
        try:
            tx.commit()
        finally:
            self._connection_manager.release_connection(tx.connection)
    
    def rollback_transaction(self, tx: Transaction) -> None:
        """
        Откатывает транзакцию и возвращает соединение в пул.
        
        Args:
            tx: Транзакция для отката
        """
        try:
            tx.rollback()
        finally:
            self._connection_manager.release_connection(tx.connection)
    
    # ==================== Конкурентные операции ====================
    
    def execute_async(
        self,
        query: str,
        parameters: Optional[Any] = None
    ) -> Future:
        """
        Асинхронно выполняет запрос.
        
        Args:
            query: SQL запрос
            parameters: Параметры запроса
            
        Returns:
            Future с результатом
        """
        def _execute():
            with self._connection_manager.connection() as conn:
                if parameters:
                    return conn.execute(query, parameters).fetchall()
                return conn.execute(query).fetchall()
        
        return self._get_executor().submit(_execute)
    
    def execute_many_async(
        self,
        queries: List[tuple]
    ) -> List[Future]:
        """
        Асинхронно выполняет несколько запросов.
        
        Args:
            queries: Список кортежей (query, parameters)
            
        Returns:
            Список Future с результатами
        """
        futures = []
        for query_tuple in queries:
            if len(query_tuple) == 2:
                query, params = query_tuple
            else:
                query, params = query_tuple[0], None
            futures.append(self.execute_async(query, params))
        return futures
    
    def execute_parallel(
        self,
        operations: List[Callable[["DuckPTEngine"], Any]]
    ) -> List[Any]:
        """
        Выполняет операции параллельно.
        
        Args:
            operations: Список функций, принимающих engine
            
        Returns:
            Список результатов
            
        Example:
            results = engine.execute_parallel([
                lambda e: e.fetchall("SELECT * FROM users WHERE age > 30"),
                lambda e: e.fetchall("SELECT * FROM orders WHERE amount > 1000"),
            ])
        """
        executor = self._get_executor()
        futures = [executor.submit(op, self) for op in operations]
        return [f.result() for f in futures]
    
    def batch_execute(
        self,
        query: str,
        batch_data: List[tuple],
        batch_size: int = 1000,
        use_transaction: bool = True
    ) -> int:
        """
        Выполняет пакетную вставку данных.
        
        Args:
            query: SQL запрос с плейсхолдерами
            batch_data: Список кортежей с данными
            batch_size: Размер пакета
            use_transaction: Использовать транзакцию для каждого пакета
            
        Returns:
            Количество обработанных записей
        """
        total_processed = 0
        
        for i in range(0, len(batch_data), batch_size):
            batch = batch_data[i:i + batch_size]
            
            if use_transaction:
                with self.transaction() as tx:
                    for params in batch:
                        tx.execute(query, params)
                    total_processed += len(batch)
            else:
                with self._connection_manager.connection() as conn:
                    for params in batch:
                        conn.execute(query, params)
                    total_processed += len(batch)
        
        return total_processed
    
    def batch_execute_parallel(
        self,
        query: str,
        batch_data: List[tuple],
        batch_size: int = 1000,
        num_workers: Optional[int] = None
    ) -> int:
        """
        Выполняет пакетную вставку данных параллельно.
        
        Args:
            query: SQL запрос с плейсхолдерами
            batch_data: Список кортежей с данными
            batch_size: Размер пакета
            num_workers: Количество рабочих потоков
            
        Returns:
            Количество обработанных записей
        """
        if num_workers is None:
            num_workers = self._max_workers
        
        # Разбиваем данные на пакеты
        batches = [
            batch_data[i:i + batch_size]
            for i in range(0, len(batch_data), batch_size)
        ]
        
        def process_batch(batch: List[tuple]) -> int:
            with self.transaction() as tx:
                for params in batch:
                    tx.execute(query, params)
            return len(batch)
        
        executor = self._get_executor()
        futures = [executor.submit(process_batch, batch) for batch in batches]
        
        return sum(f.result() for f in futures)
    
    # ==================== Утилиты ====================
    
    def table_exists(self, table_name: str, schema: str = "main") -> bool:
        """
        Проверяет существование таблицы.
        
        Args:
            table_name: Имя таблицы
            schema: Схема базы данных
            
        Returns:
            True если таблица существует
        """
        result = self.fetchone(
            """
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = ? AND table_name = ?
            """,
            (schema, table_name)
        )
        return result[0] > 0 if result else False
    
    def get_table_info(self, table_name: str) -> List[Dict[str, Any]]:
        """
        Получает информацию о структуре таблицы.
        
        Args:
            table_name: Имя таблицы
            
        Returns:
            Список словарей с информацией о колонках
        """
        result = self.fetchall(f"DESCRIBE {table_name}")
        columns = ["column_name", "column_type", "null", "key", "default", "extra"]
        return [dict(zip(columns, row)) for row in result]
    
    def create_table_from_df(self, table_name: str, df, if_not_exists: bool = True) -> None:
        """
        Создаёт таблицу из pandas DataFrame.
        
        Args:
            table_name: Имя таблицы
            df: pandas DataFrame
            if_not_exists: Не выбрасывать ошибку если таблица существует
        """
        with self._connection_manager.connection() as conn:
            conn.register("temp_df", df)
            exists_clause = "IF NOT EXISTS " if if_not_exists else ""
            conn.execute(f"CREATE TABLE {exists_clause}{table_name} AS SELECT * FROM temp_df")
            conn.unregister("temp_df")
    
    def insert_df(self, table_name: str, df, use_transaction: bool = True) -> int:
        """
        Вставляет данные из pandas DataFrame в таблицу.
        
        Args:
            table_name: Имя таблицы
            df: pandas DataFrame
            use_transaction: Использовать транзакцию
            
        Returns:
            Количество вставленных строк
        """
        if use_transaction:
            with self.transaction() as tx:
                tx.connection.register("temp_df", df)
                tx.execute(f"INSERT INTO {table_name} SELECT * FROM temp_df")
                tx.connection.unregister("temp_df")
        else:
            with self._connection_manager.connection() as conn:
                conn.register("temp_df", df)
                conn.execute(f"INSERT INTO {table_name} SELECT * FROM temp_df")
                conn.unregister("temp_df")
        
        return len(df)
    
    # ==================== Управление ресурсами ====================
    
    @property
    def connection_manager(self) -> ConnectionManager:
        """Возвращает менеджер соединений."""
        return self._connection_manager
    
    @property
    def database(self) -> str:
        """Путь к базе данных."""
        return self._connection_manager.database
    
    def close(self) -> None:
        """Закрывает движок и освобождает ресурсы."""
        self._closed = True
        
        if self._executor:
            self._executor.shutdown(wait=True)
            self._executor = None
        
        self._connection_manager.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False


