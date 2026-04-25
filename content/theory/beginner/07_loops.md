# Циклы — от 0 до 100%

Цикл — это «делай это снова и снова, пока не выполнится условие». Без циклов программа линейна: 100 инструкций — 100 действий. С циклами одна инструкция превращается в тысячи действий.

В Python два цикла: `for` и `while`. На вид простые. Под капотом — фундаментальная концепция **итераторов**, которая лежит в основе всего языка: comprehensions, генераторы, обход словарей, чтение файлов, async-операции — всё это итераторы под разными личинами.

---

## 1. for — обход итерируемого

```python
for x in [1, 2, 3]:
    print(x)
```

`for` берёт **итерируемый** объект и идёт по нему по очереди. На каждом шаге `x` принимает следующее значение.

### Что можно «итерировать»

Любой объект, у которого есть `__iter__()`:
- list, tuple, str, set, dict
- range
- file (по строкам)
- generator
- любой свой класс с `__iter__`

```python
for ch in "hello":
    print(ch)        # h, e, l, l, o

for i in range(5):
    print(i)         # 0, 1, 2, 3, 4

for line in open("data.txt"):
    print(line)      # читает файл построчно
```

---

## 2. range — генератор последовательности чисел

```python
range(5)              # 0, 1, 2, 3, 4
range(2, 8)           # 2, 3, 4, 5, 6, 7
range(0, 10, 2)       # 0, 2, 4, 6, 8
range(10, 0, -1)      # 10, 9, 8, ..., 1
range(0)              # пусто
range(5, 5)           # пусто
range(-3, 3)          # -3, -2, -1, 0, 1, 2
```

`range(start, stop, step)`:
- `start` включается, `stop` — нет.
- `step` может быть отрицательным.

`range` — **не список!** Это специальный объект, который **генерирует** числа по требованию, не храня их все в памяти:
```python
range(10**18)         # моментально создаётся
list(range(10**18))   # упадёт по памяти
```

Поэтому если тебе нужен список — `list(range(...))` явно. Для итерации в for — оставляй range.

### `for i in range(len(lst))` — антипаттерн

```python
# плохо:
for i in range(len(lst)):
    print(lst[i])

# хорошо:
for x in lst:
    print(x)
```

Если **нужен индекс** — используй `enumerate`:
```python
for i, x in enumerate(lst):
    print(i, x)
```

`enumerate(start=...)` начинает счёт не с нуля:
```python
for n, line in enumerate(lines, start=1):
    print(f"Строка {n}: {line}")
```

---

## 3. enumerate, zip, reversed

### `enumerate` — индекс + значение

```python
for i, x in enumerate(["a", "b", "c"]):
    print(i, x)
# 0 a
# 1 b
# 2 c
```

### `zip` — параллельная итерация

```python
names = ["Alice", "Bob", "Carol"]
ages = [30, 25, 35]

for name, age in zip(names, ages):
    print(name, age)
# Alice 30
# Bob 25
# Carol 35
```

`zip` останавливается на самой короткой:
```python
list(zip([1, 2, 3], [10, 20]))    # [(1, 10), (2, 20)] — третий потерян
```

С Python 3.10 есть `zip(..., strict=True)` — падает с ValueError если длины разные:
```python
list(zip([1, 2, 3], [10, 20], strict=True))    # ValueError
```

Для трёх и более:
```python
for a, b, c in zip(xs, ys, zs):
    ...
```

### `reversed` — обратный обход

```python
for x in reversed([1, 2, 3]):
    print(x)        # 3, 2, 1
```

Работает с list, tuple, range, str. Для `reversed` нужен либо `__reversed__()`, либо `__len__()` + `__getitem__()`.

### `sorted` для сортированного обхода

```python
for x in sorted(data):
    print(x)

for x in sorted(data, reverse=True):
    print(x)

for w in sorted(words, key=len):
    print(w)        # отсортирован по длине
```

`sorted` всегда возвращает **новый** список. `lst.sort()` — на месте.

---

## 4. while — цикл с условием

```python
n = 0
while n < 5:
    print(n)
    n += 1
```

`while` повторяет тело пока условие `True`. Условие проверяется **перед** каждой итерацией.

### Без счётчика

```python
data = ""
while not data.startswith("END"):
    data = input()
    process(data)
```

### Бесконечный цикл

```python
while True:
    line = input()
    if line == "quit":
        break
    process(line)
```

Класический паттерн для CLI или сервера. `break` — единственный способ выйти.

### Цикл «do-while» — нет в Python

Аналог `do { ... } while (cond)` из C — повторяй хотя бы один раз — в Python нет, эмулируем:

```python
while True:
    do_something()
    if not condition:
        break
```

### Walrus в while (Python 3.8+)

```python
while (chunk := f.read(1024)):
    process(chunk)
```

Раньше:
```python
while True:
    chunk = f.read(1024)
    if not chunk:
        break
    process(chunk)
```

Walrus делает короче и яснее.

---

## 5. break и continue

### `break` — выход из цикла

```python
for x in data:
    if x < 0:
        break        # выходит из цикла полностью
    process(x)
```

`break` выходит **только из ближайшего** цикла. Из вложенных нужны или флаги, или ранний return из функции.

### `continue` — пропустить итерацию

```python
for x in data:
    if x < 0:
        continue     # пропуск этого x, переход к следующему
    process(x)       # выполнится только для x >= 0
```

### Глубоко вложенные циклы

```python
found = False
for i in range(rows):
    for j in range(cols):
        if matrix[i][j] == target:
            found = True
            break
    if found:
        break
```

Чисто и красиво — вынести в функцию и использовать `return`:
```python
def find(matrix, target):
    for i in range(rows):
        for j in range(cols):
            if matrix[i][j] == target:
                return (i, j)
    return None
```

---

## 6. else у цикла — необычная конструкция

Python поддерживает `else` у цикла:

```python
for x in data:
    if x < 0:
        print("найдено отрицательное!")
        break
else:
    print("всё неотрицательное")
```

`else` выполняется **если цикл завершился нормально**, без `break`. Если был `break` — `else` не выполняется.

Полезно для поиска:
```python
for n in range(2, num):
    if num % n == 0:
        print(f"{num} не простое (делится на {n})")
        break
else:
    print(f"{num} простое")
```

С `while` тоже работает:
```python
while condition:
    ...
else:
    # выполнится, когда condition стала False (без break)
    ...
```

Многим кажется неинтуитивным — пишут редко. Но знать стоит, иногда встречается.

---

## 7. Что под капотом for: итераторы

`for x in obj:` Python переводит в:
```python
iterator = iter(obj)
while True:
    try:
        x = next(iterator)
    except StopIteration:
        break
    # тело цикла
```

`iter(obj)` вызывает `obj.__iter__()` — должен вернуть **итератор**.
`next(it)` вызывает `it.__next__()` — должен вернуть следующее значение или возбудить `StopIteration`.

Итератор — это объект с двумя методами: `__iter__` (возвращает себя) и `__next__` (выдаёт следующее).

```python
lst = [1, 2, 3]
it = iter(lst)
print(next(it))    # 1
print(next(it))    # 2
print(next(it))    # 3
print(next(it))    # StopIteration
```

### Свой итератор

```python
class Counter:
    def __init__(self, max):
        self.max = max
        self.current = 0
    def __iter__(self):
        return self
    def __next__(self):
        if self.current >= self.max:
            raise StopIteration
        self.current += 1
        return self.current

for n in Counter(3):
    print(n)    # 1, 2, 3
```

### Iterable vs Iterator

- **Iterable** — объект, у которого есть `__iter__()`, возвращающий новый итератор. Например, list.
- **Iterator** — объект, который сам ходит. У него `__iter__()` возвращает **себя**, и есть `__next__()`. Например, `iter([1,2,3])`.

```python
lst = [1, 2, 3]      # iterable
it = iter(lst)        # iterator
list(it)              # [1, 2, 3] — пройдено
list(it)              # [] — итератор «израсходован»
```

Итераторы **одноразовые**. Список можно пройти много раз. Поэтому:
```python
def f(data):
    for x in data:           # первый проход
        ...
    for x in data:           # второй проход — будет ли работать?
        ...
```

Если `data` — список, оба прохода сработают. Если `data` — генератор/итератор — второй пройдёт по пустому.

---

## 8. Генераторы

Самый удобный способ создать **свой итератор** — генератор. Это функция с `yield` вместо `return`:

```python
def count_up(max):
    n = 1
    while n <= max:
        yield n
        n += 1

for x in count_up(5):
    print(x)    # 1, 2, 3, 4, 5
```

Генератор:
- ленивый — генерирует значения по требованию;
- запоминает состояние между `yield`;
- занимает мало памяти даже для бесконечной последовательности.

Бесконечный генератор — можно:
```python
def naturals():
    n = 1
    while True:
        yield n
        n += 1

for n in naturals():
    if n > 10:
        break
    print(n)
```

Важно — без `break` цикл будет бесконечным.

### Генераторное выражение

Как list comprehension, но в круглых скобках:
```python
gen = (x**2 for x in range(1_000_000))
sum(gen)        # считает по одному, не строит список
```

Это часто нужно для оптимизации памяти, особенно с `sum`, `max`, `any`, `all`.

```python
# плохо — список из миллиона:
sum([x**2 for x in range(1_000_000)])

# хорошо — генератор:
sum(x**2 for x in range(1_000_000))
```

---

## 9. Полезные функции для итерируемых

Стандартная библиотека:

```python
sum(iterable)              # сумма
max(iterable)              # максимум
min(iterable)              # минимум
len(sequence)              # длина (только если есть __len__)
any(iterable)              # хотя бы один truthy
all(iterable)              # все truthy
sorted(iterable)           # отсортированный список
list(iterable)             # в список
tuple(iterable)            # в кортеж
set(iterable)              # в множество
dict(iterable_of_pairs)    # в словарь

map(func, iterable)        # ленивый, применяет func
filter(predicate, iter)    # ленивый, оставляет где predicate True
zip(*iterables)            # параллельный обход
enumerate(iterable)        # с индексом
reversed(seq)              # обратно
```

`itertools` — модуль с **продвинутыми** итераторами:

```python
import itertools

# бесконечные
itertools.count(10, 2)            # 10, 12, 14, 16, ...
itertools.cycle([1, 2, 3])         # 1, 2, 3, 1, 2, 3, ...
itertools.repeat("hi", 3)          # 'hi', 'hi', 'hi'

# конечные
itertools.chain([1,2], [3,4])      # 1, 2, 3, 4
itertools.islice(gen, 5)           # первые 5
itertools.takewhile(pred, iter)    # пока pred True
itertools.dropwhile(pred, iter)    # пропустить пока pred True
itertools.groupby(iter, key)       # группировать соседние

# комбинаторика
itertools.product([1,2], [3,4])    # [(1,3),(1,4),(2,3),(2,4)]
itertools.permutations([1,2,3])    # все перестановки
itertools.combinations([1,2,3], 2) # все пары без повторов
```

Знание `itertools` — признак уверенного питониста. Многие циклы можно заменить на 1-2 вызова из этого модуля.

---

## 10. Вложенные циклы

```python
for i in range(3):
    for j in range(3):
        print(i, j)
```

Сложность — произведение. Двойной по 1000 — миллион итераций. Тройной — миллиард. Будь осторожен с вложенностью.

### Альтернатива через product

```python
from itertools import product
for i, j in product(range(3), range(3)):
    print(i, j)
```

Меньше отступов — если глубина 3+, читабельнее.

### Матрицы

```python
matrix = [
    [1, 2, 3],
    [4, 5, 6],
    [7, 8, 9],
]
for row in matrix:
    for x in row:
        print(x, end=" ")
    print()
```

С enumerate:
```python
for i, row in enumerate(matrix):
    for j, x in enumerate(row):
        print(f"matrix[{i}][{j}] = {x}")
```

---

## 11. Производительность циклов

Python — медленный язык в чистых циклах. Чем больше работы делает Python в питоновской логике (а не в C-коде встроенных функций) — тем медленнее.

### Идиомы для скорости:

**Векторные операции через numpy** (если работаешь с числами):
```python
import numpy as np
a = np.array([1, 2, 3, 4])
b = np.array([10, 20, 30, 40])
c = a + b              # быстрее, чем for-цикл
```

**Встроенные функции** часто быстрее цикла:
```python
sum(x**2 for x in range(n))   # быстрее, чем накапливать в переменной
```

**Comprehensions** быстрее, чем explicit for + append:
```python
# медленно:
result = []
for x in data:
    if x > 0:
        result.append(x*2)

# быстрее:
result = [x*2 for x in data if x > 0]
```

**Избегай переменных в горячем цикле**:
```python
# медленно — атрибутный доступ каждый раз:
for x in data:
    obj.method(x)

# быстрее — кешируй:
m = obj.method
for x in data:
    m(x)
```

В типичном коде это микрооптимизации. Для огромных циклов (миллионы итераций) — имеет смысл.

---

## 12. Типичные ошибки

### Изменение списка во время итерации

```python
lst = [1, 2, 3, 4, 5]
for x in lst:
    if x % 2 == 0:
        lst.remove(x)        # ⚠️ результат непредсказуем
print(lst)
```

Никогда не модифицируй коллекцию, по которой идёшь. Решения:
- Итерируй по копии: `for x in lst[:]:`
- Собирай новый список: `lst = [x for x in lst if x % 2]`
- Иди по индексам с конца: `for i in range(len(lst)-1, -1, -1):`

### Изменение словаря во время итерации

```python
d = {"a": 1, "b": 2}
for k in d:
    if d[k] == 0:
        del d[k]    # RuntimeError: dictionary changed size during iteration
```

Решение — собрать ключи на удаление, потом удалить:
```python
to_delete = [k for k, v in d.items() if v == 0]
for k in to_delete:
    del d[k]
```

### Itterator уже исчерпан

```python
gen = (x for x in range(3))
print(list(gen))    # [0, 1, 2]
print(list(gen))    # [] — итератор кончился
```

### Off-by-one

```python
for i in range(1, 10):    # 1..9, не до 10!
    ...
```

`range(stop)` не включает stop. Помни.

### Бесконечный цикл

```python
n = 10
while n > 0:
    print(n)
    # забыл n -= 1
```

Добавляй проверку `if iterations > MAX:` или таймаут на крайний случай.

---

## 13. Приёмы

### Список из ввода

```python
n = int(input())
data = [int(input()) for _ in range(n)]
```

### Парсинг таблицы

```python
n = int(input())
matrix = [list(map(int, input().split())) for _ in range(n)]
```

### Накопление

```python
total = 0
for x in data:
    total += x
# или
total = sum(data)
```

### Группировка по чётности

```python
even = [x for x in data if x % 2 == 0]
odd = [x for x in data if x % 2 != 0]
```

### Отсортировать в обратном порядке

```python
for x in sorted(data, reverse=True):
    ...
```

### Найти максимум по критерию

```python
longest = max(words, key=len)
```

---

## 14. Что нужно запомнить

- `for x in iterable:` — общая форма обхода.
- `range(start, stop, step)` — последовательность чисел; не список.
- `enumerate` для индекса, `zip` для параллельной итерации, `reversed` для обратной.
- `while` — пока условие True; `break` — выход, `continue` — пропуск.
- `else` у цикла — выполнится, если не было `break`.
- `for` под капотом — это `iter` + `next` + `StopIteration`.
- Генераторы (`yield`) — ленивые итераторы, не занимают много памяти.
- `itertools` — мощный модуль, заменяет многие циклы.
- Никогда не модифицируй коллекцию, по которой идёшь.
- Comprehensions часто быстрее и читабельнее цикла + append.

После циклов у тебя есть **полный** набор управляющих конструкций: переменные, условия, циклы. Дальше — структуры данных (списки, словари, множества) и функции, на которых строится вся реальная программа.
