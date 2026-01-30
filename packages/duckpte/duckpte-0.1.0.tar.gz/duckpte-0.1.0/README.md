# DuckPTE - DuckDB Parallel Transaction Engine

Модуль для работы с DuckDB с поддержкой транзакций, конкурентных операций и **Peewee ORM**.

## Установка

```bash
# Из PyPI (когда опубликован)
pip install duckpte

# Локальная установка для разработки
pip install -e .

# С дополнительными зависимостями
pip install duckpte[pandas]     # + pandas
pip install duckpte[dev]        # + инструменты разработки
pip install duckpte[all]        # всё
```

## Возможности

- **Пул соединений** - эффективное управление соединениями для многопоточных приложений
- **Транзакции** - полная поддержка транзакций с commit/rollback и savepoints
- **Конкурентные операции** - параллельное выполнение запросов
- **Пакетная обработка** - эффективная вставка больших объёмов данных
- **Интеграция с pandas** - работа с DataFrame
- **Peewee ORM** - полная интеграция с Peewee для работы с моделями

---

## Peewee ORM интеграция

### Быстрый старт с Peewee

```python
from peewee import Model, CharField, IntegerField, BooleanField, DateTimeField
from duckpte import DuckDBDatabase
from datetime import datetime

# Создаём подключение к DuckDB
db = DuckDBDatabase('my_database.db')

# Определяем модели
class BaseModel(Model):
    class Meta:
        database = db

class User(BaseModel):
    name = CharField(max_length=100)
    email = CharField(unique=True)
    age = IntegerField(default=0)
    is_active = BooleanField(default=True)
    created_at = DateTimeField(default=datetime.now)

class Post(BaseModel):
    title = CharField(max_length=255)
    content = CharField()
    views = IntegerField(default=0)
    # user = ForeignKeyField(User, backref='posts')

# Создаём таблицы
db.create_tables([User, Post])

# CRUD операции
user = User.create(name='Иван', email='ivan@example.com', age=25)
print(f"Создан пользователь: {user.name}")

# Выборка
users = User.select().where(User.is_active == True)
for u in users:
    print(f"{u.name}: {u.email}")

# Обновление
User.update(age=26).where(User.name == 'Иван').execute()

# Удаление
User.delete().where(User.email == 'ivan@example.com').execute()
```

### Транзакции с Peewee

```python
from duckpte import DuckDBDatabase

db = DuckDBDatabase('data.db')

# Использование контекстного менеджера
with db.atomic() as transaction:
    User.create(name='Алексей', email='alex@example.com')
    User.create(name='Мария', email='maria@example.com')
    # Автоматический commit при успешном завершении
    # Автоматический rollback при исключении

# Ручное управление транзакциями
db.begin()
try:
    User.create(name='Пётр', email='peter@example.com')
    db.commit()
except Exception as e:
    db.rollback()
    raise
```

### Сложные запросы

```python
from peewee import fn, JOIN

# Агрегация
stats = (User
    .select(
        fn.COUNT(User.id).alias('total'),
        fn.AVG(User.age).alias('avg_age')
    )
    .where(User.is_active == True)
    .get())

print(f"Всего: {stats.total}, Средний возраст: {stats.avg_age}")

# Группировка
by_age = (User
    .select(User.age, fn.COUNT(User.id).alias('count'))
    .group_by(User.age)
    .order_by(User.age))

for row in by_age:
    print(f"Возраст {row.age}: {row.count} пользователей")

# Подзапросы
active_users = User.select().where(User.is_active == True)
posts = Post.select().where(Post.user << active_users)
```

### In-Memory база данных

```python
from duckpte import DuckDBDatabase

# Для тестов и временных данных
db = DuckDBDatabase(':memory:')

class TempData(Model):
    value = CharField()
    
    class Meta:
        database = db

db.create_tables([TempData])
TempData.create(value='temporary')
```

---

## Низкоуровневый API (DuckPTEngine)

### Быстрый старт

```python
from duckpte import DuckPTEngine

# Создание движка
engine = DuckPTEngine(database="my_database.db", pool_size=5)

# Создание таблицы
engine.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        name VARCHAR,
        email VARCHAR
    )
""")

# Использование транзакций
with engine.transaction() as tx:
    tx.execute("INSERT INTO users VALUES (?, ?, ?)", (1, "Иван", "ivan@example.com"))
    tx.execute("INSERT INTO users VALUES (?, ?, ?)", (2, "Мария", "maria@example.com"))
    # Автоматический commit при успешном завершении

# Выборка данных
users = engine.fetchall("SELECT * FROM users")
print(users)

# Закрытие
engine.close()
```

### Использование контекстного менеджера

```python
from duckpte import DuckPTEngine

with DuckPTEngine(database=":memory:") as engine:
    engine.execute("CREATE TABLE test (id INTEGER, value TEXT)")
    
    with engine.transaction() as tx:
        tx.execute("INSERT INTO test VALUES (1, 'hello')")
        tx.execute("INSERT INTO test VALUES (2, 'world')")
    
    results = engine.fetchall("SELECT * FROM test")
```

### Транзакции с Savepoints

```python
with engine.transaction() as tx:
    tx.execute("INSERT INTO users VALUES (1, 'User1', 'user1@example.com')")
    
    # Создаём savepoint
    sp = tx.savepoint("before_batch")
    
    try:
        tx.execute("INSERT INTO users VALUES (2, 'User2', 'user2@example.com')")
        tx.execute("INSERT INTO users VALUES (3, 'User3', 'invalid')")  # Может вызвать ошибку
    except Exception:
        # Откат к savepoint, сохраняя первую вставку
        tx.rollback(to_savepoint=sp)
    
    # Коммит с первой записью
```

### Конкурентные операции

#### Асинхронное выполнение

```python
# Асинхронный запрос
future = engine.execute_async("SELECT * FROM large_table WHERE condition = ?", (value,))
# ... другие операции ...
result = future.result()  # Получение результата
```

#### Параллельное выполнение

```python
# Выполнение нескольких запросов параллельно
results = engine.execute_parallel([
    lambda e: e.fetchall("SELECT COUNT(*) FROM users"),
    lambda e: e.fetchall("SELECT AVG(age) FROM users"),
    lambda e: e.fetchall("SELECT * FROM orders WHERE status = 'pending'"),
])
```

#### Пакетная вставка

```python
# Данные для вставки
data = [(i, f"User{i}", f"user{i}@example.com") for i in range(10000)]

# Пакетная вставка с транзакциями
count = engine.batch_execute(
    "INSERT INTO users VALUES (?, ?, ?)",
    data,
    batch_size=1000,
    use_transaction=True
)

# Параллельная пакетная вставка
count = engine.batch_execute_parallel(
    "INSERT INTO users VALUES (?, ?, ?)",
    data,
    batch_size=1000,
    num_workers=4
)
```

### Работа с pandas DataFrame

```python
import pandas as pd

# Создание таблицы из DataFrame
df = pd.DataFrame({
    'id': [1, 2, 3],
    'name': ['Alice', 'Bob', 'Charlie'],
    'score': [95.5, 87.3, 92.1]
})

engine.create_table_from_df("scores", df)

# Вставка данных из DataFrame
new_data = pd.DataFrame({
    'id': [4, 5],
    'name': ['David', 'Eve'],
    'score': [88.0, 91.5]
})

engine.insert_df("scores", new_data)

# Получение результата как DataFrame
result_df = engine.fetchdf("SELECT * FROM scores WHERE score > 90")
```

---

## API Reference

### DuckDBDatabase (Peewee)

Peewee-совместимый адаптер для DuckDB.

```python
DuckDBDatabase(
    database: str = ":memory:",  # Путь к БД или ":memory:"
    read_only: bool = False,     # Режим только для чтения
    config: dict = None          # Конфигурация DuckDB
)
```

| Метод | Описание |
|-------|----------|
| `create_tables([models])` | Создаёт таблицы для моделей |
| `drop_tables([models])` | Удаляет таблицы |
| `atomic()` | Контекстный менеджер транзакции |
| `begin()` | Начинает транзакцию |
| `commit()` | Фиксирует транзакцию |
| `rollback()` | Откатывает транзакцию |
| `execute_sql(sql, params)` | Выполняет SQL запрос |
| `get_tables()` | Возвращает список таблиц |
| `get_columns(table)` | Возвращает колонки таблицы |
| `close()` | Закрывает соединение |

### DuckPTEngine

Основной класс для работы с DuckDB.

```python
DuckPTEngine(
    database: str = ":memory:",  # Путь к БД или ":memory:"
    pool_size: int = 5,          # Размер пула соединений
    max_workers: int = 4,        # Макс. рабочих потоков
    read_only: bool = False,     # Режим только для чтения
    config: dict = None          # Конфигурация DuckDB
)
```

| Метод | Описание |
|-------|----------|
| `execute(query, params)` | Выполняет SQL запрос |
| `fetchall(query, params)` | Возвращает все результаты |
| `fetchone(query, params)` | Возвращает первую строку |
| `fetchdf(query, params)` | Возвращает pandas DataFrame |
| `transaction()` | Контекстный менеджер транзакции |
| `execute_async(query, params)` | Асинхронное выполнение |
| `execute_parallel(operations)` | Параллельное выполнение |
| `batch_execute(query, data, batch_size)` | Пакетная вставка |
| `batch_execute_parallel(query, data, batch_size)` | Параллельная пакетная вставка |
| `table_exists(table_name)` | Проверка существования таблицы |
| `create_table_from_df(name, df)` | Создание таблицы из DataFrame |
| `insert_df(name, df)` | Вставка из DataFrame |
| `close()` | Закрытие движка |

### Transaction

Класс управления транзакциями.

| Метод | Описание |
|-------|----------|
| `begin()` | Начинает транзакцию |
| `commit()` | Фиксирует транзакцию |
| `rollback(to_savepoint)` | Откатывает транзакцию |
| `savepoint(name)` | Создаёт savepoint |
| `release_savepoint(name)` | Освобождает savepoint |
| `execute(query, params)` | Выполняет запрос в транзакции |
| `fetchall(query, params)` | Выполняет и возвращает результаты |
| `fetchone(query, params)` | Выполняет и возвращает первую строку |

---

## Сборка и публикация пакета

```bash
# Установка инструментов сборки
pip install build twine

# Сборка пакета
python -m build

# Проверка пакета
twine check dist/*

# Публикация на PyPI
twine upload dist/*

# Публикация на TestPyPI (для тестирования)
twine upload --repository testpypi dist/*
```

## Лицензия

MIT
