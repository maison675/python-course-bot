# Рекурсия — от 0 до 100%

Рекурсия — это когда функция **вызывает саму себя**. Звучит странно: «как функция может вызвать сама себя, если она ещё не закончилась?». Но именно это и делает рекурсию мощной — каждый вызов работает в своей собственной среде, и они складываются стопкой (стеком).

Рекурсия — концепция, которой пугаются новички, но потом понимают: некоторые задачи **естественно** описываются рекурсивно. Деревья, графы, парсеры, фракталы, обход директорий — везде ты встретишь рекурсию.

В этой теме разберём: как она работает «под капотом», когда нужна, когда не нужна (есть предел), как избежать typical pitfalls.

---

## 1. Что такое рекурсия

Канонический пример — факториал:

```
n! = 1, если n = 0 или 1
n! = n * (n-1)! иначе
```

Это математическое **рекурсивное определение**: значение `n!` определяется через `(n-1)!` — то же самое, но «меньше». Программно:

```python
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)

print(factorial(5))    # 120
```

Что происходит в `factorial(5)`:
```
factorial(5)
  → 5 * factorial(4)
    → 5 * 4 * factorial(3)
      → 5 * 4 * 3 * factorial(2)
        → 5 * 4 * 3 * 2 * factorial(1)
          → 5 * 4 * 3 * 2 * 1
        ← возвращается 2
      ← возвращается 6
    ← возвращается 24
  ← возвращается 120
```

Каждый вызов — это **новый кадр стека** (stack frame). Когда вызов завершается — кадр удаляется и управление возвращается.

---

## 2. Два обязательных компонента рекурсии

### 1. Базовый случай (base case)

Условие, при котором функция **не** делает рекурсивный вызов:
```python
if n <= 1:
    return 1
```

Без базового случая — бесконечная рекурсия → **RecursionError**.

### 2. Рекурсивный шаг

Вызов с **«меньшей» задачей**, который должен приближать к базовому случаю:
```python
return n * factorial(n - 1)    # (n-1) меньше n
```

Если шаг не уменьшает — тоже бесконечная рекурсия:
```python
def bad(n):
    return bad(n)    # бесконечно
```

---

## 3. Лимит рекурсии в Python

Python имеет **жёсткий лимит** на глубину рекурсии — обычно **1000** вложенных вызовов:

```python
import sys
print(sys.getrecursionlimit())    # 1000

def deep(n):
    if n == 0:
        return 0
    return deep(n - 1) + 1

deep(1000)    # RecursionError: maximum recursion depth exceeded
```

Это защита: каждый вызов занимает место в стеке (примерно 1-2 КБ), и при глубокой рекурсии стек переполняется → SegFault. Python предпочитает контролируемое исключение.

### Увеличить лимит

```python
import sys
sys.setrecursionlimit(10000)
```

Но это **не решает проблему**. Если задача требует 100 000 вложенных вызовов — нужен **другой алгоритм**, обычно итеративный.

---

## 4. Классические рекурсивные задачи

### Факториал

```python
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)
```

### Числа Фибоначчи

```python
def fib(n):
    if n < 2:
        return n
    return fib(n - 1) + fib(n - 2)

print(fib(10))    # 55
```

⚠️ Эта реализация **экспоненциально** медленная — O(2^n). Подробнее — в секции про мемоизацию.

### Сумма цифр

```python
def digit_sum(n):
    if n == 0:
        return 0
    return n % 10 + digit_sum(n // 10)

print(digit_sum(12345))    # 15
```

### Возведение в степень

```python
def power(base, exp):
    if exp == 0:
        return 1
    return base * power(base, exp - 1)

print(power(2, 10))    # 1024
```

### Длина списка

```python
def length(lst):
    if not lst:
        return 0
    return 1 + length(lst[1:])
```

### Реверс строки

```python
def reverse(s):
    if len(s) <= 1:
        return s
    return reverse(s[1:]) + s[0]

print(reverse("hello"))    # 'olleh'
```

### Палиндром

```python
def is_palindrome(s):
    if len(s) <= 1:
        return True
    if s[0] != s[-1]:
        return False
    return is_palindrome(s[1:-1])
```

### НОД (алгоритм Евклида)

```python
def gcd(a, b):
    if b == 0:
        return a
    return gcd(b, a % b)

print(gcd(48, 18))    # 6
```

### Бинарный поиск

```python
def bsearch(arr, target, lo=0, hi=None):
    if hi is None:
        hi = len(arr) - 1
    if lo > hi:
        return -1
    mid = (lo + hi) // 2
    if arr[mid] == target:
        return mid
    if arr[mid] < target:
        return bsearch(arr, target, mid + 1, hi)
    return bsearch(arr, target, lo, mid - 1)
```

---

## 5. Несколько ветвей рекурсии

Одна функция может делать **несколько** рекурсивных вызовов. Это превращает её в дерево:

```python
def fib(n):
    if n < 2:
        return n
    return fib(n - 1) + fib(n - 2)
```

Каждый вызов вызывает два (если n ≥ 2). Дерево вызовов растёт как 2^n. Поэтому для n=40 уже 1 миллиард вызовов — секунды.

Для таких задач — мемоизация.

---

## 6. Мемоизация

Кешируй уже посчитанные значения:

```python
cache = {}
def fib(n):
    if n in cache:
        return cache[n]
    if n < 2:
        return n
    result = fib(n - 1) + fib(n - 2)
    cache[n] = result
    return result

print(fib(100))    # мгновенно
```

Каждое значение считается **один раз**. Сложность падает с O(2^n) до O(n).

### `functools.lru_cache`

В Python — встроенный декоратор:
```python
from functools import lru_cache

@lru_cache(maxsize=None)
def fib(n):
    if n < 2:
        return n
    return fib(n - 1) + fib(n - 2)

print(fib(100))    # тоже мгновенно
```

`lru_cache` хранит результаты в LRU-кэше (Last Recently Used). `maxsize=None` — неограниченный.

С Python 3.9 — есть `@cache`, без ограничения по размеру:
```python
from functools import cache

@cache
def fib(n):
    if n < 2:
        return n
    return fib(n - 1) + fib(n - 2)
```

Аргументы кешируемой функции должны быть **хешируемые** (можно tuple, нельзя list).

---

## 7. Хвостовая рекурсия

Когда последнее действие функции — рекурсивный вызов:
```python
def factorial(n, acc=1):
    if n <= 1:
        return acc
    return factorial(n - 1, acc * n)    # хвостовой вызов
```

В некоторых языках (Scheme, Scala) компилятор **оптимизирует** хвостовую рекурсию в цикл — глубина не растёт. В Python — **нет такой оптимизации**. Поэтому хвостовая рекурсия не имеет преимуществ перед обычной по поводу глубины.

Если в Python хочешь избежать роста стека — переписывай в цикл.

---

## 8. Когда лучше итерация

Любая рекурсия **может** быть переписана как цикл с явным стеком. Часто — намного быстрее и без RecursionError:

### Факториал — итеративно

```python
def factorial(n):
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result
```

### Фибоначчи — итеративно

```python
def fib(n):
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a
```

O(n), без рекурсии, без стека.

### Реверс строки — итеративно

```python
def reverse(s):
    return s[::-1]
```

В Python вообще одной строкой.

**Правило**: если задача однонаправленная (линейная), цикл обычно лучше.

Рекурсия выигрывает когда:
- задача **естественно** разветвлённая (дерево, граф, фрактал);
- глубина небольшая и предсказуемая;
- читабельность важнее скорости.

---

## 9. Рекурсия для деревьев

Дерево — структура, где у узла есть дочерние узлы. Обход — естественно рекурсивный:

```python
tree = {
    "value": 1,
    "children": [
        {"value": 2, "children": []},
        {
            "value": 3,
            "children": [
                {"value": 4, "children": []},
                {"value": 5, "children": []},
            ],
        },
    ],
}

def sum_tree(node):
    total = node["value"]
    for child in node["children"]:
        total += sum_tree(child)
    return total

print(sum_tree(tree))    # 1 + 2 + 3 + 4 + 5 = 15
```

Без рекурсии — пришлось бы вручную вести стек узлов:
```python
def sum_tree_iter(node):
    total = 0
    stack = [node]
    while stack:
        n = stack.pop()
        total += n["value"]
        stack.extend(n["children"])
    return total
```

Итеративно — работает, но сложнее читать. Рекурсия для дерева — естественнее.

---

## 10. Обход вложенных структур

```python
def flatten(lst):
    """Развернуть произвольно вложенный список."""
    result = []
    for item in lst:
        if isinstance(item, list):
            result.extend(flatten(item))
        else:
            result.append(item)
    return result

print(flatten([1, [2, [3, [4, 5]], 6], 7]))    # [1, 2, 3, 4, 5, 6, 7]
```

Глубина зависит от данных — для глубоко вложенных списков (>1000) надо итеративно.

---

## 11. Обход директорий

```python
import os

def walk(path):
    for entry in os.listdir(path):
        full = os.path.join(path, entry)
        if os.path.isdir(full):
            walk(full)
        else:
            print(full)

walk("/home/user/docs")
```

В Python для этого есть `os.walk`, но если хочешь свой логику — рекурсия идеальна.

---

## 12. Ханойские башни

Классическая задача:

```python
def hanoi(n, from_, via, to):
    if n == 0:
        return
    hanoi(n - 1, from_, to, via)
    print(f"Move disk {n} from {from_} to {to}")
    hanoi(n - 1, via, from_, to)

hanoi(3, "A", "B", "C")
```

Без рекурсии — кошмар. С рекурсией — 5 строк.

---

## 13. Frames и стек вызовов

Каждый вызов функции создаёт **frame** в стеке. Frame содержит:
- локальные переменные;
- адрес возврата (куда вернуться после `return`);
- ссылку на предыдущий frame.

При рекурсии стек растёт:
```
factorial(5)        ← текущий frame
  factorial(4)      ← вызывающий
    factorial(3)
      factorial(2)
        factorial(1)
```

`sys.getrecursionlimit()` — текущий лимит. Превышение → RecursionError.

При исключении ты видишь **traceback** — это и есть стек вызовов:
```
File "...", line 5, in factorial
File "...", line 5, in factorial
File "...", line 5, in factorial
RecursionError: maximum recursion depth exceeded
```

---

## 14. Взаимная рекурсия

Две (или больше) функции, вызывающие друг друга:
```python
def is_even(n):
    if n == 0:
        return True
    return is_odd(n - 1)

def is_odd(n):
    if n == 0:
        return False
    return is_even(n - 1)

print(is_even(10))    # True
```

Тоже ограничена тем же лимитом стека. Нет особой пользы перед обычной рекурсией.

---

## 15. Типичные ошибки

### Забыл базовый случай

```python
def f(n):
    return n + f(n - 1)    # бесконечно
```

→ RecursionError.

### Неправильное приближение к базе

```python
def f(n):
    if n == 0:
        return 0
    return f(n)    # n не уменьшается
```

→ RecursionError.

### Слишком глубокая рекурсия

```python
def f(n):
    if n == 0:
        return 0
    return 1 + f(n - 1)

f(10000)    # RecursionError
```

Решение — итерация или мемоизация.

### Без мемоизации экспоненциальная рекурсия

```python
def fib(n):
    if n < 2:
        return n
    return fib(n - 1) + fib(n - 2)

fib(40)    # медленно (минуты)
fib(50)    # лет
```

Решение — `@lru_cache` или итеративная версия.

### `n - 1` при mutable / неправильный тип

```python
def length(lst):
    if not lst:
        return 0
    return 1 + length(lst[1:])    # каждый вызов копирует список → O(n²)
```

Лучше передавать индекс:
```python
def length(lst, i=0):
    if i == len(lst):
        return 0
    return 1 + length(lst, i + 1)
```

Но в Python — `len(lst)` уже O(1).

---

## 16. Чек-лист для решения через рекурсию

1. Определи **базовый случай**. Что вернёт функция в самом простом виде?
2. Определи **рекурсивный шаг**. Как функция вызывает себя на меньшей задаче?
3. Убедись, что шаг **приближает** к базе.
4. Проверь, не будет ли **слишком глубокой** рекурсии (n > 1000).
5. Если есть пересекающиеся подзадачи — добавь **мемоизацию**.

---

## 17. Что нужно запомнить

- Рекурсия = функция вызывает себя.
- Нужны: **база** (когда не вызывать) и **шаг** (вызов на меньшей задаче).
- Лимит ~1000 вложений в Python (`sys.setrecursionlimit` помогает, но не решает).
- Хвостовая оптимизация в Python **отсутствует**.
- Для пересекающихся подзадач — `@lru_cache`/`@cache`.
- Для деревьев и графов — рекурсия естественна.
- Для линейных задач — обычно итерация быстрее и надёжнее.
- Каждый вызов — кадр в стеке. Глубокая рекурсия → RecursionError.

После рекурсии всё дальнейшее идёт легко — файлы, исключения, ООП. Рекурсия и циклы вместе закрывают весь императивный фундамент языка.
