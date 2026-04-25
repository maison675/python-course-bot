# Метаклассы — от 0 до 100%

Метаклассы — это «классы классов». Звучит абстрактно, но если кратко: `type` — это класс, а его экземпляры — это **другие классы**. Когда ты пишешь `class Foo: pass`, Python создаёт объект `Foo`, экземпляр класса `type`. Метакласс — это и есть «то, что создаёт класс».

Метаклассы — мощный инструмент метапрограммирования. На них построены: `abc.ABC`, Django models, SQLAlchemy declarative, enum.Enum, `typing.Generic`, и многое другое. На собеседованиях в крутые компании по Python — стабильный вопрос.

> «Метаклассы — это магия, которая 99% разработчиков не нужна. Если ты сомневаешься, нужен ли тебе метакласс — он не нужен.»  
> — Тим Питерс (один из core-developer Python)

Тем не менее, важно понимать как они работают — даже если не пишешь свои, ты их встретишь.

---

## 1. Классы — это объекты

Первое и главное: в Python **классы — это обычные объекты**. С ними можно делать всё, что и с другими:

```python
class Foo:
    pass

print(Foo)           # <class '__main__.Foo'>
print(type(Foo))     # <class 'type'>

# Класс можно положить в переменную:
F = Foo
f = F()              # эквивалент Foo()

# Передать в функцию:
def make(cls):
    return cls()

# Хранить в коллекциях:
classes = [int, str, list, Foo]
```

`type(obj)` для экземпляра — возвращает класс. `type(class)` — возвращает **метакласс**. Метакласс по умолчанию — `type`.

---

## 2. Создание класса вручную через `type`

`type(name, bases, dict)` — динамическое создание класса:

```python
Foo = type("Foo", (), {"x": 5, "greet": lambda self: f"hi, x={self.x}"})

f = Foo()
print(f.x)           # 5
print(f.greet())     # 'hi, x=5'

print(type(Foo))     # <class 'type'>
print(Foo.__name__)  # 'Foo'
```

Это **полностью эквивалентно**:
```python
class Foo:
    x = 5
    def greet(self):
        return f"hi, x={self.x}"
```

`class Foo: ...` — **синтаксический сахар** для `type("Foo", (), {...})`. Когда Python встречает `class`, он:
1. Выполняет тело класса в новом namespace (словаре).
2. Зовёт метакласс с `(name, bases, namespace)`.
3. Привязывает результат к имени `Foo`.

---

## 3. Свой метакласс

Свой метакласс = подкласс `type`:

```python
class MyMeta(type):
    def __new__(mcs, name, bases, namespace):
        print(f"Создаю класс {name}")
        return super().__new__(mcs, name, bases, namespace)

class Foo(metaclass=MyMeta):
    pass

# Печатает: 'Создаю класс Foo'

class Bar(Foo):    # тоже использует MyMeta — наследуется
    pass

# Печатает: 'Создаю класс Bar'
```

`metaclass=MyMeta` указывается в скобках при определении класса. Метакласс наследуется автоматически.

---

## 4. Что можно сделать в метаклассе

### Изменить namespace (добавить/изменить методы)

```python
class AddRepr(type):
    def __new__(mcs, name, bases, namespace):
        def __repr__(self):
            attrs = ", ".join(f"{k}={v!r}" for k, v in self.__dict__.items())
            return f"{name}({attrs})"
        namespace["__repr__"] = __repr__
        return super().__new__(mcs, name, bases, namespace)

class Point(metaclass=AddRepr):
    def __init__(self, x, y):
        self.x = x
        self.y = y

print(Point(1, 2))    # Point(x=1, y=2)
```

### Регистрировать классы

```python
plugins = {}

class PluginMeta(type):
    def __new__(mcs, name, bases, namespace):
        cls = super().__new__(mcs, name, bases, namespace)
        if name != "Plugin":      # не регистрируем сам базовый
            plugins[name] = cls
        return cls

class Plugin(metaclass=PluginMeta):
    pass

class FooPlugin(Plugin):
    pass

class BarPlugin(Plugin):
    pass

print(plugins)    # {'FooPlugin': <class 'FooPlugin'>, 'BarPlugin': <class 'BarPlugin'>}
```

Это паттерн «авто-регистрация» — все наследники сами добавляются в реестр.

### Принудить к интерфейсу

```python
class RequireMethods(type):
    def __new__(mcs, name, bases, namespace):
        if "method" not in namespace:
            raise TypeError(f"{name} must implement method()")
        return super().__new__(mcs, name, bases, namespace)

class Good(metaclass=RequireMethods):
    def method(self): pass

class Bad(metaclass=RequireMethods):    # TypeError
    pass
```

Альтернатива — `abc.ABCMeta` (стандартная).

### Добавить классовое поле

```python
class Counted(type):
    count = 0
    def __new__(mcs, name, bases, namespace):
        Counted.count += 1
        cls = super().__new__(mcs, name, bases, namespace)
        cls.id = Counted.count
        return cls

class A(metaclass=Counted): pass
class B(metaclass=Counted): pass

print(A.id, B.id)    # 1 2
```

---

## 5. `__init__` метакласса vs `__new__`

```python
class Meta(type):
    def __new__(mcs, name, bases, namespace, **kwargs):
        print("__new__")
        return super().__new__(mcs, name, bases, namespace)
    
    def __init__(cls, name, bases, namespace, **kwargs):
        print("__init__")
        super().__init__(name, bases, namespace)

class Foo(metaclass=Meta):
    pass
# __new__
# __init__
```

- `__new__` — создаёт сам объект класса.
- `__init__` — инициализирует уже созданный класс.

Чаще всего — переопределять `__new__` или `__init__`. Иногда оба, для разных задач.

---

## 6. `__call__` метакласса — контроль создания экземпляров

```python
class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]

class Database(metaclass=Singleton):
    def __init__(self):
        print("Connecting...")

a = Database()    # 'Connecting...'
b = Database()    # ничего — возвращает тот же объект
print(a is b)     # True
```

`metaclass.__call__` вызывается **когда создаётся экземпляр класса**. По умолчанию вызывает `cls.__new__` и `cls.__init__`. Переопределив — можно контролировать.

Это ровно то, как реализуется паттерн **Singleton**.

---

## 7. `__init_subclass__` — лёгкая альтернатива (3.6+)

В большинстве случаев метакласса можно избежать через `__init_subclass__` — хук, вызываемый при создании подкласса:

```python
class Base:
    plugins = {}
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        Base.plugins[cls.__name__] = cls

class Foo(Base):
    pass

class Bar(Base):
    pass

print(Base.plugins)    # {'Foo': ..., 'Bar': ...}
```

Гораздо проще, чем метакласс. Используй когда возможно.

С аргументами:
```python
class Plugin:
    def __init_subclass__(cls, name=None, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.name = name or cls.__name__.lower()

class FooPlugin(Plugin, name="foo"):
    pass

print(FooPlugin.name)    # 'foo'
```

---

## 8. ABCMeta и абстрактные классы

`ABCMeta` — стандартный метакласс из `abc`:
```python
from abc import ABCMeta, abstractmethod

class Shape(metaclass=ABCMeta):
    @abstractmethod
    def area(self): pass

class Circle(Shape):
    def __init__(self, r): self.r = r
    def area(self): return 3.14 * self.r ** 2

# Shape()    # TypeError: can't instantiate abstract class
Circle(5)    # OK
```

Удобнее наследоваться от `ABC`:
```python
from abc import ABC, abstractmethod

class Shape(ABC):    # эквивалент metaclass=ABCMeta
    @abstractmethod
    def area(self): pass
```

`ABCMeta` также позволяет «виртуальную регистрацию»:
```python
from abc import ABC

class Drawable(ABC):
    pass

class Square:
    def draw(self): print("drawing")

Drawable.register(Square)
print(issubclass(Square, Drawable))    # True
print(isinstance(Square(), Drawable))  # True
```

---

## 9. Как разрешается метакласс

Когда у тебя:
```python
class C(A, B, metaclass=M):
    pass
```

Python выбирает метакласс в таком порядке:
1. Если указан явно `metaclass=` — используется он.
2. Иначе — берётся метакласс самого «строгого» родителя (наследника наиболее specific метакласса).

При **конфликте** метаклассов:
```python
class M1(type): pass
class M2(type): pass

class A(metaclass=M1): pass
class B(metaclass=M2): pass

class C(A, B): pass
# TypeError: metaclass conflict
```

Решение — общий метакласс:
```python
class M3(M1, M2): pass

class C(A, B, metaclass=M3): pass    # OK
```

---

## 10. type-hierarchy

```
                  object
                    │
                ┌───┴────┐
              type      ...
                │
            (другие
            метаклассы)
```

`type` сам — экземпляр себя:
```python
print(type(type))    # <class 'type'>
print(type(object))  # <class 'type'>
print(type(int))     # <class 'type'>
```

`object` — корень всех классов. `type` — корень всех метаклассов. Один из самых intricate моментов Python.

---

## 11. Метакласс vs обычный класс — когда что

### Используй обычный класс/композицию когда

- нужно поведение **экземпляров**;
- нужен класс, у которого есть состояние;
- 99% случаев.

### Используй декоратор класса когда

- нужно модифицировать класс **после создания**;
- одно изменение, на конкретный класс;
- `@dataclass`, `@register`, и т.п.

```python
def add_repr(cls):
    cls.__repr__ = lambda self: f"{cls.__name__}({self.__dict__})"
    return cls

@add_repr
class Foo:
    def __init__(self, x): self.x = x

print(Foo(1))    # Foo({'x': 1})
```

### Используй `__init_subclass__` когда

- нужно поведение при создании **подклассов**;
- один уровень сложности;
- большинство случаев, где раньше нужен был метакласс.

### Используй метакласс когда

- нужно повлиять на **создание самого класса**, не подклассов;
- нужен полный контроль (изменение namespace, контроль `__call__`);
- работаешь с фреймворками (Django, SQLAlchemy);
- редко.

---

## 12. Реальные примеры из библиотек

### Django Model

```python
class User(models.Model):
    name = models.CharField(max_length=100)
    age = models.IntegerField()
```

`models.Model` имеет метакласс `ModelBase`. Он:
- собирает все Field из namespace;
- регистрирует модель в реестре приложения;
- генерирует Manager (`objects`);
- настраивает `_meta` атрибут.

### SQLAlchemy declarative

```python
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String)
```

Метакласс собирает Column-ы и создаёт SQL-таблицу.

### Enum

```python
from enum import Enum

class Color(Enum):
    RED = 1
    GREEN = 2
    BLUE = 3
```

Метакласс `EnumMeta`:
- запрещает создание новых членов после класса;
- делает `Color.RED` синглтоном;
- предоставляет `__iter__`, `__len__` по членам.

---

## 13. `__class__` и `__class__.__class__`

```python
x = 5
print(x.__class__)              # <class 'int'>
print(x.__class__.__class__)    # <class 'type'>
print(x.__class__.__class__.__class__)    # <class 'type'> — самореференция
```

`type` — экземпляр себя. Это и есть «дно».

---

## 14. Меньше известное: namespace

При создании класса Python вызывает `Meta.__prepare__(name, bases)` — она возвращает namespace, который потом будет наполняться:

```python
class Meta(type):
    @classmethod
    def __prepare__(mcs, name, bases):
        print("preparing")
        return {}    # обычный dict
    
    def __new__(mcs, name, bases, namespace):
        return super().__new__(mcs, name, bases, namespace)

class Foo(metaclass=Meta):
    x = 1
```

Можно вернуть `OrderedDict` (раньше нужно было — теперь dict упорядочен), или свой словарь, перехватывающий назначения:

```python
class TrackingDict(dict):
    def __setitem__(self, k, v):
        print(f"set {k}={v}")
        super().__setitem__(k, v)

class Meta(type):
    @classmethod
    def __prepare__(mcs, name, bases):
        return TrackingDict()
```

Это даёт **полный контроль** над тем как класс заполняется.

---

## 15. Типичные ошибки

### Метакласс там, где не нужен

```python
class CounterMeta(type):
    count = 0
    def __new__(mcs, name, bases, ns):
        CounterMeta.count += 1
        return super().__new__(mcs, name, bases, ns)
```

Если хочешь считать только подклассы — `__init_subclass__` проще.

### Метакласс конфликт

```python
class A(metaclass=M1): pass
class B(metaclass=M2): pass
class C(A, B): pass    # TypeError
```

См. п.9 — решается общим метаклассом.

### Метакласс — `class` не `instance`

```python
class Meta(type):
    def __new__(mcs, name, bases, ns):
        ...
```

Помни: `mcs` — это сам метакласс, `cls` — создаваемый класс, `obj` — будущий экземпляр. Три разных уровня.

### Чрезмерное усложнение

Метакласс легко превращает простой код в нечитаемый:
```python
class StrangeMeta(type):
    def __new__(mcs, name, bases, ns):
        # 50 строк магии
        ...
```

Альтернатива почти всегда есть. **Если ты не пишешь фреймворк** — подумай, нужен ли метакласс.

---

## 16. Что нужно запомнить

- Класс — это объект, экземпляр метакласса (по умолчанию `type`).
- `class Foo: ...` ≡ `type("Foo", bases, namespace)`.
- Метакласс — подкласс `type`, переопределяет `__new__`/`__init__`/`__call__`.
- Применения: реестры, валидация структуры, синглтоны, ORM.
- `__init_subclass__` — простая альтернатива для большинства случаев.
- `ABCMeta` — стандартный метакласс для абстрактных классов.
- Декораторы класса — другая альтернатива.
- Метаклассы наследуются. Конфликты — через общий метакласс.
- Используй метаклассы только когда другие способы не подходят.

После метаклассов — следующая глубокая тема: **MRO и множественное наследование**. Алгоритм C3, как `super()` находит правильного предка, и почему diamond-наследование работает.
