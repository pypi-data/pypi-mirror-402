"""
Менеджер соединений для DuckDB с поддержкой пула соединений.
"""

import threading
from contextlib import contextmanager
from queue import Queue, Empty
from typing import Optional, Any
import duckdb


class ConnectionManager:
    """
    Менеджер пула соединений DuckDB для конкурентных операций.
    
    DuckDB поддерживает несколько соединений к одной базе данных,
    но каждое соединение должно использоваться только одним потоком.
    """
    
    def __init__(
        self,
        database: str = ":memory:",
        pool_size: int = 5,
        read_only: bool = False,
        config: Optional[dict] = None
    ):
        """
        Инициализация менеджера соединений.
        
        Args:
            database: Путь к файлу базы данных или ":memory:" для in-memory БД
            pool_size: Размер пула соединений
            read_only: Режим только для чтения
            config: Дополнительная конфигурация DuckDB
        """
        self._database = database
        self._pool_size = pool_size
        self._read_only = read_only
        self._config = config or {}
        
        self._pool: Queue[duckdb.DuckDBPyConnection] = Queue(maxsize=pool_size)
        self._lock = threading.Lock()
        self._connections_created = 0
        self._closed = False
        
        # Создаём основное соединение для инициализации БД
        self._main_connection = self._create_connection()
    
    def _create_connection(self) -> duckdb.DuckDBPyConnection:
        """Создаёт новое соединение с DuckDB."""
        conn = duckdb.connect(
            database=self._database,
            read_only=self._read_only,
            config=self._config
        )
        return conn
    
    def get_connection(self, timeout: Optional[float] = None) -> duckdb.DuckDBPyConnection:
        """
        Получает соединение из пула.
        
        Args:
            timeout: Таймаут ожидания свободного соединения
            
        Returns:
            Соединение DuckDB
            
        Raises:
            RuntimeError: Если менеджер закрыт
            Empty: Если таймаут истёк
        """
        if self._closed:
            raise RuntimeError("ConnectionManager закрыт")
        
        # Пытаемся получить соединение из пула
        try:
            return self._pool.get(block=False)
        except Empty:
            pass
        
        # Создаём новое соединение, если лимит не достигнут
        with self._lock:
            if self._connections_created < self._pool_size:
                self._connections_created += 1
                return self._create_connection()
        
        # Ждём освобождения соединения
        return self._pool.get(block=True, timeout=timeout)
    
    def release_connection(self, conn: duckdb.DuckDBPyConnection) -> None:
        """
        Возвращает соединение в пул.
        
        Args:
            conn: Соединение для возврата
        """
        if self._closed:
            try:
                conn.close()
            except Exception:
                pass
            return
        
        try:
            self._pool.put_nowait(conn)
        except Exception:
            # Пул переполнен, закрываем соединение
            try:
                conn.close()
            except Exception:
                pass
    
    @contextmanager
    def connection(self, timeout: Optional[float] = None):
        """
        Контекстный менеджер для работы с соединением.
        
        Args:
            timeout: Таймаут ожидания соединения
            
        Yields:
            Соединение DuckDB
        """
        conn = self.get_connection(timeout=timeout)
        try:
            yield conn
        finally:
            self.release_connection(conn)
    
    def execute(self, query: str, parameters: Optional[Any] = None) -> duckdb.DuckDBPyRelation:
        """
        Выполняет запрос используя соединение из пула.
        
        Args:
            query: SQL запрос
            parameters: Параметры запроса
            
        Returns:
            Результат запроса
        """
        with self.connection() as conn:
            if parameters:
                return conn.execute(query, parameters)
            return conn.execute(query)
    
    def close(self) -> None:
        """Закрывает все соединения и менеджер."""
        self._closed = True
        
        # Закрываем основное соединение
        try:
            self._main_connection.close()
        except Exception:
            pass
        
        # Закрываем все соединения в пуле
        while True:
            try:
                conn = self._pool.get_nowait()
                try:
                    conn.close()
                except Exception:
                    pass
            except Empty:
                break
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False
    
    @property
    def database(self) -> str:
        """Путь к базе данных."""
        return self._database
    
    @property
    def pool_size(self) -> int:
        """Размер пула соединений."""
        return self._pool_size
    
    @property
    def active_connections(self) -> int:
        """Количество созданных соединений."""
        return self._connections_created


