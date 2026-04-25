# Исключения — от 0 до 100%

Исключения — это механизм **обработки ошибок**. Программа что-то делает, что-то идёт не так — деление на ноль, файл не найден, сеть упала. Без исключений ты бы вынужден был после каждой операции проверять «удалось или нет?» и руками разруливать. С исключениями — ошибка «всплывает» наверх, пока кто-то не «поймает» её.

В Python исключения — **обычные объекты**, у них есть тип и сообщение. И они часть нормального потока программы: например, итерация работает на `StopIteration`, выход из цикла генератора — на исключении.

Понимание исключений делит программистов на «начинающих» (страх перед ошибками, везде try/except) и «опытных» (знают где, что и как ловить, и когда лучше не ловить вообще).

---

## 1. Что такое исключение

Когда что-то идёт не так, Python:
1. Создаёт **объект исключения** определённого типа.
2. Отдаёт управление наверх, пока не найдёт обработчик (`try/except`).
3. Если обработчика нет — программа завершается, печатается **traceback**.

```python
n = int("abc")    # ValueError: invalid literal for int() with base 10: 'abc'
```

Traceback:
```
Traceback (most recent call last):
  File "script.py", line 1, in <module>
    n = int("abc")
ValueError: invalid literal for int() with base 10: 'abc'
```

Тип исключения: `ValueError`. Сообщение: `'invalid literal...'`.

---

## 2. try/except — основа

```python
try:
    n = int(input("число: "))
except ValueError:
    print("Это не число!")
```

Если внутри `try` возникнет `ValueError` — Python выполнит `except`-блок. Если возникнет другое исключение — оно пройдёт мимо и пойдёт выше.

### Несколько типов

```python
try:
    risky()
except (TypeError, ValueError):
    print("Что-то не так")
```

### Несколько обработчиков

```python
try:
    risky()
except ValueError:
    print("Неверное значение")
except TypeError:
    print("Неверный тип")
```

Проверяются по порядку. Первый подходящий — выполняется.

### Получить объект исключения

```python
try:
    n = int("abc")
except ValueError as e:
    print(f"Ошибка: {e}")        # 'invalid literal...'
    print(type(e).__name__)      # 'ValueError'
    print(e.args)                # ('invalid literal...',)
```

---

## 3. else и finally

### `else` — если не было исключения

```python
try:
    n = int(input())
except ValueError:
    print("ошибка")
else:
    print(f"Успешно: {n}")
```

`else` выполнится **только если** `try` прошёл без исключения. Полезен для разделения «опасной» части и «обработки результата».

### `finally` — всегда

```python
try:
    f = open("data.txt")
    process(f)
except FileNotFoundError:
    print("нет файла")
finally:
    f.close()        # выполнится даже если был exception
```

`finally` выполняется **всегда**: после try (если без исключения), после except (если было обработано), даже если внутри try был return или raise.

В современном коде `finally` часто заменён на `with` (контекстный менеджер).

### Полный синтаксис

```python
try:
    # опасный код
except SomeError:
    # обработка
except OtherError:
    # обработка
else:
    # если не было исключения
finally:
    # всегда
```

---

## 4. Иерархия исключений

Все исключения наследуются от `BaseException`. Иерархия (упрощённо):
```
BaseException
├── SystemExit         (sys.exit())
├── KeyboardInterrupt  (Ctrl+C)
├── GeneratorExit      (закрытие генератора)
└── Exception          ← обычно ловят это или потомков
    ├── ArithmeticError
    │   ├── ZeroDivisionError
    │   ├── OverflowError
    │   └── FloatingPointError
    ├── LookupError
    │   ├── IndexError
    │   └── KeyError
    ├── ValueError
    ├── TypeError
    ├── AttributeError
    ├── NameError
    ├── OSError
    │   ├── FileNotFoundError
    │   ├── PermissionError
    │   └── ConnectionError
    ├── RuntimeError
    │   └── RecursionError
    ├── StopIteration
    └── ...
```

**`except ParentError`** ловит все дочерние:
```python
try:
    ...
except OSError:    # ловит и FileNotFoundError, и PermissionError
    ...
```

`except Exception` — ловит **почти всё** (но не KeyboardInterrupt и SystemExit). Часто используется как fallback:
```python
try:
    ...
except Exception as e:
    log.error(f"Что-то пошло не так: {e}")
```

`except BaseException` — ловит **всё**, включая Ctrl+C. Почти никогда не нужно.

`except:` без типа — то же что `except BaseException` — **антипаттерн**.

---

## 5. Самые частые встроенные исключения

### `ValueError` — неверное значение

```python
int("abc")            # ValueError
float("xyz")
list.index(x)         # если x нет в списке
str.encode("invalid-codec")
```

### `TypeError` — неверный тип

```python
"a" + 5               # TypeError: can only concatenate str to str
len(42)               # TypeError: object of type 'int' has no len()
sorted([1, "a"])      # TypeError: '<' not supported between 'int' and 'str'
```

### `IndexError` — индекс за пределами

```python
[1, 2, 3][10]         # IndexError
"abc"[100]
```

### `KeyError` — нет такого ключа

```python
{"a": 1}["b"]         # KeyError
```

### `AttributeError` — нет такого атрибута

```python
None.method()         # AttributeError
"abc".nonexistent()
```

### `FileNotFoundError`

```python
open("nonexistent.txt")
```

### `ZeroDivisionError`

```python
1 / 0
1 // 0
1 % 0
```

### `RecursionError`

```python
def f(): f()
f()
```

### `ImportError` / `ModuleNotFoundError`

```python
import nonexistent_module
```

### `KeyboardInterrupt`

Когда пользователь нажал Ctrl+C. Особенный — наследник `BaseException`, не `Exception`.

```python
try:
    while True:
        ...
except KeyboardInterrupt:
    print("Прервано пользователем")
```

### `StopIteration`

Когда итератор закончился. Используется внутри `for` для остановки:
```python
it = iter([1, 2, 3])
next(it)    # 1
next(it)    # 2
next(it)    # 3
next(it)    # StopIteration
```

---

## 6. raise — поднять исключение

```python
def divide(a, b):
    if b == 0:
        raise ValueError("Деление на ноль")
    return a / b

try:
    divide(1, 0)
except ValueError as e:
    print(e)    # 'Деление на ноль'
```

`raise <ExceptionClass>(<message>)` — стандартная форма.

### `raise` без аргумента — переподнять

Внутри `except`:
```python
try:
    risky()
except ValueError:
    log.error("ошибка")
    raise           # переподнимает то же исключение, чтобы шло выше
```

Полезно когда хочешь логировать или сделать что-то промежуточное, но не хочешь подавлять.

### `raise from` — связать с предыдущей причиной

```python
try:
    int("abc")
except ValueError as e:
    raise RuntimeError("Парсинг провалился") from e
```

В traceback увидишь:
```
ValueError: invalid literal for int()
The above exception was the direct cause of the following exception:
RuntimeError: Парсинг провалился
```

Это полезно для **обёртки** низкоуровневой ошибки в высокоуровневую, без потери информации о причине.

### `raise from None` — скрыть причину

```python
except ValueError:
    raise RuntimeError("Чисто новая ошибка") from None
```

Скрывает оригинальную ошибку. Используется когда не хочешь засорять стек.

---

## 7. Свои исключения

```python
class MyError(Exception):
    pass

raise MyError("что-то моё")
```

С полями:
```python
class ValidationError(Exception):
    def __init__(self, field, message):
        super().__init__(f"{field}: {message}")
        self.field = field
        self.message = message

try:
    raise ValidationError("email", "неверный формат")
except ValidationError as e:
    print(e.field, e.message)
```

### Иерархия своих

```python
class AppError(Exception):
    """Базовое для нашего приложения."""

class DatabaseError(AppError):
    pass

class NotFoundError(DatabaseError):
    pass

class UserNotFound(NotFoundError):
    pass

# Можно ловить точно или общо:
try:
    ...
except UserNotFound:    # только эту
    ...
except NotFoundError:   # все NotFound
    ...
except DatabaseError:   # все БД
    ...
except AppError:        # все наши
    ...
```

Хорошая иерархия исключений — признак зрелого приложения.

---

## 8. Кастомные сообщения

```python
raise ValueError(f"Возраст должен быть положительным, получено: {age}")
```

Хорошее сообщение:
- объясняет **что** не так;
- говорит **где** возникло (если не очевидно);
- показывает **значения**, которые вызвали проблему.

Плохое:
```python
raise ValueError("ошибка")    # бесполезно
```

---

## 9. EAFP vs LBYL

Два подхода к написанию кода:

### LBYL — Look Before You Leap

«Сначала проверь, потом действуй»:
```python
if "key" in d:
    val = d["key"]
else:
    val = "default"

if os.path.exists("file.txt"):
    with open("file.txt") as f:
        ...
```

### EAFP — Easier to Ask Forgiveness than Permission

«Делай, ловишь если что»:
```python
try:
    val = d["key"]
except KeyError:
    val = "default"

try:
    with open("file.txt") as f:
        ...
except FileNotFoundError:
    print("нет")
```

В Python **EAFP считается более идиоматичным**. Причины:
- атомарность: между `if exists` и `open` файл может быть удалён (race condition);
- скорость: try/except почти бесплатен в случае без ошибок;
- естественность для динамики типов.

Но иногда LBYL чище:
- проверка простая и быстрая;
- ошибка — частый случай (тогда try/except медленнее).

---

## 10. Подавление исключения

Иногда нужно проигнорировать ошибку:
```python
try:
    risky()
except SomeError:
    pass
```

`pass` — пустой блок, означает «ничего не делать».

⚠️ **Опасно!** Подавлять без логирования — теряешь информацию. Лучше:
```python
try:
    risky()
except SomeError as e:
    log.warning(f"Ошибка: {e}")
```

Или с `contextlib`:
```python
from contextlib import suppress

with suppress(FileNotFoundError):
    os.remove("temp.txt")
```

`suppress` подавляет указанные исключения. Чище, чем try/except/pass.

---

## 11. assert — это тоже исключение

```python
assert condition, "сообщение"
```

Эквивалент:
```python
if not condition:
    raise AssertionError("сообщение")
```

Особенности:
- **Отключается** флагом `-O`: `python -O script.py`. Поэтому **не используй для пользовательской валидации**.
- Используется для **инвариантов**: «здесь точно должно быть n > 0».
- Основа `pytest` — все тесты на assert.

---

## 12. with и контекстные менеджеры

`with` — это «специализированный try/finally»:
```python
with open("file.txt") as f:
    ...
# всегда: f.close()

# эквивалентно:
f = open("file.txt")
try:
    ...
finally:
    f.close()
```

Контекстные менеджеры обеспечивают **детерминированное освобождение ресурсов** — файлов, lock'ов, соединений с БД, транзакций.

Свой контекстный менеджер:
```python
class Timer:
    def __enter__(self):
        self.start = time.time()
        return self
    def __exit__(self, exc_type, exc_value, tb):
        print(f"took {time.time() - self.start:.2f}s")
        # вернуть True — подавить исключение, False/None — пропустить дальше
        return False

with Timer():
    do_work()
```

---

## 13. Логирование исключений

```python
import logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

try:
    risky()
except Exception as e:
    log.exception("Что-то пошло не так")    # автоматически добавляет traceback
```

`log.exception` (внутри except) — записывает сообщение + полный traceback. Это намного полезнее чем `log.error(str(e))`.

---

## 14. Группы исключений (3.11+)

С Python 3.11 — **ExceptionGroup** для одновременной обработки нескольких:
```python
try:
    raise ExceptionGroup("multi", [
        ValueError("один"),
        TypeError("два"),
    ])
except* ValueError as eg:
    print("словил все ValueError")
except* TypeError as eg:
    print("словил все TypeError")
```

Используется в asyncio.TaskGroup. Подробно — в продвинутом треке.

---

## 15. Типичные ошибки

### Слишком широкий except

```python
try:
    n = int(input())
except:                # ⚠️ ловит ВСЁ, включая KeyboardInterrupt
    print("ошибка")
```

Решение: ловить **конкретный** тип.

```python
try:
    ...
except Exception as e:    # лучше, но всё ещё широко
    ...
```

### except с pass без логирования

```python
try:
    risky()
except Exception:
    pass    # ⚠️ заглатывает все ошибки молча
```

Если правда нужно — хотя бы логируй:
```python
except Exception:
    log.exception("проигнорировано")
```

### Ловить и переподнимать без причины

```python
try:
    risky()
except ValueError as e:
    raise ValueError(str(e))    # ⚠️ потерял оригинальный traceback
```

Решение:
```python
except ValueError:
    raise    # без аргумента — переподнять то же
```

### Использовать assert для пользовательской валидации

```python
def f(age):
    assert age > 0    # ⚠️ выкинется при -O
```

Решение:
```python
def f(age):
    if age <= 0:
        raise ValueError("age должен быть > 0")
```

### Ловить SystemExit / KeyboardInterrupt

```python
try:
    ...
except BaseException:    # ⚠️ Ctrl+C тоже ловится
    ...
```

Не используй BaseException, используй Exception.

### Излишний try/except где достаточно `dict.get`

```python
try:
    val = d["key"]
except KeyError:
    val = "default"

# проще:
val = d.get("key", "default")
```

### finally с return перекрывает исключение

```python
def f():
    try:
        raise ValueError()
    finally:
        return 0    # ⚠️ ValueError проглочена!

f()    # 0, исключения не видно
```

Не возвращай из finally.

---

## 16. Что нужно запомнить

- Исключения — объекты, имеют тип и сообщение.
- `try/except`, опционально `else` (если без ошибки) и `finally` (всегда).
- `except ParentClass` ловит и потомков.
- `Exception` — общий родитель «нормальных» ошибок; `BaseException` — всех включая SystemExit.
- `raise` поднимает; `raise from` связывает с предыдущей причиной.
- Свои исключения — наследоваться от Exception (или собственного базового).
- EAFP в Python предпочтительнее LBYL.
- `with` — обёртка над try/finally.
- Не подавляй ошибки молча; логируй.
- assert — для инвариантов, не для пользовательской валидации.

После исключений у тебя в инструментарии всё для написания **надёжных** программ. Дальше — большая тема: ООП. И в финале начинающего трека — comprehensions/lambda/функциональный стиль.
