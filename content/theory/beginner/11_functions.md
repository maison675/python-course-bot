# Функции — от 0 до 100%

Функция — это **именованный блок кода с входами и выходом**, который можно переиспользовать. Без функций ты пишешь скрипт-простыню. С функциями — структурированную программу. Любой сложный код состоит из десятков и сотен маленьких функций. Поэтому понимать функции по-настоящему — это половина программирования.

В Python функции — особые: они **первоклассные объекты**. Их можно передавать как аргументы, возвращать из других функций, хранить в списках. На этом построены декораторы, замыкания, функциональный стиль. Разберём всё.

---

## 1. Базовый синтаксис

```python
def greet(name):
    print(f"Hello, {name}!")

greet("Alice")    # Hello, Alice!
```

Структура:
- `def <имя>(<параметры>):` — заголовок.
- Тело функции — отступ 4 пробела.
- `return <значение>` — выход с возвратом значения. Если нет — функция вернёт `None`.

```python
def add(a, b):
    return a + b

result = add(2, 3)    # 5
```

### Вызов

Функция — объект. Вызов — это применение оператора `()`:
```python
print(add)          # <function add at 0x...>
print(add(2, 3))    # 5

f = add             # f теперь ссылается на ту же функцию
print(f(2, 3))      # 5
```

---

## 2. Параметры и аргументы

Тонкое различие:
- **Параметр** — имя в `def f(x):` — то, что объявлено.
- **Аргумент** — значение в `f(5)` — то, что передано.

В обиходе путают, но идея ясна.

### Позиционные

```python
def f(a, b, c):
    print(a, b, c)

f(1, 2, 3)       # 1 2 3 — по порядку
```

### Именованные (keyword)

```python
f(c=3, a=1, b=2)    # 1 2 3 — по имени, в любом порядке
```

Можно смешивать:
```python
f(1, c=3, b=2)      # сначала позиционные, потом именованные
f(c=3, 1, b=2)      # SyntaxError — позиционный после именованного
```

### Параметры по умолчанию

```python
def greet(name, greeting="Hello"):
    print(f"{greeting}, {name}!")

greet("Alice")                  # Hello, Alice!
greet("Bob", "Hi")              # Hi, Bob!
greet("Carol", greeting="Hey")  # Hey, Carol!
```

Параметры с default — **в конце** списка:
```python
def f(a, b=10, c):    # SyntaxError — non-default после default
    ...
```

### Mutable default — главный «гадский» баг

```python
def f(x, lst=[]):           # ⚠️
    lst.append(x)
    return lst

print(f(1))    # [1]
print(f(2))    # [1, 2] — !!! не [2]
```

`[]` создаётся **один раз** во время определения, и переиспользуется. Решение:
```python
def f(x, lst=None):
    if lst is None:
        lst = []
    lst.append(x)
    return lst
```

Это самый часто упоминаемый «gotcha» в Python.

---

## 3. *args и **kwargs

### `*args` — переменное число позиционных

```python
def sum_all(*nums):
    total = 0
    for n in nums:
        total += n
    return total

sum_all(1, 2, 3)        # 6
sum_all(1, 2, 3, 4, 5)  # 15
```

`args` — это **tuple** всех «лишних» позиционных аргументов. Имя `args` — конвенция, можно любое: `*nums`, `*items`.

### `**kwargs` — переменное число именованных

```python
def info(**opts):
    for k, v in opts.items():
        print(f"{k}: {v}")

info(name="Alice", age=30, city="Moscow")
```

`kwargs` — это **dict** именованных аргументов.

### Вместе

```python
def f(a, b, *args, **kwargs):
    print(a, b, args, kwargs)

f(1, 2, 3, 4, x=10, y=20)
# 1 2 (3, 4) {'x': 10, 'y': 20}
```

### Распаковка при вызове

```python
def f(a, b, c):
    print(a, b, c)

args = [1, 2, 3]
f(*args)              # f(1, 2, 3)

kwargs = {"a": 1, "b": 2, "c": 3}
f(**kwargs)           # f(a=1, b=2, c=3)
```

`*` распаковывает iterable в позиционные, `**` распаковывает dict в именованные. Полезно для проброса аргументов:
```python
def wrapper(*args, **kwargs):
    log("calling original")
    return original(*args, **kwargs)
```

---

## 4. Только-позиционные и только-именованные

С Python 3.8 — синтаксис `/` и `*` для разделения видов параметров.

### Только-позиционные (до `/`)

```python
def f(a, b, /, c):
    ...

f(1, 2, 3)        # OK
f(1, 2, c=3)      # OK
f(a=1, b=2, c=3)  # TypeError — a, b только позиционные
```

Используется для имён, которые не должны быть API (например, `pow(x, y)` — нельзя `pow(x=2, y=3)`).

### Только-именованные (после `*`)

```python
def f(a, *, b, c):
    ...

f(1, b=2, c=3)    # OK
f(1, 2, 3)        # TypeError — b, c только именованные
```

Используется для опциональных флагов: чтобы вызывающий явно писал `verbose=True`, а не `f(1, True)`.

```python
def open_file(path, *, encoding="utf-8", errors="strict"):
    ...
```

### Все три зоны

```python
def f(a, b, /, c, d, *, e, f):
    ...
```

- `a, b` — только позиционные;
- `c, d` — позиционные или именованные;
- `e, f` — только именованные.

В реальности используется редко, но в стандартной библиотеке встречается.

---

## 5. return

### Возврат значения

```python
def add(a, b):
    return a + b
```

### Несколько значений (через tuple)

```python
def divmod_(a, b):
    return a // b, a % b      # возвращает tuple

quot, rem = divmod_(10, 3)    # 3, 1
```

### Без return

Если функция не делает `return`, она автоматически возвращает `None`:
```python
def silent():
    print("hi")
result = silent()         # 'hi'
print(result)             # None
```

### Ранние return (early return)

```python
def divide(a, b):
    if b == 0:
        return None        # ранний выход
    return a / b
```

Это лучше, чем большой `if/else` в конце.

### return ничего не делает после себя

```python
def f():
    return 5
    print("never executes")    # недостижимо
```

---

## 6. Локальные и глобальные переменные

```python
x = 10                  # global

def f():
    x = 20              # это другая, локальная x
    print(x)

f()                     # 20
print(x)                # 10
```

Функция создаёт **свою область видимости**. Имена внутри функции — локальные, не видны снаружи.

### Чтение global

```python
y = 100

def f():
    print(y)      # читать глобал — можно
```

### Запись в global

```python
y = 100

def f():
    y = 200     # это новая локальная y, глобал не меняется

f()
print(y)        # 100
```

Чтобы менять глобал — `global`:
```python
y = 100

def f():
    global y
    y = 200

f()
print(y)        # 200
```

`global` обычно — **плохая практика**. Лучше передавать значения через параметры и возвращать через return.

### LEGB — порядок поиска имени

Python ищет имя в порядке:
1. **L**ocal (локальная функция)
2. **E**nclosing (объемлющая функция, для замыканий)
3. **G**lobal (модуль)
4. **B**uilt-in (встроенные `print`, `len` и т.д.)

```python
x = "global"

def outer():
    x = "enclosing"
    def inner():
        x = "local"
        print(x)        # local
    inner()
    print(x)            # enclosing

outer()
print(x)                # global
```

### nonlocal — для замыканий

```python
def make_counter():
    count = 0
    def inc():
        nonlocal count    # модифицировать enclosing
        count += 1
        return count
    return inc

c = make_counter()
print(c())   # 1
print(c())   # 2
print(c())   # 3
```

`nonlocal` — модификация переменной из объемлющей функции. Без него `count += 1` создаст новую локальную count и упадёт с UnboundLocalError.

---

## 7. Замыкания

Когда вложенная функция использует переменную из объемлющей — это **замыкание**:
```python
def make_adder(n):
    def add(x):
        return x + n          # n из объемлющей области
    return add

add5 = make_adder(5)
print(add5(3))    # 8
print(add5(10))   # 15

add10 = make_adder(10)
print(add10(3))   # 13
```

`add5` «помнит» n=5, `add10` помнит n=10 — каждый вызов `make_adder` создаёт **отдельное** замыкание со своим n.

Замыкания — основа декораторов, генераторов callback-функций, частичного применения.

---

## 8. lambda — анонимные функции

```python
square = lambda x: x**2
print(square(5))    # 25
```

Эквивалент:
```python
def square(x):
    return x**2
```

Lambda — **выражение**, не statement. Может содержать только одно выражение, без `if/else` (но можно тернарный), без `return` (значение выражения и есть результат), без многострочного тела.

### Когда нужны

```python
sorted(words, key=lambda w: w.lower())
filter(lambda x: x > 0, data)
map(lambda x: x*2, data)
```

Для одноразовых маленьких функций. Для серьёзных — обычная `def`.

### Когда НЕ нужны

```python
square = lambda x: x**2     # ⚠️ присваивать lambda — антипаттерн
def square(x): return x**2  # ✅ так читабельнее
```

Lambda без имени имеет смысл только когда **передаётся куда-то** — sorted, max, filter, map.

---

## 9. Аннотации типов

```python
def add(a: int, b: int) -> int:
    return a + b
```

Это **подсказки** типов. Они:
- хранятся в `add.__annotations__`;
- **не проверяются** интерпретатором — `add("hi", "there")` работает;
- проверяются `mypy`, `pyright` (внешние инструменты);
- помогают IDE с автодополнением и выявлением ошибок.

### Сложные типы

```python
from typing import Optional, List, Dict, Callable, Union

def parse(text: str) -> Optional[int]:
    try:
        return int(text)
    except ValueError:
        return None

def combine(items: List[str], sep: str = " ") -> str:
    return sep.join(items)

def process(callback: Callable[[int], str]) -> None:
    print(callback(42))
```

С Python 3.9 — встроенные типы можно использовать напрямую:
```python
def f(items: list[str]) -> dict[str, int]:    # ✅ 3.9+
def f(items: List[str]) -> Dict[str, int]:    # старый стиль
```

С Python 3.10 — `|` вместо `Union`:
```python
def f(x: int | None) -> int:    # ✅ 3.10+
def f(x: Optional[int]) -> int:  # старый стиль
```

Подробно — в продвинутом треке («Типизация по-взрослому»).

---

## 10. Docstrings

Документация функции, первая строка после `def`:

```python
def add(a, b):
    """Возвращает сумму двух чисел.
    
    Args:
        a: первое число
        b: второе число
    
    Returns:
        сумма a + b
    """
    return a + b

print(add.__doc__)
help(add)
```

Стили:
- **Google** — `Args:`, `Returns:`, `Raises:`.
- **NumPy** — `Parameters\n----------`.
- **reStructuredText** — `:param a:`, `:returns:`.

Выбирай один стиль для проекта. Docstrings — основа автогенерируемой документации (Sphinx, mkdocs).

---

## 11. Функция как объект

В Python функции — **первоклассные**. Можно делать всё что с любым другим объектом.

### Передавать как аргумент

```python
def greet(name):
    return f"Hi, {name}"

def apply(func, arg):
    return func(arg)

apply(greet, "Alice")      # 'Hi, Alice'
```

Это используется везде: `sorted(key=...)`, `map(...)`, callback'и в GUI.

### Возвращать из функции

```python
def make_multiplier(k):
    def multiply(x):
        return x * k
    return multiply

double = make_multiplier(2)
triple = make_multiplier(3)
print(double(5))    # 10
print(triple(5))    # 15
```

Это и есть замыкания, и фабрика функций.

### Хранить в коллекциях

```python
operations = {
    "add": lambda a, b: a + b,
    "mul": lambda a, b: a * b,
    "sub": lambda a, b: a - b,
}

print(operations["add"](2, 3))     # 5
print(operations["mul"](2, 3))     # 6
```

Часто заменяет if/elif:
```python
def execute(op, a, b):
    return operations[op](a, b)
```

---

## 12. Декораторы (короткое введение)

Декоратор — функция, **оборачивающая** другую функцию:

```python
def logger(func):
    def wrapper(*args, **kwargs):
        print(f"Calling {func.__name__}")
        result = func(*args, **kwargs)
        print(f"Returned {result}")
        return result
    return wrapper

@logger
def add(a, b):
    return a + b

add(2, 3)
# Calling add
# Returned 5
# 5
```

`@logger` — это сахар для:
```python
def add(a, b):
    return a + b
add = logger(add)
```

Декораторы используют замыкания: `wrapper` помнит `func`. Подробно — в продвинутом треке.

Стандартные полезные декораторы:
- `@functools.lru_cache` — кеширование результатов.
- `@functools.wraps` — внутри своего декоратора, чтобы wrapper «выглядел как» оборачиваемая функция.
- `@property`, `@staticmethod`, `@classmethod` — для классов.

---

## 13. Чистые функции и побочные эффекты

**Чистая функция**:
- результат зависит **только** от аргументов;
- не модифицирует ничего вне себя (нет побочных эффектов);
- одни аргументы → один результат, всегда.

```python
def add(a, b):
    return a + b           # чистая

counter = 0
def impure():
    global counter
    counter += 1           # ⚠️ побочный эффект
    return counter
```

Чистые функции легко тестировать, кешировать, распараллеливать. Стремись писать чистые везде, где возможно.

---

## 14. Рекурсия

Функция вызывает саму себя:
```python
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)

print(factorial(5))    # 120
```

Подробно — в следующей теме.

---

## 15. Типичные ошибки

### Mutable default

См. секцию 2.

### Забыл return

```python
def double(x):
    x * 2     # вычислил, но не вернул

print(double(5))    # None
```

### Изменение глобальной переменной без global

```python
counter = 0
def inc():
    counter += 1    # UnboundLocalError
```

### Использование global на каждый чих

`global` обычно означает плохой дизайн. Возвращай значения, передавай через параметры.

### Слишком много параметров

Если у функции 10 параметров — это знак что нужен класс или dataclass:
```python
def make_user(name, age, email, city, phone, ...):    # ⚠️
def make_user(profile: UserProfile):                   # ✅
```

### Lambda с побочными эффектами

```python
f = lambda x: print(x) or x    # ⚠️ хак — print возвращает None, or x пропускает
```

Не делай так. Используй обычную def.

### return после ошибки

```python
def f():
    if error:
        raise ValueError(...)
        return None     # недостижимо после raise
```

После `raise` или `return` — код не выполняется. IDE подскажет.

---

## 16. Что нужно запомнить

- `def` создаёт функцию-объект, можно передавать как аргумент.
- Параметры могут быть позиционные, именованные, `*args`, `**kwargs`, default.
- Mutable default — баг.
- LEGB: local → enclosing → global → built-in.
- `global` — для записи глобал-переменной, `nonlocal` — для записи enclosing.
- Замыкания — функция «помнит» enclosing.
- Lambda — анонимные функции для одноразовых случаев.
- Type hints не проверяются в рантайме, но помогают IDE и mypy.
- Docstrings — для документации.
- Чистые функции — без побочных эффектов; их легче тестировать.

После функций ты можешь структурировать любой код. Дальше — рекурсия (особый вид функций), потом файлы, исключения, и ООП.
