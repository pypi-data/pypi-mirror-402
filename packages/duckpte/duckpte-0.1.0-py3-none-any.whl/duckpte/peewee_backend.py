"""
Peewee ORM адаптер для DuckDB.

Позволяет использовать DuckDB с Peewee ORM интерфейсом.
Поддерживает конкурентный доступ из нескольких процессов через файловую блокировку.
"""

import os
import re
import time
import fcntl
import threading
from contextlib import contextmanager
from typing import Any, Optional, List, Tuple, Iterator, Sequence
import duckdb

from peewee import (
    Database,
    ColumnMetadata,
    ForeignKeyMetadata,
    IndexMetadata,
    SQL,
    NodeList,
)


class FileLock:
    """
    Файловая блокировка для межпроцессной синхронизации.
    Работает как блокировка SQLite.
    """
    
    def __init__(self, lock_file: str, timeout: float = 30.0, retry_delay: float = 0.1):
        """
        Args:
            lock_file: Путь к файлу блокировки
            timeout: Таймаут ожидания блокировки в секундах
            retry_delay: Задержка между попытками захвата блокировки
        """
        self._lock_file = lock_file
        self._timeout = timeout
        self._retry_delay = retry_delay
        self._fd: Optional[int] = None
    
    def acquire(self) -> bool:
        """Захватывает блокировку."""
        start_time = time.time()
        
        # Создаём директорию для lock файла если нужно
        lock_dir = os.path.dirname(self._lock_file)
        if lock_dir and not os.path.exists(lock_dir):
            os.makedirs(lock_dir, exist_ok=True)
        
        self._fd = os.open(self._lock_file, os.O_RDWR | os.O_CREAT)
        
        while True:
            try:
                fcntl.flock(self._fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                return True
            except (IOError, OSError):
                if time.time() - start_time >= self._timeout:
                    os.close(self._fd)
                    self._fd = None
                    raise TimeoutError(f"Не удалось получить блокировку за {self._timeout} секунд")
                time.sleep(self._retry_delay)
    
    def release(self) -> None:
        """Освобождает блокировку."""
        if self._fd is not None:
            fcntl.flock(self._fd, fcntl.LOCK_UN)
            os.close(self._fd)
            self._fd = None
    
    def __enter__(self):
        self.acquire()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()
        return False


class DuckDBDatabase(Database):
    """
    Peewee Database адаптер для DuckDB с поддержкой конкурентного доступа.
    
    Каждая операция выполняется атомарно:
    1. Захват файловой блокировки
    2. Подключение к базе
    3. Выполнение запроса
    4. Отключение от базы
    5. Освобождение блокировки
    
    Это позволяет безопасно работать с базой из нескольких процессов,
    как это делает SQLite.
    
    Example:
        db = DuckDBDatabase('my_database.db')
        
        class User(Model):
            name = CharField()
            email = CharField()
            
            class Meta:
                database = db
        
        db.create_tables([User])
        User.create(name='Иван', email='ivan@example.com')
    """
    
    # Маппинг типов Peewee -> DuckDB
    field_types = {
        'AUTO': 'INTEGER',
        'BIGAUTO': 'BIGINT',
        'BIGINT': 'BIGINT',
        'BLOB': 'BLOB',
        'BOOL': 'BOOLEAN',
        'CHAR': 'VARCHAR',
        'DATE': 'DATE',
        'DATETIME': 'TIMESTAMP',
        'DECIMAL': 'DECIMAL',
        'DEFAULT': '',
        'DOUBLE': 'DOUBLE',
        'FLOAT': 'REAL',
        'INT': 'INTEGER',
        'SMALLINT': 'SMALLINT',
        'TEXT': 'TEXT',
        'TIME': 'TIME',
        'UUID': 'UUID',
        'UUIDB': 'BLOB',
        'VARCHAR': 'VARCHAR',
    }
    
    operations = {
        'LIKE': 'LIKE',
        'ILIKE': 'ILIKE',
        'REGEXP': '~',
    }
    
    returning_clause = True
    
    def __init__(
        self,
        database: str = ':memory:',
        timeout: float = 30.0,
        read_only: bool = False,
        config: Optional[dict] = None,
        pragmas: Optional[dict] = None,
        **kwargs
    ):
        """
        Инициализация DuckDB Database.
        
        Args:
            database: Путь к файлу БД или ':memory:'
            timeout: Таймаут ожидания блокировки в секундах
            read_only: Режим только для чтения
            config: Дополнительная конфигурация DuckDB
            pragmas: Pragmas (для совместимости)
            **kwargs: Дополнительные параметры для Peewee Database
        """
        self._database_path = database
        self._timeout = timeout
        self._read_only = read_only
        self._config = config or {}
        self._lock_file = f"{database}.lock" if database != ':memory:' else None
        self._thread_lock = threading.RLock()
        self._sequences: dict = {}
        self._pragmas = pragmas or {}
        self._in_transaction = False
        self._transaction_conn: Optional[duckdb.DuckDBPyConnection] = None
        self._current_lock: Optional[FileLock] = None
        
        # Вызываем конструктор Database
        super().__init__(database, **kwargs)
    
    def _get_lock(self) -> Optional[FileLock]:
        """Возвращает файловую блокировку или None для in-memory БД."""
        if self._lock_file:
            return FileLock(self._lock_file, timeout=self._timeout)
        return None
    
    @contextmanager
    def _atomic_connection(self):
        """
        Контекстный менеджер для атомарного подключения.
        Захватывает блокировку, подключается, выполняет операцию, отключается.
        """
        # Если уже в транзакции, используем существующее соединение
        if self._in_transaction and self._transaction_conn:
            yield self._transaction_conn
            return
        
        lock = self._get_lock()
        conn = None
        
        try:
            # Захватываем блокировку (если не in-memory)
            if lock:
                lock.acquire()
            
            # Подключаемся
            conn = duckdb.connect(
                database=self._database_path,
                read_only=self._read_only,
                config=self._config
            )
            
            yield conn
            
        finally:
            # Закрываем соединение
            if conn and not self._in_transaction:
                try:
                    conn.close()
                except Exception:
                    pass
            
            # Освобождаем блокировку
            if lock:
                lock.release()
    
    def _get_sequence_name(self, table_name: str) -> str:
        """Генерирует имя последовательности для таблицы."""
        return f"{table_name}_id_seq"
    
    def _ensure_sequence(self, conn: duckdb.DuckDBPyConnection, table_name: str) -> None:
        """Создаёт последовательность для таблицы, если её нет."""
        seq_name = self._get_sequence_name(table_name)
        try:
            conn.execute(f'CREATE SEQUENCE IF NOT EXISTS "{seq_name}" START 1')
        except Exception:
            pass
    
    def _process_insert_sql(self, sql: str, table_name: str) -> str:
        """Обрабатывает INSERT SQL для добавления nextval для id."""
        seq_name = self._get_sequence_name(table_name)
        
        columns_match = re.search(r'INSERT INTO "[^"]+"\s*\(([^)]*)\)\s*VALUES', sql, re.IGNORECASE)
        
        if columns_match:
            columns_part = columns_match.group(1)
            if '"id"' not in columns_part.lower():
                match = re.match(
                    r'(INSERT INTO "[^"]+"\s*)\(([^)]*)\)\s*VALUES\s*\(([^)]*)\)(.*)',
                    sql,
                    re.IGNORECASE | re.DOTALL
                )
                if match:
                    prefix = match.group(1)
                    columns = match.group(2)
                    values = match.group(3)
                    suffix = match.group(4)
                    
                    return f'{prefix}("id", {columns}) VALUES (nextval(\'{seq_name}\'), {values}){suffix}'
        
        return sql
    
    def connect(self, reuse_if_open: bool = False):
        """Подключение не требуется - соединения создаются атомарно."""
        return self
    
    def close(self) -> bool:
        """Закрытие не требуется - соединения закрываются автоматически."""
        if self._transaction_conn:
            try:
                self._transaction_conn.close()
            except Exception:
                pass
            self._transaction_conn = None
        return True
    
    def is_closed(self) -> bool:
        """Всегда возвращает False для совместимости с Peewee."""
        return False
    
    def connection(self) -> duckdb.DuckDBPyConnection:
        """Возвращает соединение (для транзакций)."""
        if self._transaction_conn:
            return self._transaction_conn
        raise RuntimeError("Нет активного соединения. Используйте execute_sql или atomic().")
    
    def cursor(self, commit: bool = False) -> 'DuckDBCursor':
        """Создаёт курсор."""
        if self._transaction_conn:
            return DuckDBCursor(self._transaction_conn, commit)
        raise RuntimeError("Нет активного соединения.")
    
    def execute_sql(
        self,
        sql: str,
        params: Optional[Sequence] = None,
        commit: bool = True
    ) -> 'DuckDBCursor':
        """
        Выполняет SQL запрос атомарно.
        
        Каждый вызов:
        1. Захватывает блокировку
        2. Подключается к базе
        3. Выполняет запрос
        4. Отключается
        5. Освобождает блокировку
        """
        with self._atomic_connection() as conn:
            # Обрабатываем INSERT для автоинкремента
            if sql.strip().upper().startswith('INSERT INTO'):
                match = re.search(r'INSERT INTO "?(\w+)"?', sql, re.IGNORECASE)
                if match:
                    table_name = match.group(1)
                    self._ensure_sequence(conn, table_name)
                    sql = self._process_insert_sql(sql, table_name)
            
            cursor = DuckDBCursor(conn, commit)
            cursor.execute(sql, params or ())
            return cursor
    
    def begin(self) -> None:
        """Начинает транзакцию."""
        if self._in_transaction:
            return
        
        lock = self._get_lock()
        if lock:
            lock.acquire()
            self._current_lock = lock
        
        self._transaction_conn = duckdb.connect(
            database=self._database_path,
            read_only=self._read_only,
            config=self._config
        )
        self._transaction_conn.execute('BEGIN TRANSACTION')
        self._in_transaction = True
    
    def commit(self) -> None:
        """Фиксирует транзакцию."""
        if not self._in_transaction:
            return
        
        try:
            if self._transaction_conn:
                self._transaction_conn.execute('COMMIT')
        finally:
            self._cleanup_transaction()
    
    def rollback(self) -> None:
        """Откатывает транзакцию."""
        if not self._in_transaction:
            return
        
        try:
            if self._transaction_conn:
                self._transaction_conn.execute('ROLLBACK')
        finally:
            self._cleanup_transaction()
    
    def _cleanup_transaction(self) -> None:
        """Очищает ресурсы транзакции."""
        if self._transaction_conn:
            try:
                self._transaction_conn.close()
            except Exception:
                pass
            self._transaction_conn = None
        
        if hasattr(self, '_current_lock') and self._current_lock:
            self._current_lock.release()
            self._current_lock = None
        
        self._in_transaction = False
    
    @contextmanager
    def atomic(self, *args, **kwargs):
        """
        Контекстный менеджер для транзакций.
        Блокировка держится на всё время транзакции.
        """
        self.begin()
        try:
            yield
            self.commit()
        except Exception:
            self.rollback()
            raise
    
    def get_tables(self, schema: Optional[str] = None) -> List[str]:
        """Получает список таблиц."""
        schema = schema or 'main'
        cursor = self.execute_sql(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = ? AND table_type = 'BASE TABLE'",
            (schema,)
        )
        return [row[0] for row in cursor.fetchall()]
    
    def get_columns(
        self,
        table: str,
        schema: Optional[str] = None
    ) -> List[ColumnMetadata]:
        """Получает информацию о колонках таблицы."""
        schema = schema or 'main'
        cursor = self.execute_sql(
            "SELECT column_name, data_type, is_nullable, column_default "
            "FROM information_schema.columns "
            "WHERE table_schema = ? AND table_name = ? "
            "ORDER BY ordinal_position",
            (schema, table)
        )
        
        columns = []
        for row in cursor.fetchall():
            columns.append(ColumnMetadata(
                name=row[0],
                data_type=row[1],
                null=row[2] == 'YES',
                primary_key=False,
                table=table,
                default=row[3]
            ))
        return columns
    
    def get_primary_keys(self, table: str, schema: Optional[str] = None) -> List[str]:
        """Получает первичные ключи таблицы."""
        cursor = self.execute_sql(f'PRAGMA table_info("{table}")')
        return [row[1] for row in cursor.fetchall() if row[5]]
    
    def get_foreign_keys(self, table: str, schema: Optional[str] = None) -> List[ForeignKeyMetadata]:
        """Получает внешние ключи таблицы."""
        try:
            cursor = self.execute_sql(f'PRAGMA foreign_key_list("{table}")')
            fks = []
            for row in cursor.fetchall():
                fks.append(ForeignKeyMetadata(
                    column=row[3],
                    dest_table=row[2],
                    dest_column=row[4],
                    table=table
                ))
            return fks
        except Exception:
            return []
    
    def get_indexes(self, table: str, schema: Optional[str] = None) -> List[IndexMetadata]:
        """Получает индексы таблицы."""
        try:
            cursor = self.execute_sql(f'PRAGMA index_list("{table}")')
            indexes = []
            for row in cursor.fetchall():
                index_name = row[1]
                unique = bool(row[2])
                
                col_cursor = self.execute_sql(f'PRAGMA index_info("{index_name}")')
                columns = [col_row[2] for col_row in col_cursor.fetchall()]
                
                indexes.append(IndexMetadata(
                    name=index_name,
                    sql='',
                    columns=columns,
                    unique=unique,
                    table=table
                ))
            return indexes
        except Exception:
            return []
    
    def sequence_exists(self, seq: str) -> bool:
        """Проверяет существование последовательности."""
        try:
            cursor = self.execute_sql(
                "SELECT 1 FROM duckdb_sequences() WHERE sequence_name = ?",
                (seq,)
            )
            return cursor.fetchone() is not None
        except Exception:
            return False
    
    def last_insert_id(self, cursor, query_type: Optional[str] = None) -> int:
        """Получает ID последней вставленной записи."""
        if hasattr(cursor, 'lastrowid'):
            return cursor.lastrowid if cursor.lastrowid else 0
        if hasattr(cursor, 'cursor') and hasattr(cursor.cursor, 'lastrowid'):
            return cursor.cursor.lastrowid if cursor.cursor.lastrowid else 0
        return 0
    
    def rows_affected(self, cursor: 'DuckDBCursor') -> int:
        """Получает количество затронутых строк."""
        return cursor.rowcount
    
    def extract_date(self, date_part: str, date_field: Any) -> SQL:
        """Извлекает часть даты."""
        return SQL(f"EXTRACT({date_part} FROM {date_field})")
    
    def truncate_date(self, date_part: str, date_field: Any) -> SQL:
        """Обрезает дату до указанной части."""
        return SQL(f"DATE_TRUNC('{date_part}', {date_field})")
    
    def random(self) -> SQL:
        """Генератор случайных чисел."""
        return SQL('RANDOM()')
    
    def concat(self, *args) -> NodeList:
        """Конкатенация строк."""
        return NodeList(args, glue=' || ')


class DuckDBCursor:
    """
    Курсор для выполнения запросов DuckDB.
    Эмулирует интерфейс DB-API 2.0.
    """
    
    def __init__(self, connection: duckdb.DuckDBPyConnection, commit: bool = False):
        self._connection = connection
        self._commit = commit
        self._result = None
        self._rows: Optional[List[tuple]] = None
        self._row_idx = 0
        self._rowcount = -1
        self._lastrowid = 0
        self._description: Optional[List[Tuple]] = None
    
    def execute(self, sql: str, params: Sequence = ()) -> 'DuckDBCursor':
        """Выполняет SQL запрос."""
        try:
            if params:
                self._result = self._connection.execute(sql, list(params))
            else:
                self._result = self._connection.execute(sql)
            
            try:
                self._rows = self._result.fetchall()
                self._rowcount = len(self._rows)
                
                # Для INSERT с RETURNING сохраняем lastrowid
                if self._rows and sql.strip().upper().startswith('INSERT'):
                    if len(self._rows) > 0 and len(self._rows[0]) > 0:
                        try:
                            self._lastrowid = int(self._rows[0][0])
                        except (ValueError, TypeError):
                            pass
                
                if self._result.description:
                    self._description = [
                        (col[0], col[1], None, None, None, None, None)
                        for col in self._result.description
                    ]
            except Exception:
                self._rows = []
                self._rowcount = 0
            
            self._row_idx = 0
            
        except Exception as e:
            raise e
        
        return self
    
    def executemany(self, sql: str, params_list: List[Sequence]) -> 'DuckDBCursor':
        """Выполняет запрос для множества параметров."""
        total_affected = 0
        for params in params_list:
            self.execute(sql, params)
            total_affected += self._rowcount if self._rowcount > 0 else 0
        self._rowcount = total_affected
        return self
    
    def fetchone(self) -> Optional[tuple]:
        """Получает одну строку."""
        if self._rows is None or self._row_idx >= len(self._rows):
            return None
        row = self._rows[self._row_idx]
        self._row_idx += 1
        return row
    
    def fetchmany(self, size: Optional[int] = None) -> List[tuple]:
        """Получает несколько строк."""
        if self._rows is None:
            return []
        if size is None:
            size = 1
        end_idx = min(self._row_idx + size, len(self._rows))
        rows = self._rows[self._row_idx:end_idx]
        self._row_idx = end_idx
        return rows
    
    def fetchall(self) -> List[tuple]:
        """Получает все строки."""
        if self._rows is None:
            return []
        rows = self._rows[self._row_idx:]
        self._row_idx = len(self._rows)
        return rows
    
    def __iter__(self) -> Iterator[tuple]:
        """Итератор по результатам."""
        if self._rows:
            for row in self._rows[self._row_idx:]:
                yield row
    
    def close(self) -> None:
        """Закрывает курсор."""
        self._result = None
        self._rows = None
    
    @property
    def rowcount(self) -> int:
        return self._rowcount
    
    @property
    def lastrowid(self) -> int:
        return self._lastrowid
    
    @property
    def description(self) -> Optional[List[Tuple]]:
        return self._description


# Алиас
DuckDB = DuckDBDatabase
