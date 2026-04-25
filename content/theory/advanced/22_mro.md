# MRO и множественное наследование — от 0 до 100%

MRO (Method Resolution Order) — порядок, в котором Python ищет методы при наследовании. Когда у тебя один родитель — это просто. Когда два, три, ромбовидное наследование — становится интересно. Python использует алгоритм **C3 linearization**, и понимание его обязательно для серьёзной работы с ООП.

Эта тема — про:
- как Python находит метод при `obj.method()`;
- что такое MRO и как его прочитать;
- как работает `super()`;
- почему diamond inheritance в Python не ломается;
- классические ловушки и паттерны.

---

## 1. Простой случай: одно наследование

```python
class A:
    def hello(self):
        print("A")

class B(A):
    pass

b = B()
b.hello()    # 'A' — нашёл в родителе
```

Python ищет `hello` в `B`, не находит → ищет в `A`, находит. Здесь логика очевидна.

---

## 2. Множественное наследование

Можно наследовать от **нескольких** классов:
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
c.hello()    # 'A'
```

Почему `A`, не `B`? Python использует **MRO** для определения порядка поиска. По умолчанию MRO учитывает порядок родителей слева направо.

```python
print(C.__mro__)
# (<class 'C'>, <class 'A'>, <class 'B'>, <class 'object'>)
```

Список порядка: сам класс → первый родитель → второй родитель → ... → object.

Поиск идёт **по этому порядку**: первый класс, в котором найден метод, выигрывает.

---

## 3. Ромбовидное наследование (diamond)

Классическая проблема ООП:

```
        A
       / \
      B   C
       \ /
        D
```

```python
class A:
    def hello(self):
        print("A")

class B(A):
    def hello(self):
        print("B")

class C(A):
    def hello(self):
        print("C")

class D(B, C):
    pass

d = D()
d.hello()        # 'B'

print(D.__mro__)
# (<class 'D'>, <class 'B'>, <class 'C'>, <class 'A'>, <class 'object'>)
```

Обрати внимание: `A` идёт **после** `C`, не сразу после `B`. Это и есть C3 — он гарантирует что родитель не появится раньше своих потомков.

Если бы MRO был «depth-first» (как в старом Python), было бы `D → B → A → C → A → object` — `A` посетили бы дважды. C3 это исправляет.

---

## 4. C3 linearization — алгоритм

C3 — алгоритм, который строит MRO так, чтобы:
1. Сам класс — первый.
2. Родители (в порядке объявления) перед более далёкими предками.
3. Никто не появляется дважды.
4. Сохраняется порядок «слева направо» из объявления.

Формально, MRO класса C, наследующего от B1, B2, ..., Bn:

```
L[C] = C + merge(L[B1], L[B2], ..., L[Bn], [B1, B2, ..., Bn])
```

`merge` — операция, которая берёт первый элемент первого списка, проверяет что он не в «хвостах» других списков, и если ок — добавляет; иначе пробует следующий список.

Для D(B, C) с B(A), C(A):
```
L[A] = [A, object]
L[B] = [B, A, object]
L[C] = [C, A, object]

L[D] = D + merge(L[B], L[C], [B, C])
     = D + merge([B,A,object], [C,A,object], [B,C])
     = D + B + merge([A,object], [C,A,object], [C])      # B не в хвостах
     = D + B + C + merge([A,object], [A,object], [])     # A в хвосте 2-го, пропускаем; берём C
     = D + B + C + A + object
     = [D, B, C, A, object]
```

Если C3 не может построить MRO — `TypeError`:
```python
class A: pass
class B(A): pass
class C(A, B): pass    # TypeError: Cannot create a consistent method resolution
```

Здесь A должен быть и до B (как первый родитель), и после B (как родитель B). Противоречие.

---

## 5. `super()` — вызов «следующего» в MRO

`super()` **не** обязательно вызывает «родителя». Он вызывает **следующего в MRO** относительно текущего класса.

```python
class A:
    def hello(self):
        print("A")

class B(A):
    def hello(self):
        print("B")
        super().hello()

class C(A):
    def hello(self):
        print("C")
        super().hello()

class D(B, C):
    def hello(self):
        print("D")
        super().hello()

d = D()
d.hello()
```

Вывод:
```
D
B
C
A
```

Это порядок MRO! `super()` в B вызывает `C.hello`, не `A.hello`. Это потому что `super()` смотрит на MRO **экземпляра** (D), а не на структуру класса B.

Это часто называют «cooperative multiple inheritance» — «кооперативное множественное наследование». Для него все методы должны вызывать `super()`.

---

## 6. `super()` без аргументов и с

В Python 3 `super()` — короткая форма:
```python
class B(A):
    def hello(self):
        super().hello()              # короткое
        super(B, self).hello()        # эквивалент, длинное
```

Длинная форма даёт контроль над тем, **с какого класса** начинать поиск:
```python
class D(B, C):
    def hello(self):
        super(C, self).hello()    # начать ПОСЛЕ C в MRO → A
```

Используется редко. Обычно `super()` достаточно.

---

## 7. Ловушка: пропустил `super()`

```python
class A:
    def __init__(self):
        print("A.__init__")

class B(A):
    def __init__(self):
        print("B.__init__")
        # forgot super().__init__()

class C(A):
    def __init__(self):
        print("C.__init__")
        super().__init__()

class D(B, C):
    def __init__(self):
        print("D.__init__")
        super().__init__()

D()
# D.__init__
# B.__init__
# (C.__init__ не вызван — потому что B забыл super)
```

Если хоть один класс «не кооперативен» — цепочка ломается. Поэтому **всегда** вызывай `super().__init__()` если есть шанс что класс будет в множественном наследовании.

---

## 8. `**kwargs` для cooperative inheritance

```python
class A:
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        print("A")

class B:
    def __init__(self, x=0, **kwargs):
        super().__init__(**kwargs)
        self.x = x
        print(f"B({x})")

class C:
    def __init__(self, y=0, **kwargs):
        super().__init__(**kwargs)
        self.y = y
        print(f"C({y})")

class D(B, C, A):
    pass

D(x=1, y=2)
# A
# C(2)
# B(1)
```

Каждый класс берёт свои аргументы из `**kwargs`, остальное передаёт дальше. Это паттерн для устойчивого MI.

---

## 9. `isinstance` и `issubclass`

```python
class A: pass
class B(A): pass
class C(B): pass

c = C()
isinstance(c, C)         # True
isinstance(c, B)         # True (наследник)
isinstance(c, A)         # True
isinstance(c, object)    # True

issubclass(C, B)         # True
issubclass(C, A)         # True
issubclass(B, A)         # True
issubclass(A, A)         # True (класс — подкласс себя)

# с tuple — «или»:
isinstance(c, (B, A))    # True если хоть один
```

`isinstance` ходит по MRO. `type(c) == B` — нет (точное сравнение).

---

## 10. Виды множественного наследования

### Implementation inheritance — «классический»

```python
class FileLogger:
    def log(self, msg): ...

class TimestampLogger:
    def log(self, msg): ...

class FileTimestampLogger(FileLogger, TimestampLogger):
    pass
```

Сложный, ломкий, не рекомендуется. Предпочти **композицию**.

### Mixins — рекомендуемый паттерн

Mixin — класс, **только добавляющий поведение**, никогда не используемый напрямую:
```python
class JSONMixin:
    def to_json(self):
        import json
        return json.dumps(self.__dict__)

class TimestampMixin:
    def __init__(self):
        from datetime import datetime
        self.created_at = datetime.now()

class User(JSONMixin, TimestampMixin):
    def __init__(self, name):
        super().__init__()
        self.name = name

u = User("Alice")
print(u.to_json())
```

Mixin-ы:
- маленькие;
- ортогональные (не пересекаются);
- никогда не инстантиируются сами;
- обычно идут **первыми** в списке родителей (чтобы переопределять).

### Interface inheritance (через ABC)

Описывает интерфейс, который классы должны реализовать:
```python
from abc import ABC, abstractmethod

class Drawable(ABC):
    @abstractmethod
    def draw(self): pass

class Resizable(ABC):
    @abstractmethod
    def resize(self, scale): pass

class Image(Drawable, Resizable):
    def draw(self): ...
    def resize(self, scale): ...
```

Это «питоновский» вариант интерфейсов из Java/C#.

---

## 11. Пример: настоящий MI в библиотеке

Tkinter:
```python
class Button(Widget):
    pass

class Widget(BaseWidget, Pack, Place, Grid):
    pass
```

Виджет наследует геометрические менеджеры (Pack, Place, Grid) — это даёт ему методы `.pack()`, `.place()`, `.grid()`.

Django views:
```python
class UserListView(LoginRequiredMixin, ListView):
    model = User
```

LoginRequiredMixin добавляет проверку авторизации.

---

## 12. type(obj) vs obj.__class__

```python
class Foo:
    pass

f = Foo()
print(type(f))         # <class 'Foo'>
print(f.__class__)     # <class 'Foo'>
```

Обычно одинаково. Но `__class__` можно перезаписать (и иногда это делают для прокси-объектов):
```python
f.__class__ = Bar    # экземпляр меняет класс
```

Делать так — обычно плохо, но иногда полезно.

---

## 13. Динамическое создание подкласса

```python
class A: pass

# через type:
B = type("B", (A,), {"x": 1})
b = B()

# с метаклассом:
class Meta(type): pass
C = Meta("C", (A,), {"y": 2})
```

Это и есть та же магия, что в `class C(A, metaclass=Meta): ...`.

---

## 14. Типичные ошибки

### Полагаться на порядок родителей без проверки MRO

```python
class M1: action = "left"
class M2: action = "right"

class C(M1, M2): pass

print(C.action)    # 'left' — но это очевидно?
```

Если хоть немного нетривиально — посмотри `C.__mro__`.

### Забыть `super()` в `__init__`

См. п.7.

### Использовать `super(ParentClass, self)` где не нужно

```python
class B(A):
    def __init__(self):
        super(A, self).__init__()    # ⚠️ начинает ПОСЛЕ A — пропустит A!
```

Должно быть `super().__init__()` (т.е. `super(B, self).__init__()`).

### MI там, где нужна композиция

```python
class Car(Engine, Wheels):    # ⚠️ машина — НЕ engine
    pass

# лучше:
class Car:
    def __init__(self):
        self.engine = Engine()
        self.wheels = Wheels()
```

### Diamond с разными signatures

```python
class A:
    def __init__(self, a): self.a = a
class B(A):
    def __init__(self, a, b):
        super().__init__(a)
        self.b = b
class C(A):
    def __init__(self, a, c):
        super().__init__(a)
        self.c = c
class D(B, C):
    def __init__(self, a, b, c):
        super().__init__(a, b)    # ⚠️ super() = B.__init__(a, b), но потом C.__init__(a, c) с какими аргументами?
```

Чтобы это работало — все `__init__` принимают `**kwargs` и передают дальше. См. п.8.

---

## 15. Просмотр MRO в реальном коде

```python
class Foo:
    def hello(self): print("Foo")

print(Foo.__mro__)
# (<class 'Foo'>, <class 'object'>)

print(Foo.mro())
# то же самое, через метод

# Найти в каком классе определён метод:
import inspect
for cls in type(obj).__mro__:
    if "hello" in cls.__dict__:
        print(f"hello defined in {cls.__name__}")
        break
```

В IPython / IDE есть «Where defined» — внутренне это и делается.

---

## 16. Что нужно запомнить

- MRO — порядок поиска методов и атрибутов при наследовании.
- C3 linearization гарантирует: сам класс первый, родители раньше предков, никто не дублируется.
- `super()` идёт по MRO, не по родителям. В сложных иерархиях вызывает «следующего», не обязательно родителя.
- Для надёжного MI — все классы вызывают `super().__init__(...)` и принимают `**kwargs`.
- Mixin-ы — рекомендуемый паттерн МИ; обычно ставятся первыми.
- `isinstance`/`issubclass` ходят по MRO.
- MI без понимания MRO — источник багов; в большинстве случаев предпочти композицию.

С этой темы началась настоящая работа с Python-фундаментом. Дальше — самые востребованные практические темы: asyncio, многопоточность/процессы, типизация, декораторы продвинутые, pytest, профилирование. Эти 6 тем — must-have для современного Python-разработчика.
