# Comprehensions, lambda, map/filter — от 0 до 100%

Это финальная тема начинающего трека. Здесь Python показывает свою элегантность: то, что в C/Java делается циклами и временными переменными, в Python пишется одной строкой.

Comprehensions — это **сжатый синтаксис** для построения списков, словарей, множеств, генераторов из других итерируемых. `[x*2 for x in nums]` вместо `result = []; for x in nums: result.append(x*2)`. Lambda и map/filter — функциональный стиль для тех же задач.

Это не просто «короче писать». Это **другой способ мышления** — декларативный («что нужно получить») вместо императивного («как это делать»). Профи Python пишут половину кода в этом стиле.

---

## 1. List comprehension — основа

Базовый синтаксис:
```python
[expression for item in iterable]
```

Эквивалент:
```python
result = []
for item in iterable:
    result.append(expression)
```

Примеры:
```python
[x**2 for x in range(5)]          # [0, 1, 4, 9, 16]
[x.upper() for x in ["a", "b"]]   # ['A', 'B']
[len(s) for s in ["hello", "hi"]] # [5, 2]
[i for i in range(10)]            # [0, 1, 2, ..., 9]
```

### С фильтром

```python
[expression for item in iterable if condition]
```

Эквивалент:
```python
result = []
for item in iterable:
    if condition:
        result.append(expression)
```

```python
[x for x in range(10) if x % 2 == 0]    # [0, 2, 4, 6, 8]
[x**2 for x in range(10) if x > 3]      # [16, 25, 36, 49, 64, 81]
[w for w in words if len(w) > 3]
```

### С тернарным в выражении

```python
[x if x >= 0 else -x for x in nums]   # абсолютные значения
[("even" if x % 2 == 0 else "odd") for x in nums]
```

⚠️ Не путай:
- `if-else` ВНУТРИ выражения — выбор значения.
- `if` В КОНЦЕ — фильтр (только if, не else).

```python
[x for x in data if x > 0]              # фильтр: оставить положительные
[x if x > 0 else 0 for x in data]       # все: положительные или 0
```

### Несколько `for` (вложенные)

```python
[(x, y) for x in range(3) for y in range(3)]
# [(0,0), (0,1), (0,2), (1,0), (1,1), (1,2), (2,0), (2,1), (2,2)]
```

Эквивалент:
```python
result = []
for x in range(3):
    for y in range(3):
        result.append((x, y))
```

С фильтром:
```python
[(x, y) for x in range(5) for y in range(5) if x + y == 4]
# [(0,4), (1,3), (2,2), (3,1), (4,0)]
```

### Развёртывание вложенных

```python
matrix = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
flat = [x for row in matrix for x in row]
# [1, 2, 3, 4, 5, 6, 7, 8, 9]
```

Порядок `for`-ов важен: первый — внешний цикл.

### Не злоупотребляй вложенностью

```python
# плохо — 3 уровня вложенности нечитаемо:
[[[i*j*k for k in range(3)] for j in range(3)] for i in range(3)]

# лучше — обычный цикл:
result = []
for i in range(3):
    for j in range(3):
        for k in range(3):
            result.append(i*j*k)
```

Правило большого пальца: не больше 2 `for`-ов в одной comprehension.

---

## 2. Dict comprehension

```python
{key_expr: value_expr for item in iterable}
```

```python
{x: x**2 for x in range(5)}
# {0: 0, 1: 1, 2: 4, 3: 9, 4: 16}

{name: len(name) for name in ["Alice", "Bob"]}
# {'Alice': 5, 'Bob': 3}

# Из существующего dict — переворот ключей и значений:
{v: k for k, v in d.items()}

# Фильтр:
{k: v for k, v in d.items() if v > 0}

# Объединить два списка:
{k: v for k, v in zip(keys, values)}
```

### Группировка через словарь

```python
# Считаем частоту слов:
freq = {}
for w in words:
    freq[w] = freq.get(w, 0) + 1

# через comprehension не очень элегантно — лучше Counter:
from collections import Counter
freq = Counter(words)
```

---

## 3. Set comprehension

```python
{expr for item in iterable}
```

```python
{x % 3 for x in range(10)}    # {0, 1, 2}
{w.lower() for w in words}    # уникальные в нижнем регистре
{x**2 for x in range(-3, 4)}  # {0, 1, 4, 9}
```

Set comprehension отличается от dict отсутствием `:`. Если в `{}` есть `:` — dict; если нет — set.

```python
{x for x in range(5)}     # set: {0, 1, 2, 3, 4}
{x: 0 for x in range(5)}  # dict: {0: 0, 1: 0, 2: 0, 3: 0, 4: 0}
```

---

## 4. Generator expression

```python
(expr for item in iterable)
```

Не строит список, а возвращает **генератор** — ленивый итератор:
```python
gen = (x**2 for x in range(1_000_000))
print(gen)             # <generator object ...>
print(next(gen))       # 0
print(next(gen))       # 1

sum(gen)               # считает по одному, не строит список
```

Когда использовать:
- большие данные, не помещаются в память;
- нужна одноразовая итерация (sum, max, any, all);
- передаёшь в функцию как «поток».

```python
# плохо — список в миллион элементов:
sum([x**2 for x in range(1_000_000)])

# хорошо — генератор:
sum(x**2 for x in range(1_000_000))
```

Скобки можно опустить, если generator — единственный аргумент:
```python
sum(x**2 for x in range(10))           # OK
sum((x**2 for x in range(10)), 100)    # явные скобки нужны
```

---

## 5. Когда comprehension, когда обычный цикл

### Comprehension хорош когда:

- одно простое преобразование;
- одна простая фильтрация;
- результат нужно **собрать** в коллекцию.

```python
[x*2 for x in nums]
{k: v for k, v in items}
[w for w in words if w.startswith("py")]
```

### Цикл лучше когда:

- несколько действий внутри;
- нужны побочные эффекты (логирование, обновление состояния);
- сложная логика.

```python
# плохо — comprehension с побочным эффектом:
[print(x) or x for x in data]    # ⚠️

# хорошо — обычный цикл:
for x in data:
    print(x)
```

```python
# плохо — слишком сложная логика:
[parse(x) for x in items if validate(x) and not exists(x)]    # читать тяжело

# лучше:
result = []
for x in items:
    if validate(x) and not exists(x):
        result.append(parse(x))
```

---

## 6. lambda — анонимные функции

```python
lambda parameters: expression
```

Эквивалент:
```python
def name(parameters):
    return expression
```

```python
square = lambda x: x ** 2
add = lambda a, b: a + b
abs_val = lambda x: x if x >= 0 else -x

square(5)    # 25
add(3, 4)    # 7
```

Lambda — это **выражение**, не **statement**:
- одна строка;
- одно выражение (нет statements: if, for, return, ...);
- может содержать тернарный.

### Когда нужны lambda

Главное применение — **передавать функцию как аргумент**:

```python
sorted(words, key=lambda w: w.lower())
sorted(people, key=lambda p: p.age)
sorted(data, key=lambda x: (-x[1], x[0]))    # по убыванию 2-го, потом по возрастанию 1-го

filter(lambda x: x > 0, data)
map(lambda x: x * 2, data)

# обработчик в GUI:
button.on_click(lambda: print("clicked"))

# default factory:
defaultdict(lambda: [])
```

### Когда НЕ нужны lambda

```python
square = lambda x: x ** 2     # ⚠️ присваивать lambda — антипаттерн
def square(x): return x ** 2  # ✅ или import operator

# вместо lambda x: x[0] — operator.itemgetter(0)
# вместо lambda x: x.name — operator.attrgetter("name")

import operator
sorted(data, key=operator.itemgetter(0))     # быстрее, чем lambda
sorted(people, key=operator.attrgetter("age"))
```

`operator.itemgetter` и `attrgetter` — стандартные функции, заменяющие простые lambda. Часто быстрее.

---

## 7. map

```python
map(func, iterable)
```

Применяет функцию к каждому элементу, возвращает **итератор** (не список!):
```python
list(map(str.upper, ["a", "b", "c"]))      # ['A', 'B', 'C']
list(map(int, ["1", "2", "3"]))            # [1, 2, 3]
list(map(lambda x: x * 2, range(5)))       # [0, 2, 4, 6, 8]
```

С несколькими iterables:
```python
list(map(lambda a, b: a + b, [1, 2, 3], [10, 20, 30]))   # [11, 22, 33]
```

### map vs comprehension

```python
# map:
list(map(lambda x: x ** 2, range(10)))

# comprehension:
[x ** 2 for x in range(10)]
```

В Python **comprehension часто предпочтительнее** — читабельнее, без явной lambda.

`map` уместен когда:
- функция уже есть (готовая, не lambda);
- нужно лениво (но тогда лучше generator expression);
- работа с несколькими iterables.

```python
# естественно с map:
list(map(int, input().split()))    # каждый split-элемент → int

# естественно с comprehension:
[int(x) for x in input().split()]
```

Здесь `map(int, ...)` чуть короче.

---

## 8. filter

```python
filter(predicate, iterable)
```

Оставляет элементы, для которых `predicate(item)` truthy:
```python
list(filter(lambda x: x > 0, [-1, 2, -3, 4]))     # [2, 4]
list(filter(None, [0, 1, "", "a", None, "x"]))    # [1, 'a', 'x'] — все truthy
```

`filter(None, ...)` — особый случай: оставляет truthy элементы.

### filter vs comprehension

```python
# filter:
list(filter(lambda x: x > 0, data))

# comprehension:
[x for x in data if x > 0]
```

Comprehension выигрывает в читаемости почти всегда. `filter` уместен когда predicate — готовая функция:
```python
# уместно:
list(filter(str.isalpha, words))    # только строки из букв
```

---

## 9. reduce — свёртка

```python
from functools import reduce

reduce(lambda a, b: a + b, [1, 2, 3, 4])    # 10
reduce(lambda a, b: a * b, [1, 2, 3, 4])    # 24
```

Применяет функцию накопительно:
```
reduce(f, [a, b, c, d]) = f(f(f(a, b), c), d)
```

С начальным значением:
```python
reduce(lambda a, b: a + b, [1, 2, 3], 100)    # 100 + 1 + 2 + 3 = 106
```

### Для чего использовать

В Python `reduce` **не часто** идиоматичен — обычно есть встроенные:
- сумма: `sum(data)`
- произведение: `math.prod(data)` (3.8+)
- максимум: `max(data)`
- минимум: `min(data)`

`reduce` нужен для **нестандартных** свёрток:
```python
# объединение словарей:
reduce(lambda a, b: {**a, **b}, [{"a":1}, {"b":2}, {"c":3}])

# самая длинная строка:
reduce(lambda a, b: a if len(a) > len(b) else b, words)
```

В современном Python предпочитают цикл — он понятнее:
```python
total = 0
for x in nums:
    total += x
```

Или специализированную функцию.

---

## 10. zip

Параллельная итерация (тоже из «функционального» арсенала):
```python
list(zip([1, 2, 3], ["a", "b", "c"]))    # [(1, 'a'), (2, 'b'), (3, 'c')]

names = ["Alice", "Bob"]
ages = [30, 25]
{name: age for name, age in zip(names, ages)}    # {'Alice': 30, 'Bob': 25}
```

Останавливается на самом коротком. С 3.10+ — `zip(..., strict=True)` для проверки одинаковой длины.

---

## 11. itertools — ещё «выше»

Уже обсуждали в теме циклов. Здесь напомню — мощные функции для работы с итераторами:

```python
from itertools import chain, accumulate, takewhile, groupby, product, combinations

list(chain([1,2], [3,4]))                  # [1, 2, 3, 4]
list(accumulate([1, 2, 3, 4]))             # [1, 3, 6, 10] — кумулятивная сумма
list(takewhile(lambda x: x < 5, [1,2,3,5,1]))   # [1, 2, 3]
list(product("ab", [1, 2]))                # [('a',1), ('a',2), ('b',1), ('b',2)]
list(combinations([1,2,3,4], 2))           # все пары без повторов
```

`itertools` — must-know для серьёзной работы. Заменяет десятки строк цикла одной строкой.

---

## 12. Walrus в comprehension

С Python 3.8 — оператор `:=`:
```python
# вычислить функцию один раз и использовать:
[y for x in data if (y := f(x)) > 0]

# с состоянием:
data = [1, 2, 3, 4, 5]
[total for total in [0] for x in data if (total := total + x)]    # хак, не делай так
```

Полезно когда вычисление дорогое и используется и для фильтра, и для значения:
```python
# плохо — f(x) вычисляется дважды:
[f(x) for x in data if f(x) > 0]

# хорошо:
[y for x in data if (y := f(x)) > 0]
```

---

## 13. Производительность

### Comprehension быстрее explicit loop + append

```python
# медленнее:
result = []
for x in data:
    result.append(x ** 2)

# быстрее:
result = [x ** 2 for x in data]
```

Причина — оптимизированный байткод comprehensions в CPython.

### map/filter лениво — пока не вызовешь list/sum

```python
m = map(f, data)         # ничего не вычислено
total = sum(m)           # вычисляется только сейчас
```

Это удобно для пайплайнов:
```python
result = list(filter(predicate, map(transform, data)))
```

Каждый элемент проходит через всю цепочку, не строя промежуточные списки.

### Generator expression vs list comprehension

```python
# для sum/max/any/all/count — generator лучше:
sum(x for x in data if x > 0)        # без промежуточного списка

# когда результат нужен повторно — list:
positive = [x for x in data if x > 0]
print(len(positive))
print(positive[0])
```

---

## 14. Типичные ошибки

### Перепутали dict и set comprehension

```python
{x for x in range(5)}        # set
{x: 0 for x in range(5)}     # dict
{}                            # пустой dict (НЕ пустое set!)
```

Пустое set — `set()`.

### Многократное вычисление в условии

```python
# плохо — f(x) дважды:
[x for x in data if f(x) > 0 and f(x) < 100]

# хорошо:
[x for x in data if (y := f(x)) > 0 and y < 100]

# или просто:
result = []
for x in data:
    y = f(x)
    if 0 < y < 100:
        result.append(x)
```

### Слишком сложно

```python
# нечитаемо:
[[(y, x) for y in range(x) if y % 2 == 0] for x in range(10) if x > 3]

# лучше — циклами:
result = []
for x in range(10):
    if x <= 3:
        continue
    inner = []
    for y in range(x):
        if y % 2 == 0:
            inner.append((y, x))
    result.append(inner)
```

### Comprehension с побочным эффектом

```python
[print(x) for x in data]    # ⚠️ создаёт список Nones, никому не нужен
```

Используй цикл:
```python
for x in data:
    print(x)
```

Или `list(map(print, data))` — но всё равно странно. Просто цикл.

### list() от map/filter забыл

```python
m = map(int, ["1", "2", "3"])
print(m)              # <map object> — не список!
print(list(m))        # [1, 2, 3]
```

Map/filter возвращают итераторы. Чтобы напечатать или повторно использовать — обернуть в `list()`.

### Generator expression — одноразовый

```python
g = (x for x in range(3))
print(list(g))    # [0, 1, 2]
print(list(g))    # [] — итератор кончился
```

Если нужен повторный обход — `list()` или построй список через comprehension.

---

## 15. Итого: что выбрать

| Задача | Идиома |
|---|---|
| Простое преобразование | `[f(x) for x in data]` |
| Фильтр | `[x for x in data if cond(x)]` |
| Преобразование + фильтр | `[f(x) for x in data if cond(x)]` |
| Словарь по парам | `{k: v for k, v in items}` |
| Уникальные | `{x for x in data}` |
| Лениво для агрегации | `sum(x**2 for x in data)` |
| map с готовой функцией | `map(int, items)` |
| Сложная логика | обычный цикл |
| Несколько действий | обычный цикл |

---

## 16. Что нужно запомнить

- List/dict/set comprehension: `[expr for x in iter]`, `{k:v for ...}`, `{x for ...}`.
- Тернарный `if-else` внутри vs фильтр `if` в конце — разные роли.
- Generator expression `(...)` — ленивый, без промежуточного списка.
- Lambda — для одноразовых маленьких функций; не присваивать.
- `map`, `filter` возвращают итераторы; обернуть в `list()` если нужно увидеть.
- Comprehension часто читабельнее `map`/`filter`.
- `reduce` редко нужен — есть `sum`, `max`, `min`, `math.prod`.
- `itertools` — мощный инструмент: chain, product, combinations, accumulate.
- Не злоупотребляй вложенностью — 1-2 уровня max.

Поздравляю — ты прошёл начинающий трек. У тебя теперь есть **полный** инструментарий для написания реальных программ на Python. Дальше — продвинутый трек, где мы разберёмся, **как Python устроен под капотом**: модель памяти, GIL, метаклассы, async, типизация. Это уровень для собеседований в серьёзные компании и для оптимизации кода.
