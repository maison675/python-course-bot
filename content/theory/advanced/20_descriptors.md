# Дескрипторы и `__slots__` — от 0 до 100%

Если ты использовал `@property` — ты уже видел дескриптор, просто не знал. Если использовал ORM (Django, SQLAlchemy) — каждое поле модели это дескриптор. Если работал с `pydantic` — тоже дескриптор. Они везде, и понимание их даёт суперсилу: способность писать собственные «магические» атрибуты, валидаторы, и оптимизированные классы.

`__slots__` — оптимизация памяти и скорости. Заодно частая тема для собеседований.

---

## 1. Зачем дескрипторы

Базовый сценарий: хочешь, чтобы при `obj.x = 5` происходила какая-то логика — валидация, логирование, ленивое вычисление. В Python для этого есть несколько уровней:

1. Простой атрибут.
2. `@property` — для одного класса.
3. **Дескрипторы** — переиспользуемая логика для множества классов.

```python
class Person:
    @property
    def age(self):
        return self._age
    @age.setter
    def age(self, value):
        if not 0 <= value <= 150:
            raise ValueError
        self._age = value
```

Если тебе нужна та же валидация в 10 классах — `@property` дублируется. Дескриптор позволяет **один раз написать логику** и применить везде.

---

## 2. Что такое дескриптор

Дескриптор — это объект **с одним из методов**:
- `__get__(self, obj, objtype=None)` — чтение атрибута;
- `__set__(self, obj, value)` — запись атрибута;
- `__delete__(self, obj)` — удаление атрибута;
- `__set_name__(self, owner, name)` — установка имени (3.6+).

Когда такой объект **назначен атрибутом класса** (не экземпляра), доступ через экземпляр идёт через эти методы.

```python
class MyDescriptor:
    def __get__(self, obj, objtype=None):
        print("get")
        return 42
    def __set__(self, obj, value):
        print(f"set {value}")

class Foo:
    x = MyDescriptor()    # дескриптор как атрибут класса

f = Foo()
f.x          # 'get' → 42
f.x = 10     # 'set 10'
```

---

## 3. Виды дескрипторов

### Data descriptor

Имеет `__set__` (и/или `__delete__`). Управляет и записью, и чтением.

### Non-data descriptor

Имеет только `__get__`, без `__set__`.

Разница важна: data-дескриптор **перекрывает** атрибут экземпляра, non-data — нет.

```python
class DataDesc:
    def __get__(self, obj, objtype=None):
        return "from descriptor"
    def __set__(self, obj, value):
        obj.__dict__["x"] = value

class NonDataDesc:
    def __get__(self, obj, objtype=None):
        return "from descriptor"

class A:
    x = DataDesc()
class B:
    x = NonDataDesc()

a = A()
a.__dict__["x"] = "from instance"
print(a.x)    # 'from descriptor' — data desc выигрывает

b = B()
b.__dict__["x"] = "from instance"
print(b.x)    # 'from instance' — non-data, instance dict выигрывает
```

Это делает `@property` (data desc) надёжной защитой от случайной перезаписи.

---

## 4. Простой пример: валидация

```python
class PositiveInt:
    def __set_name__(self, owner, name):
        self.name = name
    def __get__(self, obj, objtype=None):
        return obj.__dict__.get(self.name)
    def __set__(self, obj, value):
        if not isinstance(value, int) or value < 0:
            raise ValueError(f"{self.name} must be a positive integer")
        obj.__dict__[self.name] = value

class Person:
    age = PositiveInt()
    weight = PositiveInt()

p = Person()
p.age = 30        # OK
p.weight = 70
p.age = -1        # ValueError: age must be a positive integer
```

`__set_name__` вызывается автоматически при создании класса и сохраняет имя атрибута. Это позволяет дескриптору работать с произвольным числом полей в одном классе.

---

## 5. Хранение данных

Куда дескриптор хранит данные? Обычно — в `obj.__dict__`. Иногда — в самом дескрипторе, но это **антипаттерн**:

```python
class BAD_Descriptor:
    def __init__(self):
        self.value = None      # ⚠️ один на все экземпляры
    def __get__(self, obj, objtype=None):
        return self.value
    def __set__(self, obj, value):
        self.value = value

class Foo:
    x = BAD_Descriptor()

a = Foo()
b = Foo()
a.x = 1
print(b.x)    # 1 — !!! значения смешались
```

Поэтому всегда храни в `obj.__dict__[self.name]` или в `WeakKeyDictionary`.

---

## 6. WeakKeyDictionary для хранения

Если использовать `__slots__` — `obj.__dict__` нет. Тогда:
```python
import weakref

class TypedField:
    def __init__(self, type_):
        self.type = type_
        self.data = weakref.WeakKeyDictionary()
    def __get__(self, obj, objtype=None):
        return self.data.get(obj)
    def __set__(self, obj, value):
        if not isinstance(value, self.type):
            raise TypeError
        self.data[obj] = value
```

WeakKeyDictionary не удерживает ключи — когда экземпляр удаляется, его данные тоже.

---

## 7. Как работают встроенные

### `@property` — это дескриптор

```python
class Foo:
    @property
    def x(self):
        return self._x

# эквивалентно:
class Foo:
    x = property(lambda self: self._x)

print(type(Foo.x))    # <class 'property'>
```

`property` — стандартный data-дескриптор. Принимает getter, setter, deleter.

### Методы — тоже дескрипторы

```python
class Foo:
    def method(self):
        return 42

f = Foo()
print(f.method)             # <bound method ...>
print(Foo.method)           # <function ...>
print(f.method == Foo.method.__get__(f))    # True

# unbound method:
type(Foo.method)            # <class 'function'>
# bound method:
type(f.method)              # <class 'method'>
```

Когда ты делаешь `f.method`, на самом деле вызывается `function.__get__(f, Foo)`, который возвращает **bound method** — обёртку, у которой `self` уже привязан.

### `staticmethod`, `classmethod` — тоже дескрипторы

```python
class Foo:
    @staticmethod
    def bar():
        return "static"

print(type(Foo.__dict__["bar"]))    # <class 'staticmethod'>
```

`staticmethod.__get__()` возвращает функцию без привязки. `classmethod.__get__()` возвращает bound method с `cls` вместо `self`.

---

## 8. Применения дескрипторов

### ORM-поля

```python
class Field:
    def __set_name__(self, owner, name):
        self.name = name
    def __get__(self, obj, objtype=None):
        return obj.__dict__.get(self.name)
    def __set__(self, obj, value):
        # тут можно: валидация, конверсия, логирование, dirty-tracking
        obj.__dict__[self.name] = value

class IntField(Field):
    def __set__(self, obj, value):
        super().__set__(obj, int(value))

class StringField(Field):
    def __init__(self, max_length=None):
        self.max_length = max_length
    def __set__(self, obj, value):
        if self.max_length and len(value) > self.max_length:
            raise ValueError("too long")
        super().__set__(obj, value)

class User:
    name = StringField(max_length=50)
    age = IntField()
```

Это и есть упрощённая модель Django/SQLAlchemy.

### Lazy evaluation

```python
class Lazy:
    def __init__(self, func):
        self.func = func
    def __set_name__(self, owner, name):
        self.name = name
    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        if self.name not in obj.__dict__:
            obj.__dict__[self.name] = self.func(obj)
        return obj.__dict__[self.name]

class User:
    @Lazy
    def expensive(self):
        print("вычисляю...")
        return sum(range(1_000_000))

u = User()
u.expensive    # 'вычисляю...' → большое число
u.expensive    # сразу большое число — кэшировано
```

Это упрощённая `functools.cached_property`.

### Type checking

```python
class TypeChecked:
    def __init__(self, type_):
        self.type = type_
    def __set_name__(self, owner, name):
        self.name = "_" + name
    def __get__(self, obj, objtype=None):
        return getattr(obj, self.name, None)
    def __set__(self, obj, value):
        if not isinstance(value, self.type):
            raise TypeError(f"expected {self.type.__name__}, got {type(value).__name__}")
        setattr(obj, self.name, value)

class Point:
    x = TypeChecked(int)
    y = TypeChecked(int)

p = Point()
p.x = 5         # OK
p.x = "5"       # TypeError
```

---

## 9. `__slots__` — что это

Обычно у каждого экземпляра есть `__dict__` для атрибутов:
```python
class Foo:
    pass
f = Foo()
f.x = 1
f.y = 2
print(f.__dict__)    # {'x': 1, 'y': 2}
f.z = 3              # можно добавить любой атрибут
```

Это гибкое, но дорого по памяти. Для миллионов мелких объектов — `__slots__`:
```python
class Point:
    __slots__ = ("x", "y")
    def __init__(self, x, y):
        self.x = x
        self.y = y

p = Point(1, 2)
print(p.x, p.y)    # 1 2
p.z = 3            # AttributeError — нельзя добавлять
print(hasattr(p, "__dict__"))    # False — словаря нет
```

### Что даёт `__slots__`

- **Меньше памяти** — нет `__dict__`. Атрибуты хранятся в фиксированном массиве.
- **Быстрее доступ** — атрибуты как структурные поля, без dict lookup.
- **Защита от опечаток** — `p.tt = 5` упадёт, не создастся новый атрибут.

### Цифры

```python
import sys

class WithDict:
    def __init__(self, x, y):
        self.x, self.y = x, y

class WithSlots:
    __slots__ = ("x", "y")
    def __init__(self, x, y):
        self.x, self.y = x, y

a = WithDict(1, 2)
b = WithSlots(1, 2)

print(sys.getsizeof(a))                    # 48
print(sys.getsizeof(a) + sys.getsizeof(a.__dict__))    # ~152
print(sys.getsizeof(b))                    # 48 — но БЕЗ доп. словаря
```

Реальная экономия — около 40-50% памяти на объект.

### Когда применять

- Объекты, которых много (миллионы) и атрибуты фиксированные.
- DTO, value objects.
- Узкие места по памяти.

### Когда НЕ применять

- Если нужна гибкость (добавлять атрибуты динамически).
- Если используешь множественное наследование (бывают конфликты slots).
- Если объектов мало — экономия не стоит сложности.

---

## 10. `__slots__` и наследование

```python
class A:
    __slots__ = ("x",)

class B(A):
    __slots__ = ("y",)        # A.x доступен, добавляем y

class C(A):
    pass                       # ⚠️ нет __slots__ → возвращается __dict__

c = C()
c.z = 3        # OK — есть __dict__
```

Если хоть один родитель без `__slots__` — `__dict__` появляется снова. Чтобы наследование работало эффективно — `__slots__` в каждом потомке.

### Конфликты

```python
class A:
    __slots__ = ("x",)
class B:
    __slots__ = ("x",)           # тот же slot
class C(A, B):                    # TypeError: multiple bases have instance lay-out conflict
    __slots__ = ()
```

При множественном наследовании с `__slots__` — сложно. Часто используется только в простых иерархиях.

---

## 11. `__slots__` и `__dict__`

Можно явно добавить:
```python
class Foo:
    __slots__ = ("x", "__dict__")
    def __init__(self, x):
        self.x = x

f = Foo(1)
f.y = 2        # OK — есть __dict__
```

Но смысл `__slots__` тогда теряется. Делается редко.

---

## 12. `__slots__` с дескрипторами

```python
class Validated:
    def __set_name__(self, owner, name):
        self.public = name
        self.private = "_" + name
    def __get__(self, obj, objtype=None):
        return getattr(obj, self.private, None)
    def __set__(self, obj, value):
        if value < 0: raise ValueError
        setattr(obj, self.private, value)

class Foo:
    __slots__ = ("_x",)
    x = Validated()

f = Foo()
f.x = 5        # → __set__ → self._x = 5
print(f.x)      # 5
```

Дескриптор хранит данные в `_x` слоте.

---

## 13. dataclass со slots

С 3.10:
```python
from dataclasses import dataclass

@dataclass(slots=True)
class Point:
    x: int
    y: int

p = Point(1, 2)
p.z = 3    # AttributeError — slots работают
```

Это самый удобный способ получить slots-класс.

---

## 14. `@cached_property`

С 3.8 — стандартная библиотечная замена для lazy:
```python
from functools import cached_property

class Container:
    def __init__(self, data):
        self.data = data

    @cached_property
    def expensive(self):
        return sum(self.data)

c = Container(range(1_000_000))
c.expensive    # вычисляется
c.expensive    # сразу
```

Это data-дескриптор, хранящий значение в `obj.__dict__`. Не работает со `__slots__` без явного `"__dict__"` в слотах.

---

## 15. Почему дескрипторы — фундамент

Когда ты делаешь `obj.attr`, Python проходит сложную процедуру:

1. Вызывает `type(obj).__getattribute__(obj, "attr")`.
2. Тот ищет в `type(obj).__mro__` дескриптор:
   - Если **data descriptor** — вызывает `__get__`. Конец.
   - Иначе — смотрит в `obj.__dict__`. Если есть — возвращает.
   - Иначе — если **non-data descriptor** — вызывает `__get__`.
   - Иначе — если статика в классе — возвращает.
   - Иначе — `__getattr__` (если есть) или AttributeError.

Эта процедура и есть **протокол доступа к атрибутам**. Дескрипторы встраиваются в него.

---

## 16. Типичные ошибки

### Дескриптор как атрибут экземпляра

```python
class Foo:
    pass

f = Foo()
f.x = MyDescriptor()    # ⚠️ не работает как дескриптор!
```

Дескрипторы работают **только как атрибуты класса**.

### Хранение в `self.value` дескриптора

Уже обсуждали — все экземпляры расшарят значение.

### `__slots__` забыт в наследнике

```python
class A:
    __slots__ = ("x",)
class B(A):
    pass     # ⚠️ B имеет __dict__
```

### `__slots__` и пустой кортеж

```python
class A:
    __slots__ = ("x")    # ⚠️ это строка, не кортеж!
```

`A.__slots__` будет интерпретирован как iterable строки → слоты "x". В простом случае работает, но в сложных — баги. Используй `("x",)` всегда.

### `__set_name__` не определён

```python
class Foo:
    x = MyDescriptor()
    y = MyDescriptor()

f = Foo()
f.x = 1     # все экземпляры путаются если name общий
```

Без `__set_name__` дескриптор не знает, под каким именем привязан. Без него работа с несколькими полями ломается.

---

## 17. Что нужно запомнить

- Дескриптор — объект с `__get__`/`__set__`/`__delete__`, привязанный к классу.
- Data-дескриптор перекрывает `obj.__dict__`, non-data — нет.
- `@property`, методы, `@staticmethod`, `@classmethod` — все дескрипторы.
- Хранить значения — в `obj.__dict__[self.name]`, не в самом дескрипторе.
- `__set_name__` (3.6+) — стандартный способ узнать имя поля.
- Использование: ORM-поля, валидация, lazy-evaluation, type checks.
- `__slots__` — отказ от `__dict__`, экономия памяти и скорость.
- В наследниках — нужен свой `__slots__`.
- `@dataclass(slots=True)` — удобный способ.
- `@cached_property` — стандартное lazy-кэширование.

После этого ты понимаешь, **как** Python обрабатывает доступ к атрибутам. Дальше — следующий уровень магии: метаклассы.
