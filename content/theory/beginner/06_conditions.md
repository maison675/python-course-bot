# Условия — от 0 до 100%

Условные конструкции — это первый шаг от «программа выполняется построчно» к **программа принимает решения**. Без `if` нет логики; без логики нет программирования. На каждой странице любого Python-кода ты увидишь `if`/`else` — как в банке, в игре, в боте, в нейронной сети — везде.

Кажется, тут разбирать нечего: `if` есть в каждом языке. Но в Python у `if` есть свои нюансы: тернарный оператор, `match/case` (новый в 3.10), правила истинности объектов, защитные (guard) выражения, типичные ошибки с `==` и `is`. Разберём всё.

---

## 1. Базовый if/elif/else

```python
x = 10

if x > 0:
    print("положительное")
elif x < 0:
    print("отрицательное")
else:
    print("ноль")
```

Структура:
- `if <условие>:` — обязательно.
- `elif <условие>:` — 0 или больше веток.
- `else:` — 0 или 1 ветка.
- Тело каждой ветки — отступ 4 пробела (по PEP 8).

Условие — любое выражение. Python **не требует** скобки вокруг условия (как Java/C):
```python
if x > 0:           # ✅
if (x > 0):         # ✅ работает, но избыточно
```

### Без else

`else` опционален:
```python
if x > 0:
    print("положительное")
# программа продолжается
```

Если ни одно условие не True — ни одна ветка не выполняется, программа просто идёт дальше.

### Только if без elif/else

```python
if user.is_admin:
    show_admin_panel()
```

Это один из самых частых паттернов — «опциональная» ветка для редкого случая.

---

## 2. Истинность объектов (truthiness)

Условие в `if` — необязательно `True`/`False`. Python приводит **любой** объект к bool по правилам.

**Falsy объекты:**
- `False`, `None`
- Числовые нули: `0`, `0.0`, `0j`, `Decimal(0)`
- Пустые контейнеры: `""`, `[]`, `{}`, `set()`, `()`, `range(0)`
- Объекты с `__bool__()` → False, или `__len__()` → 0

**Truthy объекты:** всё остальное.

```python
if data:        # True если data непустой/ненулевой
    process(data)

if not name:    # True если name пуст или None
    name = "default"
```

Это **Pythonic**. Не пиши `if len(lst) > 0:` — пиши `if lst:`.

### Как объект «решает», что он truthy

Внутри Python вызывает (по очереди, до первого подходящего):
1. `obj.__bool__()` — должен вернуть True/False.
2. `obj.__len__()` — если > 0, объект truthy.
3. По умолчанию (если ни того, ни другого нет) — объект truthy.

```python
class Container:
    def __init__(self, items):
        self.items = items
    def __bool__(self):
        return bool(self.items)

c = Container([])
if c:           # вызов __bool__ → False
    ...
```

---

## 3. Сравнения и логика

Подробно операторы сравнений (`==`, `<`, `is`, `in`) — в теме «Операторы». Здесь — типичные ошибки и идиомы.

### `==` vs `is`

```python
if x == None:     # ⚠️ работает, но плохой стиль и медленно
if x is None:     # ✅ правильно
```

Для `None`, `True`, `False` — всегда `is`/`is not`. Для остальных значений — `==`.

### Цепочки

```python
if 0 <= x < 10:           # x в диапазоне [0, 10)
    ...

if a == b == c:           # все три равны
    ...
```

В отличие от C/Java, Python поддерживает цепочки сравнений. Используй активно — это читабельнее, чем `if a == b and b == c`.

### Логические операторы

```python
if x > 0 and y > 0:       # оба условия
if x > 0 or y > 0:        # хотя бы одно
if not active:            # отрицание
```

`and` и `or` — короткозамкнутые. Если левая часть всё определяет, правая не вычисляется:
```python
if user is not None and user.is_admin:
    ...
# user.is_admin не пытаемся прочитать если user = None — нет AttributeError
```

Это используется как **защита от None / пустых значений**.

---

## 4. Тернарный оператор

```python
result = "yes" if condition else "no"
```

Эквивалент:
```python
if condition:
    result = "yes"
else:
    result = "no"
```

**Удобство:** одна строка, можно использовать как выражение (например, в return или в аргументах функции).

```python
def label(n):
    return "even" if n % 2 == 0 else "odd"

print(f"Status: {'OK' if ok else 'FAIL'}")

items = [x for x in data if (x if x > 0 else None) is not None]   # хак, но так пишут
```

### Не злоупотребляй вложенностью

```python
# плохо (нечитаемо):
x = "a" if c1 else "b" if c2 else "c" if c3 else "d"

# лучше — обычные if/elif:
if c1:
    x = "a"
elif c2:
    x = "b"
elif c3:
    x = "c"
else:
    x = "d"
```

Однократный тернарный — отлично. Цепочка из трёх — уже сомнительно.

---

## 5. match/case — pattern matching (Python 3.10+)

Современный Python ввёл `match/case` — продвинутый switch с возможностью разбора структур данных.

### Базовый match

```python
def describe(x):
    match x:
        case 0:
            return "zero"
        case 1 | 2 | 3:           # OR-pattern
            return "small"
        case n if n > 100:        # guard
            return "big"
        case _:                   # default
            return "other"
```

### Деструктурирующий match

```python
def handle(point):
    match point:
        case (0, 0):
            return "origin"
        case (x, 0):
            return f"on x-axis at {x}"
        case (0, y):
            return f"on y-axis at {y}"
        case (x, y):
            return f"point ({x}, {y})"
```

### По типам и атрибутам

```python
class Circle:
    def __init__(self, r):
        self.r = r
class Square:
    def __init__(self, side):
        self.side = side

def area(shape):
    match shape:
        case Circle(r=r):
            return 3.14 * r ** 2
        case Square(side=s):
            return s * s
        case _:
            raise ValueError("Unknown shape")
```

### Match по словарю

```python
def handle_event(event):
    match event:
        case {"type": "click", "x": x, "y": y}:
            click(x, y)
        case {"type": "key", "code": code}:
            press(code)
        case {"type": "exit"}:
            quit()
        case _:
            print("неизвестное событие")
```

### Подвохи

- `case Circle(r):` — это **захват**: r — это переменная, в которую кладётся значение. Если хочешь сравнить с уже существующей переменной, используй точку: `case Circle(my_const_r):` — захват, но `case Circle(my.const.r):` — сравнение.
- `case (1, 2):` — точное сравнение тапла, а `case (a, b):` — захват двух элементов.
- `case _` — wildcard, не захватывает.
- Без `case _` или if-в-case в конце, неподходящий вход просто «протекает» дальше без действий.

`match/case` особенно полезен для парсинга DSL, обработки событий, AST. Не нужен для простых проверок — для них достаточно if/elif.

---

## 6. Вложенные if

```python
if x > 0:
    if x < 10:
        print("положительное малое")
    else:
        print("положительное большое")
else:
    print("неположительное")
```

Можно, но обычно это сворачивается в один if или if/elif:
```python
if 0 < x < 10:
    print("положительное малое")
elif x >= 10:
    print("положительное большое")
else:
    print("неположительное")
```

Меньше отступов = легче читать.

### Гард-стиль (early return)

Вместо вложенных проверок — ранние выходы:

**Плохо:**
```python
def process(user):
    if user is not None:
        if user.is_active:
            if user.has_permission:
                # основная логика
                ...
            else:
                return "no permission"
        else:
            return "not active"
    else:
        return "no user"
```

**Хорошо:**
```python
def process(user):
    if user is None:
        return "no user"
    if not user.is_active:
        return "not active"
    if not user.has_permission:
        return "no permission"
    # основная логика без отступов
    ...
```

«Pyramid of doom» (пирамида отступов) — антипаттерн. Раннее возвращение — плоский, читаемый код.

---

## 7. Условные выражения в более широком контексте

### С присваиванием через walrus (`:=`)

```python
if (n := len(data)) > 10:
    print(f"Большой список: {n}")
```

То же что:
```python
n = len(data)
if n > 10:
    print(f"Большой список: {n}")
```

Walrus вошёл в Python 3.8. Удобен в условиях циклов (см. тему «Циклы»).

### in для проверки членства

```python
if x in [1, 2, 3]:        # есть в списке
if "py" in name:          # подстрока
if key in some_dict:      # ключ есть
```

`in` для list/tuple — O(n). Если делаешь много проверок — заведи `set`:
```python
allowed = {"admin", "moderator", "user"}
if role in allowed:       # O(1)
    ...
```

### isinstance

```python
if isinstance(x, int):
    ...
if isinstance(x, (int, float)):    # любой из
    ...
```

Лучше, чем `type(x) == int`, потому что:
- работает с подклассами (наследник int пройдёт isinstance(x, int));
- принимает кортеж типов.

### hasattr / callable

```python
if hasattr(obj, "method"):
    obj.method()

if callable(obj):
    obj()
```

Для **дакТайпинга** («если крякает как утка...»). Используется не часто, но иногда полезно.

---

## 8. Пустой блок: `pass`

Иногда нужна ветка, но без действия:
```python
if x > 0:
    pass         # placeholder, ничего не делает
elif x < 0:
    print("neg")
```

Без `pass` — синтаксическая ошибка (Python требует тело у блока).

Используется как **заглушка** при разработке (потом заменишь на нормальный код), и в некоторых конструкциях (пустой except, абстрактный класс без реализации).

---

## 9. assert — особый вид проверки

```python
def divide(a, b):
    assert b != 0, "Деление на ноль"
    return a / b
```

Эквивалент:
```python
if not (b != 0):
    raise AssertionError("Деление на ноль")
```

Особенности:
- `assert` отключается флагом `-O` при запуске Python: `python -O script.py` — assertions выкидываются.
- Поэтому **не используй для валидации ввода** — на проде их может не быть.
- Используй для **инвариантов**: «здесь не может быть пусто», «индекс точно валидный».
- Полезен в тестах (`pytest` именно на assert строится).

---

## 10. Условия и комбинаторика — `all` и `any`

Иногда нужно проверить условие для каждого элемента списка:

```python
nums = [1, 2, 3, 4]
if all(n > 0 for n in nums):       # все > 0
    print("все положительные")

if any(n > 100 for n in nums):     # есть хотя бы один > 100
    print("есть большое")
```

`all([])` — True (пустое всё подходит).
`any([])` — False.

И они короткозамкнутые: `any` останавливается на первом True, `all` — на первом False.

```python
# проверить, что список отсортирован
all(a <= b for a, b in zip(nums, nums[1:]))
```

---

## 11. Тонкие моменты

### Сравнение float

```python
x = 0.1 + 0.2
if x == 0.3:        # ⚠️ False!
    ...
if abs(x - 0.3) < 1e-9:    # ✅
    ...
import math
if math.isclose(x, 0.3):   # ✅ ещё лучше
    ...
```

Никогда `==` для float, кроме экзотических случаев.

### `if x:` vs `if x is not None:`

Это **разное**:
```python
x = []
if x:               # False (пустой список)
    print("есть")

if x is not None:   # True (список существует)
    print("определён")
```

Если важно различать «не задан» (None) vs «задан, но пуст» — используй `is not None`. Если хочешь «есть какое-то полезное значение» — `if x:`.

### `1 == True` — True

```python
if 1 == True:       # True — bool наследник int
    ...
if 1 is True:       # False — разные объекты
    ...
```

Это иногда удивляет:
```python
[1, 2, 3].count(True)    # 1 — True == 1, но также есть только одна True
[True, True, 1, 1, 2].count(True)    # 4 — True == 1, оба считаются
```

### Default для get()

Часто заменяет `if/else`:
```python
# плохо:
if "key" in d:
    val = d["key"]
else:
    val = "default"

# хорошо:
val = d.get("key", "default")
```

---

## 12. Условия в comprehensions

В comprehension можно фильтровать:
```python
positive = [x for x in nums if x > 0]
```

Или применять разное значение:
```python
labels = ["even" if x % 2 == 0 else "odd" for x in nums]
```

Комбинировать:
```python
positive_labels = ["pos" if x > 0 else "non-pos" for x in nums if x != 0]
```

Подробно — в теме comprehensions.

---

## 13. Типичные ошибки

### Забыл `:` после if

```python
if x > 0
    print("yes")     # SyntaxError
```

В Python двоеточие обязательно.

### Сравнение по длине

```python
if len(lst) > 0:    # ⚠️ многословно
    ...
if lst:             # ✅
    ...
```

Пишут `len(lst) > 0` чаще от привычки из других языков.

### Сравнение строки с int

```python
n = input("число: ")    # n — строка!
if n == 5:              # False всегда — разные типы
    ...
if int(n) == 5:         # ✅
    ...
```

### Используют `=` вместо `==`

```python
if x = 5:    # SyntaxError в Python (но не в C!)
    ...
```

Python тут спасает — нельзя использовать `=` в условии (кроме `:=` walrus, но это другое).

### Логическое или вместо =

```python
def greet(name=None):
    name = name or "Гость"   # если name None или "" — "Гость"
    print(f"Hello, {name}")
```

Это работает, но нюанс: если хочешь различать «не задано» vs «пустая строка», используй `is None`:
```python
name = "Гость" if name is None else name
```

### `if x == True` или `if x is True`

```python
if is_active == True:    # ⚠️ многословно
    ...
if is_active:            # ✅ — лаконично
    ...
```

---

## 14. Условия для разных типов данных

### Числа

```python
if 0 < n <= 100:
if n != 0:
if n & 1:               # нечётное (битовая маска быстрее n % 2)
```

### Строки

```python
if s:                   # непустая
if s.strip():           # не только пробелы
if s.startswith("http://") or s.startswith("https://"):
if s.startswith(("http://", "https://")):    # короче
```

### Списки

```python
if lst:                 # непустой
if x in lst:            # содержит x
if all(x > 0 for x in lst):
```

### Словари

```python
if d:                   # непустой
if "key" in d:          # есть ключ
if d.get("key"):        # ключ есть И значение truthy
```

### None

```python
if x is None:           # точно None
if x is not None:       # не None (но может быть 0, "", [])
```

---

## 15. Что нужно запомнить

- `if/elif/else`, отступ 4 пробела, двоеточие после условия.
- Условие может быть любой объект — действует truthiness.
- `is None` для None, `==` для остальных значений.
- Цепочки сравнений работают: `0 <= x < 10`.
- `and`/`or` короткозамкнуты, возвращают операнд (не True/False).
- Тернарный `a if cond else b` — для одной строки.
- `match/case` (3.10+) — для разбора структур данных.
- Гард-стиль (early return) лучше пирамиды отступов.
- `all()`/`any()` для квантоваторов «все»/«хотя бы один».
- `assert` — для инвариантов, не для пользовательской валидации.
- Не сравнивай float через `==`.

С условиями ты уже можешь писать программы с нетривиальной логикой. Дальше — циклы, и комбинируя их с условиями, ты получишь полный набор управляющих конструкций.
