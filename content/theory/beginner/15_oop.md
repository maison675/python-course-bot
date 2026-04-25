# ООП — от 0 до 100%

ООП (Объектно-ориентированное программирование) — парадигма, в которой **код организован вокруг объектов**. Объект — это «сущность» с состоянием (атрибуты) и поведением (методы). Список «студентов» с именами, оценками, методами `add_grade(...)` — это естественно ООП.

В Python ООП — особое: всё **является** объектом. Числа, строки, функции, модули, классы — даже сами классы. Это глубоко влияет на язык и делает многие приёмы (метаклассы, декораторы, динамический dispatch) возможными.

Эта тема — фундамент. Без понимания классов ты не сможешь толком пользоваться большинством библиотек (Django ORM, FastAPI, SQLAlchemy, pytest fixtures — всё на классах).

---

## 1. Зачем ООП

Представь, что у тебя есть данные о студентах. Без ООП:
```python
students = [
    {"name": "Alice", "grades": [90, 85]},
    {"name": "Bob", "grades": [70, 80]},
]

def add_grade(student, grade):
    student["grades"].append(grade)

def average(student):
    return sum(student["grades"]) / len(student["grades"])

add_grade(students[0], 95)
print(average(students[0]))    # 90
```

Работает, но:
- легко перепутать ключи словаря;
- функции и данные оторваны;
- трудно переиспользовать.

С ООП:
```python
class Student:
    def __init__(self, name):
        self.name = name
        self.grades = []
    def add_grade(self, grade):
        self.grades.append(grade)
    def average(self):
        return sum(self.grades) / len(self.grades)

alice = Student("Alice")
alice.add_grade(90)
alice.add_grade(95)
print(alice.average())    # 92.5
```

Чище: данные и поведение **связаны**, типобезопасно (ide подскажет атрибуты), легко расширять (наследование).

---

## 2. Класс и экземпляр

**Класс** — шаблон, описывающий какой объект может быть.
**Экземпляр** (instance) — конкретный объект, созданный по шаблону.

```python
class Dog:                 # класс
    pass

rex = Dog()                # экземпляр
buddy = Dog()              # ещё один экземпляр

print(type(rex))           # <class '__main__.Dog'>
print(isinstance(rex, Dog))  # True
print(rex is buddy)        # False — разные объекты
```

Класс — **тоже объект** (можно передать в функцию, положить в список). А `type` — это «класс классов» (метакласс).

---

## 3. Атрибуты экземпляра

```python
class Dog:
    def __init__(self, name, age):    # конструктор
        self.name = name
        self.age = age

rex = Dog("Rex", 5)
print(rex.name)    # 'Rex'
rex.age = 6        # можно изменить
```

`self` — ссылка на сам экземпляр. Внутри метода `self.name = name` сохраняет значение в атрибуте экземпляра. Имя `self` — конвенция (можно `this`, но не делай так).

Каждый экземпляр имеет **свой** набор атрибутов:
```python
rex = Dog("Rex", 5)
buddy = Dog("Buddy", 3)
print(rex.name, buddy.name)    # Rex Buddy — разные
```

---

## 4. Атрибуты класса

```python
class Dog:
    species = "Canis lupus"        # атрибут класса
    
    def __init__(self, name):
        self.name = name           # атрибут экземпляра

print(Dog.species)              # 'Canis lupus'
rex = Dog("Rex")
print(rex.species)              # 'Canis lupus' — наследуется
```

Атрибуты класса **общие для всех** экземпляров. Атрибут экземпляра — индивидуальный.

### Подвох: mutable атрибут класса

```python
class Dog:
    tricks = []              # ⚠️ ОБЩИЙ для всех

    def __init__(self, name):
        self.name = name

rex = Dog("Rex")
rex.tricks.append("sit")
buddy = Dog("Buddy")
print(buddy.tricks)          # ['sit'] — !!! общий
```

Mutable атрибуты делай в `__init__`:
```python
class Dog:
    def __init__(self, name):
        self.name = name
        self.tricks = []     # ✅ свой у каждого
```

### Перекрытие

Если задать атрибут экземпляра с тем же именем — он **перекроет** атрибут класса для этого экземпляра:
```python
class Dog:
    species = "Canis lupus"

rex = Dog()
rex.species = "Custom"      # создал атрибут экземпляра
print(rex.species)          # 'Custom'
print(Dog.species)          # 'Canis lupus' — класс не изменился
```

---

## 5. Методы

Метод — это функция, **связанная с классом**.

### Метод экземпляра

```python
class Dog:
    def __init__(self, name):
        self.name = name
    
    def bark(self):
        print(f"{self.name} says woof!")

rex = Dog("Rex")
rex.bark()         # эквивалентно Dog.bark(rex) — Rex says woof!
```

`rex.bark()` — это сахар для `Dog.bark(rex)`. Поэтому первый параметр всегда `self`.

### Статический метод (`@staticmethod`)

Метод, который не использует ни `self`, ни класс:
```python
class MathUtils:
    @staticmethod
    def square(x):
        return x ** 2

MathUtils.square(5)        # 25 — можно вызвать без экземпляра
```

Это просто функция, помещённая внутрь класса для группировки. Не связан с состоянием.

### Метод класса (`@classmethod`)

Принимает класс (`cls`) вместо экземпляра:
```python
class Dog:
    count = 0
    
    def __init__(self, name):
        self.name = name
        Dog.count += 1
    
    @classmethod
    def total(cls):
        return cls.count

Dog("Rex")
Dog("Buddy")
print(Dog.total())    # 2
```

Часто используется для **альтернативных конструкторов**:
```python
class Date:
    def __init__(self, year, month, day):
        self.year, self.month, self.day = year, month, day
    
    @classmethod
    def from_string(cls, s):
        y, m, d = map(int, s.split("-"))
        return cls(y, m, d)
    
    @classmethod
    def today(cls):
        import datetime
        t = datetime.date.today()
        return cls(t.year, t.month, t.day)

d1 = Date(2024, 1, 1)
d2 = Date.from_string("2024-12-31")
d3 = Date.today()
```

---

## 6. Конструктор `__init__` и `__new__`

`__init__` — НЕ конструктор, а **инициализатор**. К моменту его вызова объект уже создан.

Настоящий конструктор — `__new__`:
```python
class Foo:
    def __new__(cls, *args, **kwargs):
        print("__new__ called")
        instance = super().__new__(cls)
        return instance
    
    def __init__(self, x):
        print("__init__ called")
        self.x = x

f = Foo(10)
# __new__ called
# __init__ called
```

Обычно ты переопределяешь только `__init__`. `__new__` нужен в редких случаях:
- паттерн Singleton;
- immutable классы (наследники tuple, str);
- метаклассы.

---

## 7. Магические методы (dunder)

Методы с двойным подчёркиванием — **магические** (dunder = "double underscore"). Они вызываются Python неявно, делают объект «питоновским».

### `__str__` и `__repr__`

```python
class Point:
    def __init__(self, x, y):
        self.x, self.y = x, y
    def __str__(self):
        return f"({self.x}, {self.y})"
    def __repr__(self):
        return f"Point({self.x}, {self.y})"

p = Point(1, 2)
print(p)            # (1, 2) — __str__
str(p)              # '(1, 2)'
repr(p)             # 'Point(1, 2)' — __repr__
[p, p]              # [Point(1, 2), Point(1, 2)] — __repr__ внутри коллекций
```

- `__str__` — для людей (понятный вид).
- `__repr__` — для разработчиков (точный вид, желательно «чтобы можно было eval()»).

Если определить только `__repr__` — `str()` тоже его использует.

### `__eq__` и `__hash__`

```python
class Point:
    def __init__(self, x, y):
        self.x, self.y = x, y
    def __eq__(self, other):
        if not isinstance(other, Point):
            return NotImplemented
        return self.x == other.x and self.y == other.y
    def __hash__(self):
        return hash((self.x, self.y))

p1 = Point(1, 2)
p2 = Point(1, 2)
print(p1 == p2)    # True
print(hash(p1) == hash(p2))    # True
```

**Контракт**: если `a == b`, то `hash(a) == hash(b)`. Иначе — баги в set/dict.

Если переопределяешь `__eq__`, Python автоматически делает `__hash__ = None` (объект становится не хешируемым) — нужно явно определить `__hash__`.

### Сравнения

```python
def __lt__(self, other): ...    # <
def __le__(self, other): ...    # <=
def __gt__(self, other): ...    # >
def __ge__(self, other): ...    # >=
```

Или один декоратор `@functools.total_ordering` достроит остальные если есть `__eq__` и `__lt__`.

### Операторы

```python
def __add__(self, other): ...        # +
def __sub__(self, other): ...        # -
def __mul__(self, other): ...        # *
def __truediv__(self, other): ...    # /
def __floordiv__(self, other): ...   # //
def __mod__(self, other): ...        # %
def __pow__(self, other): ...        # **
```

Подробно — см. тему «Операторы».

### Контейнеры

```python
def __len__(self): ...
def __getitem__(self, key): ...
def __setitem__(self, key, value): ...
def __delitem__(self, key): ...
def __contains__(self, item): ...
def __iter__(self): ...
```

С `__getitem__` и `__len__` объект становится «как список»:
```python
class MyList:
    def __init__(self, data):
        self.data = data
    def __len__(self):
        return len(self.data)
    def __getitem__(self, i):
        return self.data[i]

ml = MyList([1, 2, 3])
print(len(ml))     # 3
print(ml[0])       # 1
for x in ml:       # __iter__ автоматически если есть __getitem__
    print(x)
```

### Контекстный менеджер

```python
def __enter__(self): ...
def __exit__(self, exc_type, exc_val, exc_tb): ...
```

См. тему «Файлы».

### Вызываемость

```python
class Multiplier:
    def __init__(self, k):
        self.k = k
    def __call__(self, x):
        return x * self.k

times3 = Multiplier(3)
print(times3(5))   # 15 — объект как функция
```

---

## 8. Наследование

```python
class Animal:
    def __init__(self, name):
        self.name = name
    def speak(self):
        print(f"{self.name} makes a sound")

class Dog(Animal):
    def speak(self):
        print(f"{self.name} barks")

class Cat(Animal):
    def speak(self):
        print(f"{self.name} meows")

rex = Dog("Rex")
rex.speak()        # Rex barks

murka = Cat("Murka")
murka.speak()      # Murka meows
```

`Dog` **наследует** от `Animal` — получает все его атрибуты и методы. Можно **переопределить** (override) методы.

### `super()` — вызов родителя

```python
class Animal:
    def __init__(self, name):
        self.name = name

class Dog(Animal):
    def __init__(self, name, breed):
        super().__init__(name)         # вызвать родительский __init__
        self.breed = breed

rex = Dog("Rex", "Labrador")
print(rex.name, rex.breed)
```

`super()` — единственный «правильный» способ вызвать родителя (с учётом множественного наследования и MRO).

### Множественное наследование

```python
class A:
    def hello(self):
        print("A")

class B:
    def hello(self):
        print("B")

class C(A, B):
    pass

c = C()
c.hello()    # A — вызывается первый родитель в списке
print(C.__mro__)
# (<class 'C'>, <class 'A'>, <class 'B'>, <class 'object'>)
```

MRO (Method Resolution Order) — порядок поиска метода. Алгоритм C3. Подробно — в продвинутом треке.

Все классы в Python наследуются от `object` (явно или неявно).

### Проверки

```python
isinstance(rex, Dog)        # True
isinstance(rex, Animal)     # True (наследник)
isinstance(rex, object)     # True (всё — object)
issubclass(Dog, Animal)     # True
type(rex) == Dog            # True, но не работает с наследниками
type(rex) == Animal         # False
```

`isinstance` лучше, чем `type(x) ==`, потому что работает с наследниками.

---

## 9. Инкапсуляция: «приватные» атрибуты

Python **не имеет** настоящих private. Но есть **конвенции**:

### `_name` — «не трогай снаружи»

```python
class Account:
    def __init__(self):
        self._balance = 0      # «приватный» по конвенции
    def deposit(self, amount):
        self._balance += amount
    def get_balance(self):
        return self._balance

a = Account()
a.deposit(100)
print(a.get_balance())    # 100
print(a._balance)         # 100 — формально доступно, но «нельзя»
```

Один подчёркивающий — «hint, не лезь». IDE и линтеры предупреждают.

### `__name` — name mangling

Двойной подчёркивающий приводит к **переименованию** атрибута:
```python
class Account:
    def __init__(self):
        self.__balance = 0
    def get_balance(self):
        return self.__balance

a = Account()
a.__balance              # AttributeError
a._Account__balance      # 0 — реальное имя
```

Делается чтобы избежать конфликтов в наследовании. Не для security — обойти можно.

### `@property` — управляемый доступ

```python
class Temperature:
    def __init__(self, celsius):
        self._celsius = celsius
    
    @property
    def celsius(self):
        return self._celsius
    
    @celsius.setter
    def celsius(self, value):
        if value < -273.15:
            raise ValueError("ниже абсолютного нуля")
        self._celsius = value
    
    @property
    def fahrenheit(self):
        return self._celsius * 9/5 + 32

t = Temperature(20)
print(t.celsius)       # 20
t.celsius = 25
print(t.fahrenheit)    # 77.0
t.celsius = -300       # ValueError
```

`@property` превращает метод в **атрибут на чтение**. `@x.setter` добавляет setter. Используй для:
- валидации;
- вычисляемых свойств;
- при рефакторинге `obj.x = ...` в `obj._x = ...` без слома API.

---

## 10. Полиморфизм

Возможность одного интерфейса работать с разными типами:

```python
class Shape:
    def area(self):
        raise NotImplementedError

class Circle(Shape):
    def __init__(self, r):
        self.r = r
    def area(self):
        return 3.14 * self.r ** 2

class Square(Shape):
    def __init__(self, s):
        self.s = s
    def area(self):
        return self.s ** 2

shapes = [Circle(5), Square(4)]
for shape in shapes:
    print(shape.area())     # каждый класс — своя реализация
```

В Python — **дакТайпинг**: «если оно крякает как утка». Не нужно явно указывать что класс реализует интерфейс — достаточно иметь нужные методы:

```python
class Vector:
    def __len__(self):
        return 3

v = Vector()
print(len(v))    # 3 — работает, потому что у объекта есть __len__
```

### Абстрактные классы

Когда хочешь принудить наследников реализовать методы:
```python
from abc import ABC, abstractmethod

class Shape(ABC):
    @abstractmethod
    def area(self):
        pass

class Circle(Shape):
    def __init__(self, r):
        self.r = r
    def area(self):
        return 3.14 * self.r ** 2

# Shape()  -> TypeError — нельзя инстанциировать абстрактный класс
Circle(5)    # OK
```

---

## 11. dataclass — современный способ

Для классов «только данные» — `@dataclass`:
```python
from dataclasses import dataclass

@dataclass
class Point:
    x: int
    y: int

p = Point(1, 2)
print(p)              # Point(x=1, y=2) — авто __repr__
p2 = Point(1, 2)
print(p == p2)        # True — авто __eq__
```

`@dataclass` автоматически генерирует:
- `__init__` (на основе аннотаций);
- `__repr__`;
- `__eq__`;
- опционально `__lt__`, `__hash__`, и другие.

С опциями:
```python
@dataclass(frozen=True)         # immutable
class Point:
    x: int = 0                   # default
    y: int = 0

@dataclass(order=True)           # с сортировкой
class Score:
    value: int
    name: str

scores = [Score(90, "Alice"), Score(85, "Bob")]
sorted(scores)                   # по value
```

`field`:
```python
from dataclasses import dataclass, field

@dataclass
class Container:
    items: list = field(default_factory=list)    # вместо mutable default
```

Используй `@dataclass` вместо классов с одним `__init__` и атрибутами. Намного меньше кода и меньше ошибок.

---

## 12. Композиция vs наследование

Наследование — «есть-как» (Dog **есть** Animal).
Композиция — «имеет» (Car **имеет** Engine).

```python
# Композиция
class Engine:
    def start(self):
        print("Brrr")

class Car:
    def __init__(self):
        self.engine = Engine()
    def drive(self):
        self.engine.start()
        print("driving")

c = Car()
c.drive()
```

Современная мудрость — **предпочитай композицию наследованию**. Наследование жёстко связывает классы, композиция гибче.

Глубокие иерархии (5+ уровней) — обычно плохой дизайн.

---

## 13. `__slots__` — оптимизация

По умолчанию у каждого экземпляра — словарь `__dict__` для атрибутов:
```python
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

p = Point(1, 2)
print(p.__dict__)    # {'x': 1, 'y': 2}
p.z = 3              # можно добавить произвольный атрибут!
```

Это гибкое, но дорого по памяти. Для миллионов мелких объектов — `__slots__`:
```python
class Point:
    __slots__ = ("x", "y")
    def __init__(self, x, y):
        self.x = x
        self.y = y

p = Point(1, 2)
p.z = 3              # AttributeError — нельзя добавлять
```

Преимущества:
- меньше памяти (~50% для маленьких объектов);
- быстрее доступ к атрибутам;
- защита от опечаток в именах атрибутов.

Подробно — в продвинутом треке.

---

## 14. Декораторы класса

```python
def add_repr(cls):
    def __repr__(self):
        attrs = ", ".join(f"{k}={v}" for k, v in self.__dict__.items())
        return f"{cls.__name__}({attrs})"
    cls.__repr__ = __repr__
    return cls

@add_repr
class Foo:
    def __init__(self, a, b):
        self.a, self.b = a, b

print(Foo(1, 2))    # Foo(a=1, b=2)
```

Декораторы класса — функция, принимающая класс и возвращающая модифицированный.

Самый известный — `@dataclass` (выше).

---

## 15. Типичные ошибки

### Mutable default class attribute

```python
class Foo:
    items = []        # ⚠️ общий

a = Foo()
b = Foo()
a.items.append(1)
print(b.items)        # [1] — !!!
```

Решение: в `__init__`.

### Не вызвал super().__init__()

```python
class Animal:
    def __init__(self, name):
        self.name = name

class Dog(Animal):
    def __init__(self, name, breed):
        # super().__init__(name)  забыл!
        self.breed = breed

rex = Dog("Rex", "Lab")
print(rex.name)    # AttributeError
```

### `self` забыл

```python
class Foo:
    def method(x):    # ⚠️ нет self
        ...

f = Foo()
f.method(5)    # TypeError
```

Решение: первым параметром всегда `self`.

### Перепутал `@classmethod` и `@staticmethod`

```python
class Foo:
    @staticmethod
    def make():
        return Foo()    # хардкод имени класса
    
    @classmethod
    def make(cls):
        return cls()    # ✅ работает в наследниках
```

`classmethod` — когда нужен класс. `staticmethod` — когда вообще ничего из класса.

### Cравнение без `__eq__`

```python
class Foo:
    def __init__(self, x):
        self.x = x

a = Foo(1)
b = Foo(1)
print(a == b)    # False — по умолчанию сравнение по id
```

Определи `__eq__`.

---

## 16. Что нужно запомнить

- Класс — шаблон, экземпляр — конкретный объект.
- `__init__` — инициализатор; `__new__` — конструктор (редко переопределяется).
- Атрибуты класса общие, экземпляра индивидуальные. Mutable атрибуты — в `__init__`.
- Магические методы (`__str__`, `__eq__`, `__add__`, ...) делают объект «питоновским».
- Наследование через `class Child(Parent):`, вызов родителя — `super()`.
- Полиморфизм через дакТайпинг или явные ABC.
- `@property` для управляемого доступа к атрибуту.
- `@dataclass` — автогенерация `__init__`, `__repr__`, `__eq__`.
- Композиция > наследование в большинстве случаев.
- Нет настоящих private — конвенция `_x` и `__x` (mangling).

ООП — это значительная часть мысленной модели Python. Дальше последняя тема начинающего трека — comprehensions, lambda, map/filter — функциональный стиль.
