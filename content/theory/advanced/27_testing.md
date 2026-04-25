# Тестирование с pytest — от 0 до 100%

Без тестов нельзя жить. Любой нетривиальный код требует тестов — иначе ты не знаешь, работает ли он сейчас, а каждое изменение — рулетка. На собеседованиях в нормальные компании за «не пишу тесты» берут в инженерное лицо.

В Python золотой стандарт — **pytest**. unittest идёт в стандартной библиотеке, но pytest проще, мощнее, удобнее. Эта тема — про pytest, плюс mock, фикстуры, параметризацию, покрытие, и testing pyramid.

---

## 1. Зачем тесты

Тест — это **код, который проверяет, что другой код работает правильно**.

```python
def add(a, b):
    return a + b

def test_add():
    assert add(2, 3) == 5
    assert add(0, 0) == 0
    assert add(-1, 1) == 0
```

Запускаешь pytest — он находит `test_*` функции, выполняет, отчитывается.

Преимущества:
- **Документация поведения**: тесты показывают, как функция должна работать.
- **Регрессии**: меняешь код, тесты ловят, что сломал.
- **Дизайн**: трудно тестировать = плохой дизайн.
- **Уверенность**: можешь рефакторить без страха.

---

## 2. pytest — установка и базовое использование

```bash
pip install pytest

# структура:
# project/
#   src/
#     mymodule.py
#   tests/
#     test_mymodule.py
```

```python
# tests/test_mymodule.py
from mymodule import add

def test_add_positive():
    assert add(2, 3) == 5

def test_add_zero():
    assert add(0, 5) == 5
```

Запуск:
```bash
pytest                         # все тесты
pytest tests/test_mymodule.py  # конкретный файл
pytest -k "add_positive"       # только тесты с именем добавляющим "add_positive"
pytest -v                       # verbose
pytest -x                       # остановиться при первой ошибке
pytest --pdb                    # упасть в pdb при ошибке
```

---

## 3. Соглашения

- Файлы: `test_*.py` или `*_test.py`.
- Функции: `def test_*():`.
- Классы: `class Test*` (без `__init__`).
- В классах: `def test_*(self):`.

```python
class TestUser:
    def test_create(self):
        u = User("Alice")
        assert u.name == "Alice"
    
    def test_email(self):
        u = User("Alice", email="a@b.com")
        assert u.email == "a@b.com"
```

Если есть `pyproject.toml` или `pytest.ini`, можно настраивать обнаружение:
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
```

---

## 4. assert — мощно в pytest

В обычном `unittest` приходится `self.assertEqual(...)`. В pytest — обычный `assert`:
```python
assert result == 5
assert "hello" in greeting
assert isinstance(obj, list)
assert len(items) > 0
```

Pytest **разбирает** assert и показывает информативное сообщение:
```
>       assert add(2, 3) == 6
E       assert 5 == 6
E         +  where 5 = add(2, 3)
```

Это «assertion rewriting» — pytest перехватывает компиляцию и улучшает диагностику.

---

## 5. Фикстуры — основа pytest

Фикстура — это **подготовительная функция**, чьё значение передаётся в тесты:

```python
import pytest

@pytest.fixture
def user():
    return User("Alice", email="a@b.com")

def test_user_name(user):
    assert user.name == "Alice"

def test_user_email(user):
    assert user.email == "a@b.com"
```

pytest видит `user` как параметр теста → понимает что нужна фикстура `user` → вызывает её → передаёт результат.

### Setup/teardown через yield

```python
@pytest.fixture
def db():
    conn = connect_to_db()
    yield conn
    conn.close()    # выполняется после теста
```

`yield` разделяет setup и teardown. Если тест упадёт — teardown всё равно выполнится.

### Scope

```python
@pytest.fixture(scope="function")    # default — для каждого теста
@pytest.fixture(scope="class")        # одна на класс
@pytest.fixture(scope="module")       # одна на файл
@pytest.fixture(scope="session")      # одна на запуск pytest
```

Если фикстура дорогая (запуск БД) — `scope="session"` чтобы запускалась один раз.

### conftest.py — общие фикстуры

```python
# tests/conftest.py
import pytest

@pytest.fixture
def db():
    return connect_to_test_db()
```

Этот файл pytest подхватывает автоматически. Фикстуры из него доступны во всех тестах в этой папке (и вложенных).

### autouse

```python
@pytest.fixture(autouse=True)
def reset_state():
    yield
    clear_global_state()
```

`autouse=True` — фикстура применяется ко всем тестам автоматически, без указания в параметрах.

---

## 6. Параметризация

Запустить тот же тест с разными данными:
```python
import pytest

@pytest.mark.parametrize("a,b,expected", [
    (1, 2, 3),
    (0, 0, 0),
    (-1, 1, 0),
    (10, 20, 30),
])
def test_add(a, b, expected):
    assert add(a, b) == expected
```

pytest запустит 4 теста, каждый с своими параметрами. В отчёте увидишь:
```
test_add[1-2-3] PASSED
test_add[0-0-0] PASSED
...
```

С id-ами:
```python
@pytest.mark.parametrize("a,b,expected", [
    pytest.param(1, 2, 3, id="positive"),
    pytest.param(0, 0, 0, id="zeros"),
    pytest.param(-1, 1, 0, id="opposite"),
])
```

Несколько `parametrize` — декартово произведение:
```python
@pytest.mark.parametrize("a", [1, 2, 3])
@pytest.mark.parametrize("b", [10, 20])
def test_combine(a, b):
    # 6 тестов: 1×10, 1×20, 2×10, 2×20, 3×10, 3×20
    ...
```

---

## 7. Маркеры

```python
@pytest.mark.slow
def test_heavy():
    do_long_thing()

@pytest.mark.skip(reason="not implemented")
def test_future():
    ...

@pytest.mark.skipif(sys.version_info < (3, 11), reason="needs 3.11+")
def test_modern():
    ...

@pytest.mark.xfail(reason="known bug")
def test_buggy():
    assert broken_func() == 1    # упадёт, но pytest пропустит как xfail
```

Запуск только определённых:
```bash
pytest -m slow                  # только @pytest.mark.slow
pytest -m "not slow"            # все кроме slow
pytest -m "slow and integration"
```

Регистрация маркеров (чтобы pytest не ругался):
```toml
[tool.pytest.ini_options]
markers = [
    "slow: marks slow tests",
    "integration: marks integration tests",
]
```

---

## 8. pytest.raises — тестирование исключений

```python
import pytest

def test_zero_division():
    with pytest.raises(ZeroDivisionError):
        1 / 0

def test_message():
    with pytest.raises(ValueError, match="must be positive"):
        validate(-1)

def test_get_exception():
    with pytest.raises(ValueError) as exc_info:
        validate(-1)
    assert exc_info.value.code == 42
```

Эквивалент `try/except` с проверкой что исключение точно вылетело.

---

## 9. Mocking

`unittest.mock` — стандартный модуль.

```python
from unittest.mock import Mock, patch, MagicMock

def test_with_mock():
    fake_db = Mock()
    fake_db.query.return_value = ["row1", "row2"]
    
    result = process(fake_db)
    assert result == 2
    fake_db.query.assert_called_once_with("SELECT *")
```

### `patch` — подменить что-то на время теста

```python
@patch("mymodule.requests.get")
def test_fetch(mock_get):
    mock_get.return_value.json.return_value = {"key": "value"}
    
    result = fetch_data()
    
    assert result == {"key": "value"}
    mock_get.assert_called_once_with("http://...")
```

`patch` подменяет `mymodule.requests.get` на Mock на время теста, восстанавливает после.

```python
def test_fetch():
    with patch("mymodule.requests.get") as mock_get:
        mock_get.return_value.json.return_value = {...}
        ...
```

Контекстный менеджер — то же самое.

### Что мокать

```python
# плохо: patch ИСХОДНОЙ функции:
@patch("requests.get")    # ⚠️ мокает в библиотеке, может не сработать

# хорошо: patch ИМПОРТА в твоём модуле:
@patch("mymodule.requests.get")
```

Правило — мокать там, **где импорт используется**, не где определён.

### MagicMock vs Mock

`Mock` — базовый. `MagicMock` — поддерживает magic-методы (`__len__`, `__iter__`, ...).

### pytest-mock

```bash
pip install pytest-mock
```

Удобный плагин:
```python
def test_with_mocker(mocker):
    mock_get = mocker.patch("mymodule.requests.get")
    mock_get.return_value.json.return_value = {...}
    ...
```

`mocker` — фикстура, автоматически чистит после теста. Меньше @decorator-вложенности.

---

## 10. Изоляция тестов

Тесты должны быть **независимыми** — порядок не важен, тесты не делятся состоянием.

```python
# плохо:
counter = 0
def test_a():
    global counter
    counter += 1
    assert counter == 1

def test_b():
    global counter
    counter += 1
    assert counter == 2    # ⚠️ зависит от порядка
```

Тесты обычно идут в алфавите, но не полагайся:
```bash
pytest --random-order    # random ordering plugin
```

### Очистка после теста

```python
@pytest.fixture
def temp_dir(tmp_path):
    yield tmp_path
    # tmp_path автоматически очищается pytest
```

`tmp_path` — встроенная фикстура, даёт уникальную временную директорию.

`monkeypatch` — для подмены атрибутов:
```python
def test_env(monkeypatch):
    monkeypatch.setenv("API_KEY", "test")
    assert get_api_key() == "test"
    # после теста — восстановится оригинальное значение
```

---

## 11. Testing pyramid

| Уровень | Что | Скорость | Стоимость |
|---|---|---|---|
| **Unit tests** | Одна функция/класс | мс | дёшево |
| **Integration tests** | Несколько компонентов | секунды | средне |
| **E2E tests** | Полная система через UI/API | минуты | дорого |

Соотношение примерно: 70% unit, 20% integration, 10% E2E. Большая часть — быстрые unit, медленные E2E — для критичных flow.

---

## 12. Что и как тестировать

### Хорошие тесты — какие

- **Изолированные**: не зависят от внешнего мира (БД, сеть, файлы).
- **Детерминированные**: всегда тот же результат.
- **Быстрые**: миллисекунды.
- **Читаемые**: видно что проверяют.
- **Один assert на тест** (идеал; в реальности 1-3).

### Что тестировать

- Edge cases: пустой ввод, ноль, отрицательные, очень большие.
- Граничные условия: первый/последний элемент, переполнение.
- Ошибочные пути: исключения, неверные типы.
- Ключевые happy paths.

### AAA pattern

```python
def test_user_can_login():
    # Arrange
    user = create_user(email="a@b.com", password="secret")
    
    # Act
    result = login("a@b.com", "secret")
    
    # Assert
    assert result.success
    assert result.user_id == user.id
```

---

## 13. Покрытие тестов

```bash
pip install pytest-cov

pytest --cov=mymodule           # покрытие mymodule
pytest --cov=mymodule --cov-report=html
# открой htmlcov/index.html
```

Видишь, какие строки тестируются, какие нет.

⚠️ **Покрытие — не самоцель**. 100% coverage не означает 0 багов. Лучше 80% покрытия с осмысленными тестами, чем 100% с бесполезными.

---

## 14. Свойственное тестирование (property-based)

Hypothesis — генерирует случайные данные:
```python
from hypothesis import given, strategies as st

@given(st.lists(st.integers()))
def test_sort_idempotent(lst):
    assert sorted(sorted(lst)) == sorted(lst)

@given(st.text())
def test_reverse_twice(s):
    assert s[::-1][::-1] == s
```

Hypothesis находит **минимальный** контрпример, если найдёт баг. Идеально для парсеров, алгоритмов.

---

## 15. Тестирование async

```python
import pytest, asyncio

# простой:
def test_async_simple():
    result = asyncio.run(my_async_func())
    assert result == 42

# pytest-asyncio:
import pytest_asyncio

@pytest.mark.asyncio
async def test_async():
    result = await my_async_func()
    assert result == 42

@pytest_asyncio.fixture
async def db():
    conn = await connect_async()
    yield conn
    await conn.close()
```

`pytest-asyncio` упрощает работу.

---

## 16. Стандарт unittest (для контекста)

```python
import unittest

class TestUser(unittest.TestCase):
    def setUp(self):
        self.user = User("Alice")
    
    def tearDown(self):
        self.user.cleanup()
    
    def test_name(self):
        self.assertEqual(self.user.name, "Alice")
    
    def test_email(self):
        with self.assertRaises(AttributeError):
            self.user.unknown_attr

if __name__ == "__main__":
    unittest.main()
```

Чем pytest лучше:
- Меньше boilerplate.
- Простые `assert ==` вместо `self.assertEqual`.
- Фикстуры мощнее `setUp`.
- Параметризация через декоратор, не через цикл.

В современных проектах — pytest. unittest — только если интегрируешься со старым кодом.

---

## 17. doctest

```python
def add(a, b):
    """
    Сложить два числа.
    
    >>> add(2, 3)
    5
    >>> add(-1, 1)
    0
    """
    return a + b
```

```bash
python -m doctest mymodule.py -v
```

или в pytest:
```bash
pytest --doctest-modules
```

Хорошо для маленьких функций как living-документация.

---

## 18. CI и тесты

В CI (GitHub Actions, GitLab CI):
```yaml
- run: pip install -e ".[dev]"
- run: pytest --cov --cov-fail-under=80
- run: mypy src/
- run: ruff check src/
```

Ниже 80% покрытия — CI красный.

---

## 19. Типичные ошибки

### Тестирование implementation, не behavior

```python
def test_login():
    user = login("a", "b")
    assert user._token_field == "..."    # ⚠️ тестируем приватное поле
```

Тестируй интерфейс, не внутренности. Иначе рефакторинг ломает тесты.

### Большие тесты с многими assert

```python
def test_everything():
    user = create()
    assert user.id
    user.update(...)
    assert ...
    user.delete()
    assert ...
    # 50 строк
```

Разбей на маленькие тесты, по одному на сценарий.

### Зависимость от внешнего мира

```python
def test_fetch():
    response = requests.get("http://real-api.com")    # ⚠️ flaky
```

Мокай сеть. Используй httpretty, requests-mock, responses.

### Не тестируешь edge cases

```python
def test_divide():
    assert divide(10, 2) == 5    # только happy path
    # а что если b = 0? отрицательные?
```

### Тесты медленные

Если pytest идёт минуты — мало кто будет запускать. Изолируй медленные (`@pytest.mark.slow`), запускай отдельно.

### Mock-зомби: всё замокано, тесты ничего не тестируют

```python
def test_login(mocker):
    mocker.patch("login.User.authenticate", return_value=True)
    assert login("a", "b")    # тестирует что mock вернул True. Бесполезно.
```

Мокай только границы (БД, сеть). Логику не мокай.

---

## 20. Что нужно запомнить

- pytest — стандарт; обычные `assert`, не `self.assertEqual`.
- Файлы `test_*.py`, функции `def test_*():`.
- Фикстуры через `@pytest.fixture`, передаются как аргументы тестам.
- `conftest.py` — общие фикстуры.
- Параметризация — `@pytest.mark.parametrize`.
- `pytest.raises` для проверки исключений.
- `unittest.mock.patch` или `pytest-mock` для замены зависимостей.
- `tmp_path`, `monkeypatch` — встроенные фикстуры.
- Покрытие через `pytest-cov`; 80% — разумная цель.
- Property-based testing через Hypothesis.
- Async — через `pytest-asyncio`.
- Тестируй behavior, не implementation; держи тесты быстрые и изолированные.

После тестов — последняя тема: **производительность и профилирование**. Как находить медленные места и ускорять.
