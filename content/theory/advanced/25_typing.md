# Типизация по-взрослому — от 0 до 100%

Python — динамически типизированный язык. Но с PEP 484 (2014) и сейчас (2025) — типизация в Python вышла на уровень, сопоставимый с TypeScript. Большие компании пишут весь новый код с типами. Линтеры (`mypy`, `pyright`) ловят 90% багов до запуска.

В этой теме мы пройдём:
- базовый синтаксис аннотаций;
- продвинутые типы (Generic, Protocol, TypeVar);
- что такое type narrowing;
- типизацию декораторов и async;
- mypy/pyright — проверка типов;
- современные фишки 3.10/3.11/3.12.

После этого ты сможешь читать и писать типизированный код на уровне tier-1 команды.

---

## 1. Зачем типы

Без типов:
```python
def greet(name):
    return f"Hello, {name}!"

greet(42)    # 'Hello, 42!' — работает, но логически странно
greet({"a": 1})    # тоже не падает
```

С типами:
```python
def greet(name: str) -> str:
    return f"Hello, {name}!"

greet(42)    # mypy: error: Argument 1 has incompatible type "int"
```

Преимущества:
- ловишь баги до запуска;
- IDE точно подсказывает;
- self-документирование;
- легче рефакторить большой код.

⚠️ Типы в Python **не проверяются в рантайме**. Это аннотации для статических анализаторов. `greet(42)` всё равно работает, mypy просто ругается.

---

## 2. Базовые аннотации

```python
def add(a: int, b: int) -> int:
    return a + b

def greet(name: str, formal: bool = False) -> str:
    return f"Hello, {name}!" if not formal else f"Good day, {name}."

x: int = 5
y: float = 3.14
s: str = "hello"
flag: bool = True
```

Базовые: `int`, `float`, `bool`, `str`, `bytes`, `None`.

---

## 3. Коллекции

### Со старого синтаксиса (3.8-)

```python
from typing import List, Dict, Tuple, Set

def process(items: List[int]) -> Dict[str, int]: ...
```

### Современный (3.9+)

```python
def process(items: list[int]) -> dict[str, int]: ...
```

Можно использовать встроенные типы как генерики прямо. `from __future__ import annotations` позволяет делать это даже в 3.7+.

```python
from __future__ import annotations    # активирует синтаксис нового стиля

x: list[int]
y: dict[str, list[int]]
```

### Виды коллекций

```python
list[int]              # список int
tuple[int, str]        # кортеж точной длины 2
tuple[int, ...]        # кортеж любой длины из int
set[str]
dict[str, int]
frozenset[int]
```

---

## 4. Optional, Union

`Optional[X]` = `X | None`:
```python
from typing import Optional

def find_user(id: int) -> Optional[User]:
    ...

# или с 3.10+:
def find_user(id: int) -> User | None:
    ...
```

`Union[X, Y]`:
```python
from typing import Union
def parse(x: Union[int, str]) -> int: ...

# или с 3.10+:
def parse(x: int | str) -> int: ...
```

---

## 5. Any — отказ от типизации

```python
from typing import Any

def f(x: Any) -> Any:
    return x
```

`Any` совместим со всем. Используй когда:
- интегрируешься с нетипизированным кодом;
- очень динамические сценарии (рефлексия).

⚠️ Не злоупотребляй! `Any` — это «выключить проверку типов для этой переменной».

### object vs Any

`object` — базовый тип для **всего**. `Any` — «специальный тип, совместимый со всем».

Разница:
```python
def f(x: object) -> int:
    return x.upper()    # mypy error: object has no upper

def g(x: Any) -> int:
    return x.upper()    # mypy ok
```

`object` — строгое: можно вызывать только методы object. `Any` — снимает все ограничения.

Используй `object` когда хочешь принять что угодно, но потом проверяешь тип. `Any` — когда отказался от проверки.

---

## 6. Callable — функция как значение

```python
from typing import Callable

def apply(f: Callable[[int, int], int], a: int, b: int) -> int:
    return f(a, b)

apply(lambda x, y: x + y, 1, 2)
```

`Callable[[ArgTypes], ReturnType]`:
- `Callable[[int, str], bool]` — `(int, str) -> bool`.
- `Callable[..., int]` — любые аргументы, возвращает int.
- `Callable[[], None]` — без аргументов, ничего не возвращает.

---

## 7. TypeVar — обобщённые типы

```python
from typing import TypeVar

T = TypeVar("T")

def first(items: list[T]) -> T:
    return items[0]

x: int = first([1, 2, 3])
y: str = first(["a", "b"])
```

`T` — переменная типа. mypy выводит её для каждого вызова. `first` — generic функция.

### Ограничения

```python
from typing import TypeVar

# подкласс какого-то типа:
TNum = TypeVar("TNum", bound=Number)

# один из конкретных:
TStrInt = TypeVar("TStrInt", str, int)
```

---

## 8. Generic-классы

```python
from typing import TypeVar, Generic

T = TypeVar("T")

class Stack(Generic[T]):
    def __init__(self) -> None:
        self.items: list[T] = []
    def push(self, item: T) -> None:
        self.items.append(item)
    def pop(self) -> T:
        return self.items.pop()

s: Stack[int] = Stack()
s.push(1)
s.push("a")    # mypy error
```

С Python 3.12+ — синтаксис проще:
```python
class Stack[T]:        # PEP 695
    def __init__(self) -> None:
        self.items: list[T] = []
```

---

## 9. Protocol — структурная типизация (duck typing)

```python
from typing import Protocol

class HasLen(Protocol):
    def __len__(self) -> int: ...

def total_length(items: list[HasLen]) -> int:
    return sum(len(x) for x in items)

total_length(["abc", [1, 2], (1,)])    # OK — все имеют __len__
```

Protocol = «структурный тип». Класс не обязан **наследоваться** от Protocol — достаточно иметь нужные методы. Это и есть «duck typing с проверкой».

### `runtime_checkable` — для isinstance

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class Drawable(Protocol):
    def draw(self) -> None: ...

class Circle:
    def draw(self) -> None: ...

c = Circle()
isinstance(c, Drawable)    # True — проверка по структуре
```

---

## 10. Literal — точные значения

```python
from typing import Literal

def open_file(mode: Literal["r", "w", "a"]) -> None:
    ...

open_file("r")     # OK
open_file("rw")    # mypy error
```

Полезно для:
- enum-подобных параметров;
- перегрузок (overload).

---

## 11. TypedDict — словарь с фиксированными ключами

```python
from typing import TypedDict

class User(TypedDict):
    name: str
    age: int
    email: str

u: User = {"name": "Alice", "age": 30, "email": "a@b.com"}
```

Полезно для JSON-данных и старого кода с dict-ами вместо классов.

```python
class User(TypedDict, total=False):    # total=False делает все поля Optional
    name: str
    age: int
```

---

## 12. NotRequired, Required (3.11+)

```python
from typing import TypedDict, NotRequired, Required

class User(TypedDict):
    name: Required[str]
    age: NotRequired[int]    # необязательное
```

Точечная настройка обязательности.

---

## 13. NewType — type alias с уникальностью

```python
from typing import NewType

UserId = NewType("UserId", int)
PostId = NewType("PostId", int)

def get_user(user_id: UserId) -> User: ...

uid = UserId(42)
get_user(uid)        # OK
get_user(42)          # mypy error — int ≠ UserId
```

Помогает не перепутать «тот же int, но другая семантика».

В рантайме — обычный int.

---

## 14. type-aliases

```python
# простой:
JSON = dict[str, "JSON"] | list["JSON"] | str | int | float | bool | None

# через TypeAlias (3.10+):
from typing import TypeAlias
JSON: TypeAlias = dict[str, "JSON"] | list["JSON"] | str | int | float | bool | None

# через type (3.12+):
type JSON = dict[str, JSON] | list[JSON] | str | int | float | bool | None
```

Type alias — переиспользуемое имя для сложного типа.

---

## 15. Type narrowing

mypy и pyright **сужают** тип после проверок:

```python
def f(x: int | None) -> int:
    if x is None:
        return 0
    return x + 1    # mypy знает: x здесь int, не int | None

def g(x: int | str) -> str:
    if isinstance(x, int):
        return str(x)    # x: int
    return x             # x: str

# match (3.10+):
def h(x: int | str | list[int]) -> str:
    match x:
        case int():
            return str(x)
        case str():
            return x
        case list():
            return ",".join(str(i) for i in x)
```

### TypeGuard

```python
from typing import TypeGuard

def is_str_list(val: list[object]) -> TypeGuard[list[str]]:
    return all(isinstance(x, str) for x in val)

def f(items: list[object]) -> None:
    if is_str_list(items):
        # mypy знает: items: list[str]
        for s in items:
            print(s.upper())
```

`TypeGuard` — кастомная функция для сужения типа.

---

## 16. Overload — перегрузки

```python
from typing import overload

@overload
def parse(x: int) -> int: ...
@overload
def parse(x: str) -> str: ...

def parse(x: int | str) -> int | str:
    if isinstance(x, int):
        return x * 2
    return x.upper()

a: int = parse(5)         # mypy знает: int
b: str = parse("hi")      # mypy знает: str
```

Перегрузки — для функций, у которых тип возврата зависит от типа аргумента.

---

## 17. ClassVar и Final

```python
from typing import ClassVar, Final

class Foo:
    instance_var: int = 0           # переменная экземпляра
    class_var: ClassVar[int] = 0    # переменная класса

CONSTANT: Final[int] = 42
CONSTANT = 100    # mypy error
```

`ClassVar` — атрибут только класса, не экземпляров.
`Final` — нельзя переопределить.

---

## 18. Async и типы

```python
async def fetch(url: str) -> str:
    ...

# Awaitable:
from typing import Awaitable
def get_fetcher() -> Awaitable[str]: ...

# AsyncIterator:
from typing import AsyncIterator
async def stream() -> AsyncIterator[bytes]:
    yield b"chunk"

# Coroutine[Any, Any, T] — детальный тип:
from typing import Coroutine
c: Coroutine[None, None, str] = fetch("...")
```

---

## 19. Декораторы — типизация

Простой декоратор без изменения сигнатуры:
```python
from typing import TypeVar, Callable
F = TypeVar("F", bound=Callable[..., Any])

def log(func: F) -> F:
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        print(f"calling {func.__name__}")
        return func(*args, **kwargs)
    return wrapper    # type: ignore[return-value]
```

С 3.10+ — `ParamSpec` для точного сохранения сигнатуры:
```python
from typing import ParamSpec, TypeVar, Callable
P = ParamSpec("P")
T = TypeVar("T")

def log(func: Callable[P, T]) -> Callable[P, T]:
    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        print(f"calling")
        return func(*args, **kwargs)
    return wrapper
```

ParamSpec идеально подходит для декораторов, передающих все аргументы дальше.

---

## 20. Self (3.11+)

```python
from typing import Self

class Container:
    @classmethod
    def build(cls) -> Self:
        return cls()
    
    def chain(self) -> Self:
        return self
```

`Self` означает «тип текущего класса». В подклассах автоматически становится подклассом.

---

## 21. dataclass и типы

`@dataclass` использует аннотации для генерации `__init__`:
```python
from dataclasses import dataclass

@dataclass
class User:
    name: str
    age: int = 0
    tags: list[str] = field(default_factory=list)
```

Это типы и для пользователя, и для mypy.

---

## 22. Pydantic — типы в рантайме

`pydantic` — библиотека, которая **проверяет** типы в рантайме (в отличие от mypy):

```python
from pydantic import BaseModel

class User(BaseModel):
    name: str
    age: int

User(name="Alice", age="30")    # автоматически конвертирует "30" → 30
User(name=123)                   # ValidationError
```

Стандарт для:
- API-схем (FastAPI использует pydantic);
- сериализации/десериализации;
- валидации входных данных.

---

## 23. mypy — статическая проверка

```bash
pip install mypy
mypy script.py
```

Нашёл ошибки:
```
script.py:5: error: Argument 1 to "f" has incompatible type "str"; expected "int"
```

Конфигурация в `pyproject.toml`:
```toml
[tool.mypy]
strict = true
python_version = "3.12"
```

`strict = true` включает все строгие проверки. Хороший дефолт для нового кода.

### `# type: ignore`

```python
result = some_untyped_thing()    # type: ignore
```

Подавляет ошибку mypy для этой строки. Используй экономно.

### Коментарии типов

Старый стиль (когда нельзя `:` — например, в очень старом Python):
```python
x = []  # type: list[int]
def f(x):  # type: (int) -> int
    ...
```

Не используй в новом коде, есть аннотации.

---

## 24. pyright и pylance

`pyright` (Microsoft) — другой type checker, обычно **строже и быстрее** mypy. Используется в VS Code Python (Pylance).

```bash
pip install pyright
pyright script.py
```

Многие проекты используют оба для разной строгости.

---

## 25. Что современный код должен иметь

```python
from __future__ import annotations    # для совместимости старых версий

from collections.abc import Iterable
from typing import Optional

def process(items: Iterable[int], factor: Optional[int] = None) -> list[int]:
    f = factor or 1
    return [x * f for x in items]
```

Используй:
- встроенные дженерики (`list[int]`, не `List[int]`);
- `X | None` вместо `Optional[X]` (3.10+);
- `collections.abc` вместо `typing` для протоколов (Iterable, Iterator, Mapping);
- mypy strict в CI.

---

## 26. Типичные ошибки

### `List` vs `list`

```python
def f(x: list):    # ⚠️ нет параметра типа
def g(x: list[int]):    # ✅
```

### Mutable default

```python
def f(x: list[int] = []):    # ⚠️ default — всё ещё shared
```

Используй `Optional[list[int]] = None` и инициализируй внутри.

### Любой тип = Any

```python
def f(x):    # x: Any (если строгие настройки — error)
```

Включай `disallow_untyped_defs = true` чтобы mypy ругался.

### Тип объявлен но не подходит

```python
def f() -> int:
    return "abc"    # mypy error
```

Прислушивайся.

### Игнорирование протоколов

```python
def f(x: Sized) -> int:    # лучше: Sized из collections.abc
    return len(x)

# не:
def f(x: list) -> int:
    return len(x)    # принимает только list, хотя достаточно __len__
```

Делай минимально-достаточный тип.

---

## 27. Что нужно запомнить

- Аннотации не проверяются в рантайме; нужен mypy/pyright.
- Современный синтаксис: `list[int]`, `X | None`, `dict[str, list[int]]`.
- `TypeVar` для generic функций; `Generic[T]` для generic классов.
- `Protocol` — структурная типизация; `@runtime_checkable` для isinstance.
- `Literal["x", "y"]` — фиксированные значения.
- `TypedDict` — типизированные dict-ы.
- `NewType` — semantic-aliasing для int/str.
- `ParamSpec` для типизации декораторов с сохранением сигнатуры.
- Type narrowing через isinstance, match, TypeGuard.
- `Self` для возврата `self`-типа.
- pydantic — типы в рантайме (валидация).
- В современном коде — mypy strict в CI обязателен.

После типизации — глубоко в декораторы. Параметризованные, классовые, для типизации, в реальных библиотеках.
