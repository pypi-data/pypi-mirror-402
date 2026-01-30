"""
DuckPTE - DuckDB Parallel Transaction Engine

Модуль для работы с DuckDB с поддержкой транзакций, конкурентных операций
и интеграцией с Peewee ORM.
"""

from .connection_manager import ConnectionManager
from .transaction import Transaction, TransactionContext
from .engine import DuckPTEngine
from .peewee_backend import DuckDBDatabase, DuckDBCursor, DuckDB

__version__ = "0.1.0"
__all__ = [
    # Основные классы
    "ConnectionManager",
    "Transaction",
    "TransactionContext",
    "DuckPTEngine",
    # Peewee интеграция
    "DuckDBDatabase",
    "DuckDBCursor",
    "DuckDB",
]
