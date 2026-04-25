# Словари — от 0 до 100%

Словарь (`dict`) — вторая по важности структура данных в Python после списка. Если список — это «упорядоченный набор», то словарь — это «таблица соответствий»: ключ → значение. Имя пользователя → возраст. ID товара → описание. URL → HTTP-ответ. Это структура для хранения **именованных** данных.

В CPython словарь — это **хеш-таблица**: внутренне массив с особой адресацией. Поэтому почти все операции — O(1) (в среднем). Поэтому `if x in big_dict` мгновенно. Поэтому объекты Python — это словари (`__dict__`). Поэтому везде, где нужна быстрая «ассоциация» — используй dict.

---

## 1. Что такое словарь

```python
d = {"name": "Alice", "age": 30, "city": "Moscow"}
d = {}                    # пустой
d = dict()                # тоже пустой
d = dict(name="Alice", age=30)    # из именованных аргументов
d = dict([("a", 1), ("b", 2)])    # из списка пар
d = {x: x**2 for x in range(5)}   # comprehension
```

Словарь хранит **пары** ключ-значение. Доступ — по ключу (а не индексу как у списка).

```python
d["name"]                 # 'Alice'
d["age"] = 31             # обновление
d["email"] = "a@b.com"    # добавление
del d["city"]             # удаление
```

### Какие ключи можно

Ключи должны быть **хешируемыми** (immutable):
- `int`, `float`, `complex`, `bool`
- `str`, `bytes`
- `tuple` (если внутри только хешируемые)
- `frozenset`
- `None`
- свои классы (если у них есть `__hash__`)

**Нельзя** ключами:
- `list`
- `dict`
- `set`
- mutable свои классы без `__hash__`

```python
d[(1, 2)] = "тапл OK"          # OK
d[[1, 2]] = "не работает"      # TypeError: unhashable type: 'list'
```

Значения — **любой** тип, без ограничений.

---

## 2. Зачем хеш

Словарь работает как **хеш-таблица**. Когда ты делаешь `d["name"]`:
1. Python вычисляет `hash("name")` — число.
2. Применяет операцию `% размер_таблицы` → индекс.
3. По этому индексу лежит «ячейка» с (ключ, значение).
4. Если ячейка занята другим ключом (коллизия) — пробует следующую ячейку (open addressing).

Сложность — **O(1) в среднем**. Худший случай (много коллизий) — O(n), но это бывает только при намеренно плохих хешах.

Для этого ключ должен быть **immutable**: если ты изменишь ключ-список после вставки, его хеш не изменится в словаре, и Python не сможет его найти. Поэтому язык **запрещает** mutable ключи.

---

## 3. Чтение значений

### `d[key]` — KeyError если нет

```python
d = {"name": "Alice"}
d["name"]       # 'Alice'
d["age"]        # KeyError: 'age'
```

### `d.get(key, default)` — без ошибки

```python
d.get("name")              # 'Alice'
d.get("age")               # None
d.get("age", 0)            # 0
```

`get` — самый используемый метод. Используй когда не уверен, что ключ есть.

### `d.setdefault(key, default)`

```python
d.setdefault("count", 0)   # если ключ есть — вернёт значение, если нет — установит default и вернёт его
d["count"] += 1
```

Эквивалент:
```python
if "count" not in d:
    d["count"] = 0
d["count"] += 1
```

Часто используется для накопления:
```python
groups = {}
for word in words:
    first_letter = word[0]
    groups.setdefault(first_letter, []).append(word)
```

### `defaultdict` из collections

Ещё лучше — `defaultdict`:
```python
from collections import defaultdict

groups = defaultdict(list)
for word in words:
    groups[word[0]].append(word)
```

`defaultdict(list)` автоматически создаёт `[]` для новых ключей. Можно `defaultdict(int)`, `defaultdict(set)`, `defaultdict(lambda: ...)`.

---

## 4. Перебор словаря

```python
d = {"a": 1, "b": 2, "c": 3}

for key in d:
    print(key)              # a, b, c

for key in d.keys():        # явно ключи
    print(key)

for value in d.values():    # значения
    print(value)            # 1, 2, 3

for key, value in d.items():    # пары
    print(key, value)
```

Идиоматично — `d.items()` для одновременной работы с ключом и значением.

### Порядок

С Python 3.7 — словарь **сохраняет порядок вставки**. До 3.7 порядок был случайным. Сейчас это часть гарантий языка, можно полагаться.

```python
d = {}
d["first"] = 1
d["second"] = 2
d["third"] = 3
list(d.keys())      # ['first', 'second', 'third'] — гарантированно
```

### Изменение во время итерации — RuntimeError

```python
for k in d:
    if d[k] == 0:
        del d[k]    # ⚠️ RuntimeError: dictionary changed size during iteration
```

Решение — собрать ключи на удаление, потом удалить:
```python
to_delete = [k for k, v in d.items() if v == 0]
for k in to_delete:
    del d[k]
```

Или через comprehension создать новый:
```python
d = {k: v for k, v in d.items() if v != 0}
```

---

## 5. Изменение и удаление

### Обновление одного ключа

```python
d["age"] = 31
```

### Обновление нескольких — `update`

```python
d.update({"city": "Moscow", "phone": "+7..."})
d.update(city="Moscow")     # из именованных
d.update([("a", 1), ("b", 2)])    # из пар
```

Существующие ключи — перезаписываются, новые — добавляются.

### Удаление

```python
del d["name"]              # KeyError если нет
val = d.pop("age")         # удалить и вернуть значение
val = d.pop("age", None)   # с default — без ошибки
```

### `popitem` — удалить произвольную пару

```python
key, value = d.popitem()    # удаляет ПОСЛЕДНЮЮ вставленную (Python 3.7+)
```

Полезно для обработки словаря «по одному элементу».

### `clear` — очистка

```python
d.clear()                   # d = {}, но id тот же
```

---

## 6. Объединение и копирование

### Python 3.9+: `|` и `|=`

```python
a = {"x": 1, "y": 2}
b = {"y": 20, "z": 30}
c = a | b               # новый: {"x":1, "y":20, "z":30} — b перекрывает a
a |= b                  # a обновляется
```

### Через `**` распаковку (любая версия 3+)

```python
c = {**a, **b}          # то же
c = {**a, "extra": 99}  # с добавлением
```

### Копирование

```python
b = a.copy()            # shallow
b = dict(a)             # тоже
import copy
b = copy.deepcopy(a)    # рекурсивно
```

Shallow — верхний уровень новый, вложенные mutable общие:
```python
a = {"key": [1, 2, 3]}
b = a.copy()
a["key"].append(99)
print(b)        # {"key": [1, 2, 3, 99]} — список общий
```

---

## 7. Проверки

```python
"key" in d              # True/False — проверка ключа
"key" not in d
d                        # truthy если непустой, falsy если пустой
bool(d)                  # явно
len(d)                   # количество пар
```

Никогда не пиши `d.has_key("key")` — это Python 2.

### `in` для значений

```python
"value" in d             # ⚠️ это проверка ключа, НЕ значения!
"value" in d.values()    # ✅ проверка значения, но O(n)
```

Если часто проверяешь по значению — переверни словарь или используй другую структуру.

---

## 8. Comprehensions

```python
{x: x**2 for x in range(5)}
# {0: 0, 1: 1, 2: 4, 3: 9, 4: 16}

{k.lower(): v for k, v in d.items()}
# приведение ключей к нижнему регистру

{v: k for k, v in d.items()}
# обращение словаря — ключи и значения местами

{x: x**2 for x in range(10) if x % 2 == 0}
# с фильтром
```

---

## 9. Группировка

Классическая задача — сгруппировать список объектов по какому-то признаку.

```python
people = [
    {"name": "Alice", "age": 30},
    {"name": "Bob", "age": 25},
    {"name": "Carol", "age": 30},
]

# Способ 1: setdefault
groups = {}
for p in people:
    groups.setdefault(p["age"], []).append(p)

# Способ 2: defaultdict
from collections import defaultdict
groups = defaultdict(list)
for p in people:
    groups[p["age"]].append(p)

# Способ 3: itertools.groupby (требует сортированных данных!)
from itertools import groupby
people.sort(key=lambda p: p["age"])
for age, group in groupby(people, key=lambda p: p["age"]):
    groups[age] = list(group)
```

`itertools.groupby` группирует **только соседние** элементы с одинаковым ключом. Поэтому требует сначала отсортировать. Если данные не сортированы — используй defaultdict.

### `Counter`

Специальный словарь для подсчёта:
```python
from collections import Counter
words = "the quick brown fox jumps over the lazy dog the fox".split()
c = Counter(words)
print(c)
# Counter({'the': 3, 'fox': 2, 'quick': 1, ...})

c.most_common(3)        # [('the', 3), ('fox', 2), ('quick', 1)]
c["the"]                # 3
c["nonexistent"]        # 0 — никогда не падает
c["new"] += 1           # становится 1
```

---

## 10. Хеши и коллизии — внутренности

### Что хешируется как

```python
hash(42)            # 42 — int хеширует сам себя (для маленьких)
hash(2**100)        # большое число
hash("abc")         # рандомизированно (PYTHONHASHSEED)
hash(("a", 1))      # комбинация хешей элементов
hash([1, 2])        # TypeError — список не хешируем
```

С Python 3.3+ хеш строк **рандомизирован** между запусками. Это защита от DoS-атак (Hash collision attacks). Если нужно одинаковое поведение между запусками — установи `PYTHONHASHSEED=0`.

### Свой класс с `__hash__`

```python
class Point:
    def __init__(self, x, y):
        self.x, self.y = x, y
    def __eq__(self, other):
        return isinstance(other, Point) and self.x == other.x and self.y == other.y
    def __hash__(self):
        return hash((self.x, self.y))

p1 = Point(1, 2)
d = {p1: "data"}        # OK — точка хешируема
```

**Контракт**: если `a == b`, то `hash(a) == hash(b)`. Если нарушишь — словарь будет работать неправильно.

Если определил `__eq__`, **обязан** определить `__hash__` (иначе автоматически становится None и объект не хешируем).

### Расход памяти

```python
import sys
sys.getsizeof({})              # 64 — пустой dict
sys.getsizeof({"a": 1})        # 232
sys.getsizeof({i: i for i in range(100)})   # ~4700
```

Каждая запись в dict — это (хеш, ключ-указатель, значение-указатель). Для много-ключевых словарей — несколько мегабайт легко набирается.

В CPython 3.6+ словари **компактные** (PEP 468) — экономия 20-25% памяти по сравнению с старыми Python.

---

## 11. Когда что использовать

| Структура | Когда |
|---|---|
| `list` | упорядоченный, по индексу |
| `dict` | по ключу, любой тип ключа |
| `set` | проверка членства, дедупликация |
| `tuple` | неизменяемая запись (struct) |
| `defaultdict` | dict с авто-default |
| `Counter` | подсчёт |
| `OrderedDict` | dict с порядком (с 3.7 dict сам такой) |
| `ChainMap` | объединение нескольких dict для поиска |

### `OrderedDict` — нужен ли?

С Python 3.7 `dict` сохраняет порядок. Однако `OrderedDict`:
- имеет `move_to_end(key)`;
- сравнивается с учётом порядка (`{"a":1,"b":2} == {"b":2,"a":1}` — True для dict, для OrderedDict — False).

В большинстве случаев — обычного dict достаточно.

### `ChainMap`

```python
from collections import ChainMap
defaults = {"color": "blue", "size": "M"}
user_config = {"color": "red"}
config = ChainMap(user_config, defaults)
config["color"]    # 'red' — берётся из первого
config["size"]     # 'M' — из defaults
```

Полезно для слоёв конфигурации (cli > env > defaults).

---

## 12. Сериализация: dict ↔ JSON

```python
import json

d = {"name": "Alice", "age": 30, "scores": [90, 85, 88]}
s = json.dumps(d)              # '{"name": "Alice", "age": 30, ...}'
s = json.dumps(d, indent=2)    # с форматированием
s = json.dumps(d, ensure_ascii=False)  # сохранять Unicode (а не \uXXXX)

back = json.loads(s)           # обратно в dict
```

JSON идеально мапится на словарь. Часто используется для:
- API (REST возвращает JSON);
- конфигов;
- хранения структурированных данных.

Не все типы Python сериализуются: `set`, `bytes`, `tuple` (превратится в list), `datetime` — нужен кастомный encoder.

---

## 13. Запрос данных из вложенных структур

Часто JSON приходит вложенный, и нужно достать что-то глубоко:
```python
data = {
    "user": {
        "profile": {
            "city": "Moscow"
        }
    }
}

# Прямо — упадёт если хоть один ключ отсутствует:
city = data["user"]["profile"]["city"]

# Через get — мягко:
city = data.get("user", {}).get("profile", {}).get("city", "Unknown")
```

Для очень глубоких структур — внешние библиотеки (`pydantic`, `dataclasses` с `from_dict`).

---

## 14. Объекты — это словари

В Python почти каждый объект имеет `__dict__` — словарь его атрибутов:

```python
class Person:
    def __init__(self, name, age):
        self.name = name
        self.age = age

p = Person("Alice", 30)
print(p.__dict__)      # {'name': 'Alice', 'age': 30}
p.__dict__["email"] = "a@b.com"
print(p.email)         # 'a@b.com'
```

Поэтому `obj.attr` — это под капотом `obj.__dict__["attr"]` (с некоторыми оговорками насчёт классов и дескрипторов).

`__slots__` (продвинутая тема) отключает `__dict__` и хранит атрибуты компактнее.

---

## 15. Типичные ошибки

### KeyError

```python
val = d["nonexistent"]    # KeyError
val = d.get("nonexistent")  # ✅ None
val = d.get("nonexistent", "default")  # ✅ "default"
```

### Mutable ключ

```python
d[[1, 2]] = "data"    # TypeError: unhashable type: 'list'
d[(1, 2)] = "data"    # OK — tuple
```

### Переопределение `__eq__` без `__hash__`

```python
class C:
    def __eq__(self, other):
        return True

c = C()
d = {c: 1}    # TypeError: unhashable type
```

При определении `__eq__` Python автоматически делает `__hash__ = None`. Если нужно — добавь `__hash__` сам.

### Изменение во время итерации

```python
for k in d:
    if d[k] == 0:
        del d[k]    # RuntimeError
```

### Сортировка словаря

`d.sort()` — нет такого. dict сам по себе не сортируется. Можно:
```python
sorted(d.items())                       # по ключам
sorted(d.items(), key=lambda x: x[1])   # по значениям
dict(sorted(d.items()))                 # обратно в dict (порядок сохранится)
```

### `dict.fromkeys` — общий mutable default

```python
d = dict.fromkeys(["a", "b", "c"], [])
d["a"].append(1)
print(d)    # {"a": [1], "b": [1], "c": [1]} — !!!
```

`fromkeys` использует **один объект** для всех ключей. Решение:
```python
d = {k: [] for k in ["a", "b", "c"]}
```

---

## 16. Производительность

| Операция | Сложность |
|---|---|
| `d[k]` | O(1) среднее |
| `d[k] = v` | O(1) |
| `del d[k]` | O(1) |
| `k in d` | O(1) |
| `d.get(k)` | O(1) |
| `len(d)` | O(1) |
| итерация | O(n) |
| `d.copy()` | O(n) |

В худшем случае — O(n) при катастрофических коллизиях, что в реальной жизни не случается.

---

## 17. Что нужно запомнить

- Словарь — таблица «ключ → значение», O(1) на основные операции.
- Ключи — immutable (хешируемые). Значения — любые.
- С Python 3.7 словарь сохраняет порядок вставки.
- `d.get(k, default)` — стандартная безопасная проверка.
- `defaultdict`, `Counter`, `OrderedDict` — специализированные подвиды.
- Не модифицируй словарь во время итерации.
- `dict.fromkeys` с mutable default — общий объект.
- JSON ↔ dict — естественная пара.
- Объекты в Python — это словари (через `__dict__`).
- Хеширование рандомизировано между запусками (с 3.3+).

После словарей у тебя есть три основные коллекции — list, dict, set (следующая тема). Дальше пойдёт работа с функциями и логикой более высокого порядка.
