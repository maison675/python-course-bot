# GIL — от 0 до 100%

GIL (Global Interpreter Lock) — самая обсуждаемая особенность CPython. Каждый питонист рано или поздно сталкивается с ним: «Я запустил threading на 8 потоков, а оно работает медленнее одного!». Это не ошибка кода — это GIL.

В этой теме мы разберём:
- что такое GIL и зачем он есть;
- когда он мешает, а когда нет;
- как обходить (multiprocessing, asyncio, Cython, GIL-free);
- что происходит сейчас (Python 3.13+ no-GIL);
- какие альтернативы.

После этого ты сможешь обоснованно выбирать между threading, multiprocessing и asyncio.

---

## 1. Что такое GIL

GIL — это **мьютекс** (взаимоисключающая блокировка) внутри CPython. Он гарантирует, что **только один поток может выполнять Python байткод одновременно**.

Простыми словами: даже если у тебя 8 ядер и 8 потоков — только один из них в каждый момент времени делает «питонью работу». Остальные ждут.

```python
import threading

def cpu_bound():
    total = 0
    for i in range(100_000_000):
        total += i

# Один поток:
t = threading.Thread(target=cpu_bound)
t.start(); t.join()    # ~5 сек

# Два потока — тот же объём работы вдвоём:
t1 = threading.Thread(target=cpu_bound)
t2 = threading.Thread(target=cpu_bound)
t1.start(); t2.start()
t1.join(); t2.join()    # ~10 сек, не 5! GIL.
```

Два потока **не быстрее**, иногда **медленнее** из-за оверхеда переключения.

---

## 2. Зачем GIL существует

Без GIL CPython был бы **thread-unsafe**. Объясню.

Каждое присваивание `a = b` в CPython делает примерно:
```c
Py_DECREF(old_a);    // уменьшить refcount старого
old_a = b;
Py_INCREF(b);        // увеличить refcount нового
```

Refcount — это просто int. **Атомарно ли его увеличение**?

В современных CPU `int += 1` это:
1. Загрузить значение в регистр.
2. Прибавить 1.
3. Записать обратно.

Если два потока делают это одновременно без блокировки — могут потерять обновление. Refcount «портится». Объект освободится слишком рано (use-after-free) или не освободится никогда (утечка).

**GIL решает это просто**: только один поток выполняет байткод, поэтому никто не лезет в refcount параллельно. Это сделало CPython **простым, быстрым в однопоточном режиме, и переносимым**.

Альтернативы (atomic refcount, fine-grained locks) — существенно сложнее и часто медленнее в обычном случае. Поэтому GIL продержался ~30 лет.

---

## 3. Когда GIL мешает, когда нет

### Мешает: CPU-bound задачи

Любая чистая «питонья» работа: вычисления, парсинг, обработка данных в pure Python.
```python
def heavy(data):
    return sum(x ** 2 for x in data)
```
threading здесь **не ускорит** ничего.

### Не мешает: I/O-bound задачи

GIL **отпускается** во время системных вызовов (read, write, recv, sleep). Поэтому пока один поток ждёт сеть, другой работает.
```python
import requests, threading

def download(url):
    requests.get(url)    # GIL отпущен на recv

threads = [threading.Thread(target=download, args=(url,)) for url in urls]
for t in threads: t.start()
for t in threads: t.join()
```
**Это работает параллельно**: 100 запросов идут одновременно. threading здесь полезен.

### Не мешает: C-extensions

Если C-код объявляет «без GIL» — он работает **параллельно**. NumPy, например, в большинстве операций отпускает GIL:
```python
import numpy as np
import threading

def heavy():
    a = np.random.rand(10_000_000)
    b = a * a + a    # внутри NumPy без GIL → параллельно
```
Несколько потоков с numpy.matmul ускорятся. Это и есть «правильный путь» — хочешь скорости, делай в C-расширении.

### Не мешает: subinterpreters / multiprocessing

Каждый процесс имеет **свой** GIL. Поэтому параллелизм возможен через процессы.

---

## 4. Как именно работает GIL

GIL — это специальный объект внутри `_PyRuntime`. Он защищает **состояние интерпретатора**: `sys.modules`, refcount-ы, GC, и многое другое.

Поток, чтобы выполнять Python код, должен **захватить GIL**:
```c
PyEval_AcquireThread();
// ... выполняем байткод
PyEval_ReleaseThread();
```

### Когда GIL отпускается

1. **Регулярно** — каждые ~100 байткод-инструкций (или каждые ~5 мс в современных версиях). Поток отдаёт GIL → другой поток может схватить.
2. **На I/O** — когда поток заходит в `read()`, `write()`, `socket.recv()`, `time.sleep()`, и подобные блокирующие сисколлы.
3. **На C-уровне** — расширение может явно отпустить GIL через `Py_BEGIN_ALLOW_THREADS`/`Py_END_ALLOW_THREADS`.

### Когда удерживается

- Чистые арифметические операции в Python.
- Манипуляции со списками, словарями.
- В общем — любая инструкция байткода, не выходящая в C-extension/syscall.

---

## 5. Эксперимент: видим GIL на цифрах

```python
import time
import threading

N = 50_000_000

def work():
    x = 0
    for i in range(N):
        x += 1

# 1 поток:
t0 = time.time()
work()
print(f"1 поток: {time.time() - t0:.2f}s")

# 4 потока:
t0 = time.time()
threads = [threading.Thread(target=work) for _ in range(4)]
for t in threads: t.start()
for t in threads: t.join()
print(f"4 потока: {time.time() - t0:.2f}s")
```

Типичный результат:
```
1 поток: 3.5s
4 потока: 14.5s    # ❗
```

Четыре потока медленнее одного **в 4 раза** — потому что они делают в 4 раза больше работы, но не параллельно (GIL).

Замени `for i in range(N): x += 1` на `time.sleep(2)` — увидишь, что с I/O 4 потока работают за ~2 сек, не 8.

---

## 6. multiprocessing — обход GIL

Вместо потоков — **процессы**. У каждого свой Python-интерпретатор и свой GIL → реальный параллелизм:

```python
from multiprocessing import Pool

def square(x):
    return x ** 2

with Pool(4) as p:
    results = p.map(square, range(1000))
```

### Плюсы
- настоящий параллелизм на много ядер;
- изоляция процессов: краш одного не убивает других;
- независимая память.

### Минусы
- **дорого передавать данные** между процессами — pickle сериализация;
- больше памяти (каждый процесс — копия Python);
- сложнее отлаживать;
- не все объекты picklable (lambda, локальные функции).

### concurrent.futures

Чаще удобнее использовать `concurrent.futures` — единый API для потоков и процессов:
```python
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

with ProcessPoolExecutor(max_workers=4) as ex:
    results = list(ex.map(heavy, data))

with ThreadPoolExecutor(max_workers=10) as ex:
    results = list(ex.map(download, urls))
```

Простое правило:
- **CPU-bound** → ProcessPoolExecutor (или multiprocessing.Pool).
- **I/O-bound** → ThreadPoolExecutor (или asyncio).

---

## 7. asyncio — другой подход к параллелизму

Подробно — в теме 23. Кратко:

asyncio = **один поток + кооперативный многозадачный режим**. Никакого параллелизма CPU, только I/O. Но эффективнее threading для тысяч одновременных I/O.

```python
import asyncio
import aiohttp

async def fetch(session, url):
    async with session.get(url) as resp:
        return await resp.text()

async def main(urls):
    async with aiohttp.ClientSession() as session:
        return await asyncio.gather(*[fetch(session, u) for u in urls])

asyncio.run(main(urls))
```

asyncio — современный способ для **высоконагруженных I/O** в Python. Telegram-боты, веб-сервисы, скрейперы — всё на asyncio.

GIL не мешает asyncio (всё в одном потоке всё равно).

---

## 8. Когда threading вообще полезен

Несмотря на GIL, threading есть смысл использовать когда:

### 1. I/O-bound и не хочешь asyncio

Простой синхронный код с `requests`, `urllib3`, `psycopg2` — пусти в потоках:
```python
from concurrent.futures import ThreadPoolExecutor
with ThreadPoolExecutor(max_workers=20) as ex:
    results = list(ex.map(download, urls))
```

### 2. Параллельный C-extensions

NumPy, OpenCV, многие крипто-библиотеки отпускают GIL. Threading работает.

### 3. Удобство

Иногда threading проще asyncio для простых задач (background timer, простая отладочная утилита).

### 4. tkinter/Qt GUI

GUI часто требует отдельного потока для долгих задач, чтобы не блокировать UI.

---

## 9. Atomic operations vs GIL

Многие думают: «раз есть GIL, значит всё атомарно». **Это не так**.

```python
counter = 0

def increment():
    global counter
    for _ in range(1_000_000):
        counter += 1    # НЕ АТОМАРНО

# ...два потока, ожидаем 2_000_000, получим обычно 2_000_000 благодаря 100ms тиков
# но это не гарантировано
```

`counter += 1` — это:
1. LOAD_FAST counter
2. LOAD_CONST 1
3. BINARY_OP +
4. STORE_FAST counter

Между шагами GIL может перекинуться на другой поток.

### Что атомарно (точно)

- Одна инструкция байткода.
- `dict[key] = value` для одной ключ-пары.
- `list.append`, `list.pop`.
- `queue.Queue.put`/`.get`.
- `threading.Lock`.

### Что не атомарно

- `counter += 1`.
- `if x in d: d[x] += 1` (гонка между in и обновлением).
- Сложные выражения.

Для синхронизации — используй `threading.Lock`, `threading.RLock`, `threading.Semaphore`, или `queue.Queue`.

```python
import threading

lock = threading.Lock()
counter = 0

def increment():
    global counter
    for _ in range(1_000_000):
        with lock:
            counter += 1
```

Или используй атомарные структуры вроде `multiprocessing.Value` или `concurrent.futures` с правильной синхронизацией.

---

## 10. Cython с `nogil`

Cython — это «Python + C типы». Можно отметить функцию `nogil`:
```cython
def heavy(double[:] data) nogil:
    cdef double total = 0
    cdef int i
    for i in range(data.shape[0]):
        total += data[i] * data[i]
    return total
```

Внутри `nogil` блока поток **не держит** GIL. Несколько потоков выполняют такие функции **параллельно**.

То же самое в C-extensions — макрос `Py_BEGIN_ALLOW_THREADS`.

NumPy, scikit-learn, многие другие библиотеки используют этот трюк, чтобы давать параллельность поверх Python API.

---

## 11. Python 3.13 — экспериментальный no-GIL

С Python 3.13 появилась **опция компиляции без GIL** (PEP 703). Сборка `python --without-gil` (или `python3.13t` в дистрибутивах):

- Каждый объект имеет свой mutex для refcount.
- Используется biased reference counting (быстро в horizonal-thread-private случае).
- Используется immortal objects для глобальных констант.

Сейчас это **экспериментально**. На 2024-2025 год:
- работает корректно для большинства pure-python кода;
- многие C-extensions (особенно крупные NumPy, Pillow) уже совместимы;
- ~10-20% медленнее в однопоточном режиме (плата за thread-safety);
- даёт **настоящий** параллелизм для CPU-bound в потоках.

Когда стандартизуется (план — 3.15+, через несколько лет) — threading в Python станет реально параллельным.

Но **ещё годы** GIL будет нормой. Учись жить с ним.

---

## 12. Sub-interpreters (PEP 684, 3.12+)

Альтернативный путь: каждый sub-interpreter имеет **свой** GIL. Можно запустить несколько sub-interpreters в одном процессе и они выполняются параллельно.

```python
import _xxsubinterpreters as interpreters    # экспериментально

interp = interpreters.create()
interpreters.run_string(interp, "x = 42")
```

Плюсы перед multiprocessing:
- меньше overhead — не отдельный процесс;
- быстрее старт.

Минусы:
- API ещё нестабильное;
- объекты не делятся между sub-interpreters (как и в multiprocessing).

В 3.13 появился публичный API. В 3.14+ — будет полноценно интегрировано.

---

## 13. Где GIL уже **не** живёт

В мире Python есть:
- **Jython** — нет GIL (использует JVM lock-free структуры).
- **IronPython** — нет GIL (.NET).
- **PyPy** — есть, но эффективнее (STM экспериментировали).
- **MicroPython** — обычно single-threaded.

Только CPython реально страдает от GIL — но именно его все используют.

---

## 14. Как принимать решения

### CPU-bound (вычисления)

- Сначала: можно ли использовать NumPy/Numba? Они часто отпускают GIL.
- Если pure Python обязательно — `multiprocessing` или `concurrent.futures.ProcessPoolExecutor`.
- Если можешь скомпилировать — Cython с `nogil`, или Rust + PyO3.

### I/O-bound (сеть, диск)

- Современный стек — `asyncio` (aiohttp, asyncpg, ...).
- Старый стек — `threading` + `concurrent.futures.ThreadPoolExecutor`.
- Тысячи одновременных соединений — только asyncio.

### Mixed

- I/O в asyncio, CPU части в `loop.run_in_executor(ProcessPoolExecutor(), ...)`.
- Или Celery / RQ для heavy CPU jobs в фоне.

### High-perf

- Векторизация (numpy).
- C-extensions с `nogil`.
- Rust + PyO3.
- Жди стабилизации no-GIL Python 3.13+.

---

## 15. Типичные заблуждения

### «GIL = Python — single-threaded»

Нет. Питон **может** запускать несколько потоков, GIL просто не даёт им параллельно выполнять байткод. I/O и С-extensions параллельны.

### «threading в Python бесполезен»

Нет. Для I/O-bound — отлично работает. Для C-extensions с nogil — работает.

### «Чтобы стало быстрее, добавь поток»

Нет. Добавление потоков к CPU-bound коду в pure Python — **замедлит** программу.

### «multiprocessing просто параллелизует магически»

Не магически. Серьёзный overhead на сериализацию данных, и нужно проектировать под него.

### «asyncio быстрее threading»

Не «быстрее», а **другой**. Для I/O — да, эффективнее тысяч соединений. Для CPU — никак, всё в одном потоке.

### «GIL скоро уберут»

Скоро? — 3-5 лет минимум. Уже опция в 3.13, но дефолтом станет позже.

---

## 16. Что нужно запомнить

- GIL = «только один поток в байткоде Python в момент времени».
- Не мешает: I/O, C-extensions с nogil, multiprocessing, sub-interpreters.
- Мешает: pure-Python CPU-bound в потоках.
- Регулярно отпускается (~5 мс) и на блокирующих сисколлах.
- threading годится для I/O-bound. multiprocessing — для CPU-bound. asyncio — для тысяч I/O соединений.
- Атомарность отдельных инструкций ≠ атомарность выражений вроде `x += 1`.
- `threading.Lock` для синхронизации.
- Cython + `nogil`, Rust+PyO3 для производительных C-расширений.
- Python 3.13+ экспериментально без GIL — будущее, но не сейчас.

После GIL — следующий уровень внутренностей: дескрипторы и `__slots__`. Это то, на чём построены `@property`, ORM, валидаторы.
