# Множества — от 0 до 100%

Множество (`set`) — третья базовая коллекция Python после list и dict. Это **неупорядоченная** коллекция **уникальных** элементов. Тебе оно нужно для двух вещей: (1) **быстро** проверять «есть ли элемент в наборе» и (2) **дедуплицировать** список — убрать повторы.

Под капотом — почти такая же хеш-таблица, как у dict, только без значений (только ключи). Поэтому почти все операции — O(1). Поэтому `if x in big_set` — мгновенно даже для миллиона элементов.

---

## 1. Что такое set

```python
s = {1, 2, 3}
s = set()              # ⚠️ {} — это ПУСТОЙ DICT, не set!
s = set([1, 2, 3])
s = set("hello")       # {'h', 'e', 'l', 'o'} — l только один раз
s = {x**2 for x in range(5)}   # comprehension
```

Запомни:
- `{}` — пустой словарь.
- `set()` — пустое множество.
- `{1}` — set с одним элементом.
- `{1: "v"}` — dict.

Множество **не сохраняет порядок** (в отличие от dict). Печать `print({3, 1, 2})` может выдать `{1, 2, 3}`, `{3, 1, 2}` — без гарантий.

### Какие элементы можно

Те же что ключи dict — **хешируемые** (immutable):
- числа, строки, bytes, tuple (если внутри хешируемые), frozenset
- кастомные объекты с `__hash__`

```python
s = {1, "a", (1, 2), True}    # OK
s = {[1, 2]}                   # TypeError: unhashable
s = {{1, 2}}                   # TypeError: unhashable (set сам не хешируется)
```

### `frozenset` — неизменяемый брат

```python
fs = frozenset([1, 2, 3])
fs.add(4)         # AttributeError — нельзя
```

`frozenset` **хешируем**, поэтому может быть элементом set или ключом dict:
```python
groups = {frozenset(["a", "b"]): "duo", frozenset(["a", "b", "c"]): "trio"}
```

---

## 2. Базовые операции

### Добавление и удаление

```python
s = {1, 2, 3}
s.add(4)           # {1, 2, 3, 4}
s.add(2)           # {1, 2, 3, 4} — уже есть, без эффекта
s.remove(2)        # {1, 3, 4} — KeyError если нет
s.discard(99)      # без ошибки если нет
s.pop()            # удаляет ПРОИЗВОЛЬНЫЙ элемент (не последний — порядка нет!)
s.clear()
```

`remove` падает с KeyError если элемента нет, `discard` — нет. Используй то, что подходит по семантике.

### Размер и проверки

```python
len(s)
x in s              # O(1) — это главная фишка set
x not in s
bool(s)             # truthy если непустой
```

`x in s` для set — **O(1)**. Для list — O(n). Если делаешь много проверок — переведи список в set:

```python
allowed = {"admin", "user", "moderator"}
if role in allowed:    # быстро
    ...
```

---

## 3. Операции над множествами

### Объединение

```python
a | b           # союз
a.union(b)      # то же
a |= b          # на месте: a.update(b)
```

```python
{1, 2, 3} | {3, 4, 5}     # {1, 2, 3, 4, 5}
```

### Пересечение

```python
a & b               # элементы, которые в обоих
a.intersection(b)
a &= b
```

```python
{1, 2, 3} & {2, 3, 4}     # {2, 3}
```

### Разность

```python
a - b               # элементы в a, которых нет в b
a.difference(b)
a -= b
```

```python
{1, 2, 3} - {2, 4}        # {1, 3}
```

### Симметричная разность

```python
a ^ b                       # элементы, которые ровно в одном из множеств
a.symmetric_difference(b)
a ^= b
```

```python
{1, 2, 3} ^ {2, 3, 4}     # {1, 4}
```

### Подмножества

```python
a <= b              # a — подмножество b
a < b               # строгое подмножество
a >= b              # a — надмножество b
a > b               # строгое надмножество
a.isdisjoint(b)     # True если нет общих элементов
```

```python
{1, 2} <= {1, 2, 3}    # True
{1, 2} <= {1, 2}       # True (нестрогое)
{1, 2} < {1, 2}        # False (строгое требует чтобы было неравно)
```

### Все операции принимают итерируемое (не только set)

```python
{1, 2, 3}.union([3, 4, 5])         # OK — список
{1, 2, 3}.union(range(2, 5))       # OK — range
{1, 2, 3} | [3, 4, 5]              # ⚠️ TypeError — оператор требует set
```

Через метод — любое итерируемое. Через оператор — только set.

---

## 4. Применения

### Дедупликация

```python
unique = list(set(data))           # удалить повторы (порядок не сохраняется!)

# Если нужен порядок:
def unique_ordered(seq):
    seen = set()
    result = []
    for x in seq:
        if x not in seen:
            seen.add(x)
            result.append(x)
    return result

# Или один раз через dict (Python 3.7+):
list(dict.fromkeys(data))          # ['a', 'b', 'c'] — сохраняет порядок
```

### Быстрая проверка членства

```python
allowed_codes = {200, 201, 204, 301, 302}
if response.status in allowed_codes:
    ...
```

Для постоянно используемых множеств — лучше определить как глобальную константу.

### Поиск общих/разных элементов

```python
followers_alice = set(...)
followers_bob = set(...)

both = followers_alice & followers_bob          # общие подписчики
only_alice = followers_alice - followers_bob    # только у Алисы
either = followers_alice | followers_bob        # объединение
```

### Удаление повторов из строки

```python
list(set("hello"))    # ['h', 'e', 'l', 'o'] — порядок не сохранён
```

### Подсчёт уникальных

```python
len(set(words))       # сколько различных слов
```

---

## 5. Перебор

```python
for x in s:
    print(x)
```

Порядок **не определён** и может меняться между запусками (как у dict до 3.7).

Если нужен сортированный обход:
```python
for x in sorted(s):
    print(x)
```

### Изменение во время итерации

```python
for x in s:
    if cond(x):
        s.remove(x)    # ⚠️ RuntimeError
```

Решение — собрать на удаление:
```python
to_remove = {x for x in s if cond(x)}
s -= to_remove
```

---

## 6. Comprehensions

```python
{x**2 for x in range(10)}                   # квадраты
{x for x in data if x > 0}                  # фильтр
{(x, y) for x in range(3) for y in range(3)}   # парами
```

Set comprehension в фигурных скобках без `:` — отличает от dict comprehension.

---

## 7. Производительность

| Операция | Сложность |
|---|---|
| `x in s` | O(1) среднее |
| `s.add(x)` | O(1) |
| `s.remove(x)` | O(1) |
| `len(s)` | O(1) |
| `s | t` | O(len(s) + len(t)) |
| `s & t` | O(min(len(s), len(t))) |
| `s - t` | O(len(s)) |
| итерация | O(n) |

Поэтому если у тебя есть «список из 100 000», и ты делаешь много `if x in lst` — переведи в set, и получишь ускорение в тысячи раз.

---

## 8. Память

```python
import sys
sys.getsizeof(set())            # 216 — пустой set дороже пустого dict из-за внутреннего allocator
sys.getsizeof({1})              # 216 — те же 216 пока маленький
sys.getsizeof({1, 2, 3})        # 216
sys.getsizeof({i for i in range(1000)})    # ~32k
```

Set дороже list по памяти (примерно в 4-5 раз для маленьких), но дешевле для уникальных коллекций (где list пришлось бы хранить дубликаты).

---

## 9. Хеширование своих классов

```python
class Tag:
    def __init__(self, name):
        self.name = name
    def __eq__(self, other):
        return isinstance(other, Tag) and self.name == other.name
    def __hash__(self):
        return hash(self.name)

s = {Tag("python"), Tag("rust"), Tag("python")}
print(len(s))    # 2 — два python считаются одним
```

Те же правила, что и для dict-ключей: если `a == b`, то `hash(a) == hash(b)`. Иначе — баги.

---

## 10. frozenset

```python
fs = frozenset([1, 2, 3])
fs | {4, 5}            # frozenset({1, 2, 3, 4, 5})
fs.add(4)              # AttributeError
```

Зачем нужен:
- Можно использовать как ключ dict или элемент другого set.
- Гарантия неизменяемости при передаче в функции.
- Иногда чуть быстрее за счёт упрощённой реализации (нет add/remove).

```python
# set множеств — нельзя:
{{1, 2}, {3, 4}}        # TypeError

# set frozenset-ов — можно:
{frozenset({1, 2}), frozenset({3, 4})}     # OK
```

---

## 11. Типичные ошибки

### `{}` — это dict, не set

```python
empty = {}             # dict
empty = set()          # set
```

### Mutable элементы

```python
{[1, 2], [3, 4]}       # TypeError: unhashable
{(1, 2), (3, 4)}       # OK
```

### Изменение во время итерации

См. секцию 5.

### Перепутали `union` и `update`

```python
a.union(b)             # возвращает новый set
a.update(b)            # мутирует a
```

Аналогично у других операций: `intersection`/`intersection_update`, `difference`/`difference_update`.

### Operator vs method

```python
{1, 2} | [3, 4]                # TypeError
{1, 2}.union([3, 4])           # OK — метод принимает любое iterable
```

### Set не сохраняет порядок

```python
list(set([3, 1, 2]))    # может быть [1, 2, 3], [3, 1, 2], как угодно
```

Если важен порядок — не используй set.

### Сравнение с list

```python
{1, 2, 3} == [1, 2, 3]    # False — разные типы
list({1, 2, 3}) == [1, 2, 3]    # часто True для маленьких, но не гарантировано (порядок!)
```

---

## 12. set vs dict vs list — когда что

| Задача | Структура |
|---|---|
| Сохранить пары ключ-значение | dict |
| Уникальные элементы | set |
| Упорядоченные элементы | list |
| Проверка членства часто | set |
| Проверка членства редко | list норм |
| Доступ по индексу нужен | list |
| Доступ по ключу нужен | dict |
| Дедупликация | set |
| Хешируемая коллекция (как ключ) | frozenset/tuple |

---

## 13. Частая комбинация: dict значений-set

```python
followers = {
    "alice": {"bob", "carol"},
    "bob": {"alice"},
    "carol": {"alice", "bob"},
}

# общие подписчики Алисы и Боба:
followers["alice"] & followers["bob"]    # {'bob'}? нет, {'bob'} только если bob следит, давай:

# у Кэрол есть подписки на:
followers["carol"]    # {'alice', 'bob'}
```

Часто используется для графов, social networks.

---

## 14. Что нужно запомнить

- `set` — неупорядоченная коллекция уникальных, хешируемых элементов.
- `{}` — пустой dict, `set()` — пустой set.
- `x in s` — O(1) для set, O(n) для list.
- Операции: `|` (union), `&` (intersection), `-` (difference), `^` (symmetric).
- `frozenset` — неизменяемый, может быть ключом dict.
- Не модифицируй set во время итерации.
- Дедупликация: `list(set(data))` (без порядка) или `list(dict.fromkeys(data))` (с порядком).
- Память: set дороже list, но даёт O(1) поиск.

После set + list + dict у тебя в арсенале **все** базовые коллекции. Дальше — функции, фундамент любого структурированного кода.
