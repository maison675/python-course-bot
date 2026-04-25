# Декораторы продвинутые — от 0 до 100%

В начинающем треке мы кратко увидели декораторы. Здесь — глубоко: как они работают, продвинутые паттерны, типизация, реальные кейсы (cache, retry, validate, rate limit), декораторы для классов и для async-функций.

Декораторы — основа большинства фреймворков. `@app.route` (Flask), `@click.command`, `@property`, `@functools.lru_cache`, `@dataclass`, `@pytest.fixture` — всё это декораторы.

---

## 1. Что такое декоратор

Декоратор — это **функция, принимающая функцию и возвращающая функцию** (обычно модифицированную):

```python
def my_decorator(func):
    def wrapper(*args, **kwargs):
        print(f"Calling {func.__name__}")
        result = func(*args, **kwargs)
        print(f"Returned {result}")
        return result
    return wrapper

@my_decorator
def add(a, b):
    return a + b

# эквивалент:
def add(a, b):
    return a + b
add = my_decorator(add)

add(2, 3)
# Calling add
# Returned 5
```

`@decorator` — синтаксический сахар для `func = decorator(func)`.

---

## 2. functools.wraps — обязательно

Без `wraps` декорированная функция теряет имя, docstring, аннотации:
```python
def my_dec(func):
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper

@my_dec
def add(a, b):
    """Сложить два числа."""
    return a + b

print(add.__name__)    # 'wrapper' — потеряли
print(add.__doc__)     # None
```

С `wraps`:
```python
import functools

def my_dec(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper

print(add.__name__)    # 'add'
print(add.__doc__)     # 'Сложить два числа.'
```

`@functools.wraps(func)` копирует `__name__`, `__doc__`, `__module__`, `__qualname__`, `__annotations__` из исходной функции. **Всегда используй**.

---

## 3. Декоратор с параметрами

Декоратор может принимать аргументы. Тогда он становится «фабрикой декораторов» — функцией трёх уровней:

```python
def repeat(times):                        # фабрика
    def decorator(func):                   # декоратор
        @functools.wraps(func)
        def wrapper(*args, **kwargs):      # обёртка
            for _ in range(times):
                result = func(*args, **kwargs)
            return result
        return wrapper
    return decorator

@repeat(3)
def hello():
    print("hi")

hello()
# hi
# hi
# hi
```

Эквивалент:
```python
hello = repeat(3)(hello)
```

Три уровня вложенности — норма для параметризованных декораторов.

---

## 4. Универсальный декоратор: с/без аргументов

Иногда хочется чтобы и `@deco`, и `@deco(arg)` работали. Используем трюк:

```python
def smart_decorator(func=None, *, prefix=""):
    if func is None:
        return functools.partial(smart_decorator, prefix=prefix)
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        print(f"{prefix} calling {func.__name__}")
        return func(*args, **kwargs)
    return wrapper

@smart_decorator
def f1(): ...

@smart_decorator(prefix=">>>")
def f2(): ...
```

Если `func` передан как первый позиционный — это «без аргументов» использование. Иначе — фабрика.

---

## 5. Декоратор как класс

Декоратор может быть **классом** с `__call__`:

```python
class CallCounter:
    def __init__(self, func):
        functools.update_wrapper(self, func)
        self.func = func
        self.count = 0
    def __call__(self, *args, **kwargs):
        self.count += 1
        print(f"Call #{self.count}")
        return self.func(*args, **kwargs)

@CallCounter
def hello():
    print("hi")

hello()         # Call #1, hi
hello()         # Call #2, hi
print(hello.count)    # 2
```

Класс-декоратор удобен когда нужно состояние.

⚠️ Подвох: при использовании на методах класса — `self` не передаётся правильно. Нужен `__get__`:
```python
class Decorator:
    def __init__(self, func):
        self.func = func
    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)
    def __get__(self, instance, owner):
        return functools.partial(self, instance)
```

Часто проще — функциональный декоратор.

---

## 6. Декоратор класса

Декорирует **класс**, не функцию:

```python
def add_repr(cls):
    def __repr__(self):
        attrs = ", ".join(f"{k}={v!r}" for k, v in self.__dict__.items())
        return f"{cls.__name__}({attrs})"
    cls.__repr__ = __repr__
    return cls

@add_repr
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

print(Point(1, 2))    # Point(x=1, y=2)
```

Самые известные:
- `@dataclass` — генерирует `__init__`, `__repr__`, `__eq__`.
- `@register` (django, click) — регистрирует класс в реестре.

Декораторы класса — альтернатива метаклассам в простых случаях.

---

## 7. Реальные паттерны

### functools.lru_cache — memoization

```python
import functools

@functools.lru_cache(maxsize=128)
def fib(n):
    if n < 2: return n
    return fib(n-1) + fib(n-2)

fib(100)    # быстро, кэшируется
```

### Retry с backoff

```python
import time, functools

def retry(times=3, delay=1, backoff=2, exceptions=(Exception,)):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            cur_delay = delay
            for attempt in range(times):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == times - 1:
                        raise
                    print(f"Retry {attempt+1}: {e}")
                    time.sleep(cur_delay)
                    cur_delay *= backoff
        return wrapper
    return decorator

@retry(times=5, delay=1, backoff=2)
def fetch():
    requests.get(url)
```

### Timing

```python
def timed(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        t0 = time.perf_counter()
        result = func(*args, **kwargs)
        print(f"{func.__name__}: {time.perf_counter() - t0:.3f}s")
        return result
    return wrapper

@timed
def slow():
    time.sleep(1)
```

### Logging

```python
import logging
log = logging.getLogger(__name__)

def logged(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        log.info(f"{func.__name__}({args}, {kwargs})")
        try:
            result = func(*args, **kwargs)
            log.info(f"{func.__name__} returned {result!r}")
            return result
        except Exception as e:
            log.exception(f"{func.__name__} raised")
            raise
    return wrapper
```

### Validate

```python
def validate(**type_checks):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            sig = inspect.signature(func)
            bound = sig.bind(*args, **kwargs)
            for name, expected in type_checks.items():
                if name in bound.arguments:
                    val = bound.arguments[name]
                    if not isinstance(val, expected):
                        raise TypeError(f"{name} must be {expected.__name__}")
            return func(*args, **kwargs)
        return wrapper
    return decorator

@validate(name=str, age=int)
def greet(name, age):
    return f"{name}, {age}"

greet("Alice", 30)        # OK
greet("Alice", "30")      # TypeError
```

### Rate limit

```python
import time
from collections import deque

def rate_limit(calls, period):
    def decorator(func):
        history = deque()
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            now = time.time()
            while history and now - history[0] > period:
                history.popleft()
            if len(history) >= calls:
                raise RuntimeError(f"Rate limit: {calls} per {period}s")
            history.append(now)
            return func(*args, **kwargs)
        return wrapper
    return decorator

@rate_limit(calls=5, period=60)
def api_call(): ...
```

---

## 8. Композиция декораторов

Несколько декораторов:
```python
@A
@B
@C
def func():
    pass

# = A(B(C(func)))
```

Применяются **снизу вверх** в исходнике (ближайший к функции — первый). Внешний — последний.

```python
@timed
@logged
def slow():
    time.sleep(1)
```

Получается: сначала `logged` оборачивает `slow`, потом `timed` оборачивает результат. При вызове первым отрабатывает `timed` (внешний), потом `logged`, потом сам `slow`.

---

## 9. Async-декораторы

Для `async def` функции — декоратор тоже async:

```python
import functools, asyncio

def async_timed(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        t0 = asyncio.get_event_loop().time()
        result = await func(*args, **kwargs)
        print(f"{func.__name__}: {asyncio.get_event_loop().time() - t0:.3f}s")
        return result
    return wrapper

@async_timed
async def fetch():
    await asyncio.sleep(1)
```

### Универсальный (sync + async)

```python
import asyncio

def universal_timed(func):
    if asyncio.iscoroutinefunction(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            t0 = asyncio.get_event_loop().time()
            result = await func(*args, **kwargs)
            print(f"{func.__name__}: {asyncio.get_event_loop().time() - t0:.3f}s")
            return result
        return async_wrapper
    else:
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            t0 = time.perf_counter()
            result = func(*args, **kwargs)
            print(f"{func.__name__}: {time.perf_counter() - t0:.3f}s")
            return result
        return sync_wrapper
```

---

## 10. Типизация декораторов

Простой:
```python
from typing import TypeVar, Callable, Any
F = TypeVar("F", bound=Callable[..., Any])

def my_dec(func: F) -> F:
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper    # type: ignore[return-value]
```

С ParamSpec (3.10+) — точнее:
```python
from typing import ParamSpec, TypeVar, Callable
P = ParamSpec("P")
T = TypeVar("T")

def my_dec(func: Callable[P, T]) -> Callable[P, T]:
    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        return func(*args, **kwargs)
    return wrapper
```

mypy теперь точно проверяет аргументы декорированной функции.

---

## 11. functools.cache — простая версия lru_cache (3.9+)

```python
@functools.cache
def fib(n):
    if n < 2: return n
    return fib(n-1) + fib(n-2)
```

`cache` = `lru_cache(maxsize=None)` — без ограничения.

### functools.cached_property

```python
class Container:
    @functools.cached_property
    def expensive(self):
        return sum(self.data)

c = Container([1, 2, 3])
c.expensive    # вычислено
c.expensive    # из кэша (хранится в obj.__dict__)
```

Для методов экземпляра, кэширование по объекту.

---

## 12. functools.partial и partialmethod

`partial` — частичное применение:
```python
from functools import partial

def power(base, exp):
    return base ** exp

square = partial(power, exp=2)
square(5)    # 25

cube = partial(power, exp=3)
```

`partialmethod` — для методов класса:
```python
class Calculator:
    def operation(self, op, x, y):
        return op(x, y)
    
    add = functools.partialmethod(operation, lambda x, y: x + y)
    sub = functools.partialmethod(operation, lambda x, y: x - y)

c = Calculator()
c.add(2, 3)    # 5
```

---

## 13. functools.singledispatch — generic functions

Полиморфизм по типу аргумента:
```python
from functools import singledispatch

@singledispatch
def process(arg):
    raise NotImplementedError

@process.register
def _(arg: int):
    return arg * 2

@process.register
def _(arg: str):
    return arg.upper()

@process.register(list)
def _(arg):
    return arg[::-1]

process(5)              # 10
process("hi")           # 'HI'
process([1, 2, 3])      # [3, 2, 1]
```

Альтернатива if/isinstance цепочкам.

`singledispatchmethod` — то же для методов класса.

---

## 14. contextlib.contextmanager — декоратор для контекстных менеджеров

```python
from contextlib import contextmanager

@contextmanager
def my_resource():
    print("open")
    try:
        yield "data"
    finally:
        print("close")

with my_resource() as r:
    print(r)    # 'data'
```

Эквивалент класса с `__enter__`/`__exit__`. Удобнее для простых случаев.

---

## 15. Декораторы в стандартной библиотеке

| Декоратор | Что делает |
|---|---|
| `@property`, `@staticmethod`, `@classmethod` | модификаторы методов |
| `@functools.wraps` | сохранение метаданных |
| `@functools.cache`, `@functools.lru_cache` | мемоизация |
| `@functools.cached_property` | ленивое вычисление атрибута |
| `@functools.singledispatch` | полиморфизм по типу |
| `@functools.total_ordering` | автогенерация сравнений из `__eq__` и `__lt__` |
| `@dataclasses.dataclass` | автогенерация `__init__` и др. |
| `@contextlib.contextmanager` | контекстный менеджер из generator |
| `@contextlib.asynccontextmanager` | то же для async |
| `@abc.abstractmethod` | абстрактный метод |
| `@typing.overload` | перегрузки типов |

---

## 16. Декораторы во фреймворках

### Flask

```python
@app.route("/")
def index():
    return "Hello"

# = app.route("/")(index)
```

`app.route("/")` возвращает декоратор, который регистрирует функцию в реестре путей.

### FastAPI

```python
@app.get("/items/{id}")
async def get_item(id: int):
    return {"id": id}
```

Похожий паттерн.

### Click

```python
@click.command()
@click.argument("name")
@click.option("--count", default=1)
def hello(name, count):
    for _ in range(count):
        print(f"Hello, {name}!")
```

Декораторы регистрируют команду и её параметры.

### pytest

```python
@pytest.fixture
def db():
    return setup_db()

def test_thing(db):
    ...

@pytest.mark.parametrize("x,expected", [(1, 2), (2, 4)])
def test_double(x, expected):
    assert double(x) == expected
```

### Django

```python
@login_required
@cache_page(60 * 15)
def my_view(request):
    ...
```

Composable декораторы для view.

---

## 17. Подводные камни

### Неправильный порядок

```python
@cache
@retry(times=3)
def fetch(url):
    ...
```

`cache` — внешний. Если кэш есть — `retry` даже не вызывается. Если кэша нет — `retry` пытается, неудачи **не кэшируются**.

vs.
```python
@retry(times=3)
@cache
def fetch(url):
    ...
```

Здесь `retry` — внешний. Каждая попытка проходит через кэш. Если кэш есть — успех с первой попытки. Если нет — ретраит, и при успехе кэширует.

Порядок имеет значение!

### Декоратор выполняется при импорте

```python
@register
def my_func():
    ...
```

`register(my_func)` вызывается **в момент определения**, не вызова. Поэтому если декоратор имеет побочные эффекты (логирование, регистрация в реестре) — они происходят при загрузке модуля.

### Не использовать functools.wraps

См. п.2. Без `wraps` теряется метаинформация.

### State в декораторе для класса

```python
@call_counter
def method(self): ...    # ⚠️ state shared между всеми instances
```

Используй атрибут на экземпляре или class-attribute.

### type-checking игнорирует декораторы

mypy без ParamSpec может терять типы декорированной функции. Используй ParamSpec.

---

## 18. Что нужно запомнить

- Декоратор = функция func → func' (обычно с обёрткой).
- `@deco` ≡ `func = deco(func)`.
- `@functools.wraps(func)` обязателен в обёртке.
- Параметризованный декоратор — функция трёх уровней: фабрика → декоратор → wrapper.
- Класс-декоратор через `__call__`.
- Декораторы класса модифицируют сам класс (`@dataclass`).
- Композиция: `@A @B @C func` = `A(B(C(func)))`.
- Async-функции — async-декораторы; универсальный — проверка `iscoroutinefunction`.
- ParamSpec для точной типизации декораторов.
- Реальные паттерны: cache, retry, log, validate, rate limit, timed.

После декораторов — **тестирование**. Без тестов нельзя жить, и pytest — стандарт де-факто.
