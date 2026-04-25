# Многопоточность и многопроцессность — от 0 до 100%

В прошлой теме мы видели asyncio — модель «один поток, много задач». Сейчас — другие модели:
- **threading** — несколько потоков ОС;
- **multiprocessing** — несколько процессов ОС;
- **concurrent.futures** — единый интерфейс к обоим.

Эти инструменты решают разные задачи. Понимание когда что — критично для серьёзной разработки.

---

## 1. Поток vs процесс — теория

### Процесс

- Изолированное адресное пространство.
- Свои переменные, свой Python-интерпретатор.
- Создание дорогое (~50 мс).
- Коммуникация через IPC (pipe, queue, shared memory).
- Падение одного не убивает другие.

### Поток

- Делит адресное пространство процесса.
- Те же переменные доступны всем потокам.
- Создание дешёвое (~1 мс).
- Коммуникация через общую память (но нужны блокировки).
- Падение одного может уронить весь процесс.

В Python: процессы — настоящий параллелизм (свой GIL у каждого), потоки — ограничены GIL (см. тему 19).

---

## 2. threading — основы

```python
import threading
import time

def worker(name):
    print(f"start {name}")
    time.sleep(2)
    print(f"end {name}")

t1 = threading.Thread(target=worker, args=("A",))
t2 = threading.Thread(target=worker, args=("B",))
t1.start()
t2.start()
t1.join()
t2.join()
```

Вывод:
```
start A
start B
end A
end B
```

Оба запустились параллельно (на I/O-bound `sleep` — параллелен).

### Класс Thread

```python
class MyThread(threading.Thread):
    def __init__(self, name):
        super().__init__()
        self.name = name
    def run(self):
        print(f"running {self.name}")

t = MyThread("worker")
t.start()
t.join()
```

### Daemon thread

```python
t = threading.Thread(target=worker, daemon=True)
t.start()
# когда main завершится — daemon-потоки убиваются
```

Полезно для фоновых задач, которые должны умереть с программой.

---

## 3. Синхронизация в threading

### Lock — взаимоисключение

```python
import threading

counter = 0
lock = threading.Lock()

def increment():
    global counter
    for _ in range(100_000):
        with lock:
            counter += 1

threads = [threading.Thread(target=increment) for _ in range(10)]
for t in threads: t.start()
for t in threads: t.join()
print(counter)    # 1_000_000
```

Без lock — было бы меньше из-за race conditions.

### RLock — реентерабельный

```python
lock = threading.RLock()

def f():
    with lock:
        g()      # g тоже захватывает lock — обычный Lock здесь зависнет

def g():
    with lock:
        ...
```

RLock можно захватить несколько раз из одного потока. Освобождается после стольких же `release`.

### Semaphore — ограничение параллельности

```python
sema = threading.Semaphore(3)    # максимум 3 одновременно

def request():
    with sema:
        # только 3 потока могут быть здесь одновременно
        do_work()
```

Полезно для ограничения параллельных I/O (например, не делать больше 5 запросов к API одновременно).

### Event — сигнализация

```python
event = threading.Event()

def waiter():
    event.wait()    # ждать пока установят
    print("go")

def setter():
    time.sleep(2)
    event.set()    # все ждущие проснутся

threading.Thread(target=waiter).start()
threading.Thread(target=setter).start()
```

### Condition — ожидание условия

```python
cond = threading.Condition()
items = []

def producer():
    with cond:
        items.append(1)
        cond.notify()

def consumer():
    with cond:
        cond.wait_for(lambda: items)
        print(items.pop())
```

Чаще проще использовать `queue.Queue`:
```python
import queue

q = queue.Queue()
q.put(item)
item = q.get()    # блокирует пока что-то не появится
q.task_done()
```

Queue — thread-safe, не нужны явные блокировки.

---

## 4. concurrent.futures

Высокоуровневый интерфейс.

### ThreadPoolExecutor

```python
from concurrent.futures import ThreadPoolExecutor

def fetch(url):
    return requests.get(url).text

with ThreadPoolExecutor(max_workers=10) as ex:
    # один за раз:
    future = ex.submit(fetch, "http://...")
    result = future.result()
    
    # пакетно:
    results = list(ex.map(fetch, urls))
    
    # или с as_completed (по мере готовности):
    futures = [ex.submit(fetch, u) for u in urls]
    for f in as_completed(futures):
        print(f.result())
```

### ProcessPoolExecutor

То же самое, но процессы:
```python
from concurrent.futures import ProcessPoolExecutor

def heavy(x):
    return sum(i**2 for i in range(x))

with ProcessPoolExecutor(max_workers=4) as ex:
    results = list(ex.map(heavy, [1_000_000] * 4))
```

В отличие от threading, **реальный параллелизм** на CPU-bound. Но:
- больший overhead на старт;
- аргументы и результаты передаются через pickle;
- функция и её аргументы должны быть picklable.

---

## 5. multiprocessing — низкоуровневый

```python
from multiprocessing import Process, Queue

def worker(q):
    q.put("hello from process")

q = Queue()
p = Process(target=worker, args=(q,))
p.start()
print(q.get())
p.join()
```

### Pool

```python
from multiprocessing import Pool

def square(x):
    return x ** 2

with Pool(4) as p:
    results = p.map(square, range(100))
```

### Связь между процессами

#### Queue
```python
from multiprocessing import Queue
q = Queue()
q.put(item)
q.get()
```

Threadsafe и process-safe.

#### Pipe
```python
from multiprocessing import Pipe
parent, child = Pipe()
# parent.send(...), child.recv()
```

Двухсторонний канал.

#### Shared memory

```python
from multiprocessing import Value, Array

counter = Value("i", 0)        # int
arr = Array("d", [0.0] * 10)    # 10 doubles

def worker():
    with counter.get_lock():
        counter.value += 1
```

`Value` и `Array` — процессы делят их в памяти. Низкоуровневое.

#### Manager — для сложных структур

```python
from multiprocessing import Manager

with Manager() as m:
    d = m.dict()
    l = m.list()
    # эти объекты доступны всем процессам через прокси
```

Намного медленнее обычных dict/list (каждая операция — IPC), но удобно.

#### shared_memory (3.8+)

Низкоуровневый, но эффективный:
```python
from multiprocessing.shared_memory import SharedMemory
import numpy as np

shm = SharedMemory(create=True, size=1024)
arr = np.ndarray((100,), dtype=np.int32, buffer=shm.buf)
arr[:] = range(100)

# в другом процессе:
shm2 = SharedMemory(name=shm.name)
arr2 = np.ndarray((100,), dtype=np.int32, buffer=shm2.buf)
print(arr2[0])    # 0 — те же данные

shm.close()
shm.unlink()
```

Нулевой overhead, идеально для NumPy массивов.

---

## 6. Стратегии запуска процессов

В multiprocessing три способа создания процесса:

### `fork`

Быстрый: копирует память текущего процесса (через copy-on-write). По умолчанию на Linux.

Проблемы:
- может скопировать локально открытые соединения, треды, и т.д. — глюки.
- не работает на macOS с GUI или в asyncio.

### `spawn`

Запускает чистый Python-интерпретатор. По умолчанию на Windows и macOS (3.8+).

Безопасный, но медленнее старт.

### `forkserver`

Нечто среднее. Linux only.

Установка:
```python
import multiprocessing as mp
mp.set_start_method("spawn", force=True)
```

Если код должен работать на macOS — пиши под spawn (всё под `if __name__ == "__main__":`):
```python
def worker(): ...

if __name__ == "__main__":
    with Pool() as p:
        p.map(worker, ...)
```

Без `if __name__ == "__main__"` на spawn будет рекурсивный запуск процессов.

---

## 7. Когда что выбирать

### CPU-bound

- multiprocessing / ProcessPoolExecutor.
- numpy/numba/Cython с GIL release.
- Rust + PyO3.

### I/O-bound, простой

- threading / ThreadPoolExecutor с обычными requests/psycopg2.
- Простой код, всем понятный.

### I/O-bound, тысячи соединений

- asyncio + async-библиотеки (aiohttp, asyncpg).
- Меньше memory overhead, лучше масштабируется.

### Долгоживущий фоновый воркер

- threading с daemon=True.
- Или отдельный процесс через subprocess/multiprocessing.

### Распределение на несколько машин

- Celery, RQ, Dramatiq — распределённые очереди задач.
- Apache Kafka, Redis Streams для потоков.

---

## 8. GIL в реальной жизни

Уже обсуждали в теме 19, но напомню несколько практических вещей:

### NumPy — полезен в threading

```python
import numpy as np
import threading

def heavy():
    a = np.random.rand(10_000_000)
    return (a ** 2).sum()    # numpy без GIL

threads = [threading.Thread(target=heavy) for _ in range(4)]
# реально параллельно
```

### pandas — частично

`pandas` ниже numpy и часто отпускает GIL, но не всегда. Профилируй.

### Hashing/JSON

`hashlib` отпускает GIL для крупных blob. `json.dumps`/`json.loads` — не отпускают.

---

## 9. Race conditions — типичные

### Чтение-модификация-запись

```python
counter = 0

def increment():
    global counter
    counter += 1    # НЕ атомарно
```

В threading — нужен lock.

### Двойная проверка

```python
if cache.get(key) is None:
    cache[key] = compute(key)
    # между check и set другой поток мог уже compute
```

Решение — lock или специализированные кэши:
```python
import functools
@functools.lru_cache(maxsize=128)
def compute(key): ...
```

### Order of execution

```python
result = []
def worker():
    result.append(do_work())

# 10 потоков → result в неопределённом порядке
```

Используй индекс или Queue.

### Атомарные операции (CPython детали)

В CPython `dict[key] = value` для ОДНОЙ пары — атомарно (благодаря GIL). `list.append` — атомарно. Но нельзя на это полагаться.

---

## 10. Deadlock — взаимная блокировка

```python
lock_a = threading.Lock()
lock_b = threading.Lock()

def thread1():
    with lock_a:
        with lock_b:
            ...

def thread2():
    with lock_b:
        with lock_a:
            ...
```

Если thread1 захватил `a` и ждёт `b`, а thread2 захватил `b` и ждёт `a` — deadlock.

Решения:
- **Всегда захватывать локи в одном порядке**.
- Использовать timeout при захвате: `lock.acquire(timeout=5)`.
- Структурированные локи (контекстные менеджеры).
- Минимизировать длительность захвата.

---

## 11. Прерывание потоков

В Python **нельзя нормально остановить поток извне**:
```python
t = threading.Thread(target=worker)
t.start()
# t.terminate()   нет такого
# t.kill()        нет такого
```

Нужно делать **кооперативно** — через флаг:
```python
stop_event = threading.Event()

def worker():
    while not stop_event.is_set():
        do_chunk()
        time.sleep(0.1)

stop_event.set()    # сообщить «остановись»
```

Процессы можно убивать:
```python
p.terminate()
p.kill()       # SIGKILL
```

---

## 12. ThreadLocal — потоково-локальные данные

```python
import threading

local = threading.local()

def worker():
    local.x = threading.get_ident()
    # local.x уникален в каждом потоке

# каждый поток имеет своё local.x
```

Полезно для:
- сессий БД (каждый поток — своя сессия);
- логирование с контекстом потока;
- параметров запроса в веб-сервере.

---

## 13. subprocess — внешние процессы

Не путай с multiprocessing — это про запуск **внешних** программ:
```python
import subprocess

result = subprocess.run(["ls", "-la"], capture_output=True, text=True)
print(result.stdout)
print(result.returncode)

# с pipe:
ls = subprocess.Popen(["ls"], stdout=subprocess.PIPE)
grep = subprocess.Popen(["grep", "py"], stdin=ls.stdout, stdout=subprocess.PIPE)
ls.stdout.close()
out, _ = grep.communicate()
```

Использует ОС-ные процессы. Полезно для:
- запуска CLI-утилит из Python;
- интеграции с другими языками;
- параллельной работы независимых задач.

---

## 14. Профилирование параллельного кода

### Простое замерение

```python
import time
t0 = time.perf_counter()
do_work()
print(time.perf_counter() - t0)
```

### Контекстный менеджер

```python
import time
from contextlib import contextmanager

@contextmanager
def timer(name):
    t0 = time.perf_counter()
    yield
    print(f"{name}: {time.perf_counter() - t0:.3f}s")

with timer("download"):
    fetch_all()
```

### threading-aware профайлер

`yappi` (yet another python profiler) — поддерживает многопоточность правильно. `cProfile` тоже работает, но даёт время одного потока.

`py-spy` — sampling-профайлер, работает на запущенном процессе:
```bash
py-spy top --pid <pid>
py-spy record -o profile.svg --pid <pid>
```

Не требует изменения кода. Идеален для проды.

---

## 15. Реальные паттерны

### Producer-consumer

```python
from queue import Queue
import threading

q = Queue(maxsize=100)

def producer():
    for item in source:
        q.put(item)
    q.put(None)    # сигнал «конец»

def consumer():
    while True:
        item = q.get()
        if item is None:
            q.put(None)    # передать дальше другим consumer-ам
            break
        process(item)

threading.Thread(target=producer).start()
for _ in range(4):
    threading.Thread(target=consumer).start()
```

### Worker pool с rate limit

```python
sema = threading.Semaphore(5)    # максимум 5 параллельных

def worker(item):
    with sema:
        process(item)

with ThreadPoolExecutor(max_workers=20) as ex:
    ex.map(worker, items)
```

20 потоков, но в каждый момент только 5 в работе.

### Map-reduce

```python
from concurrent.futures import ProcessPoolExecutor

def map_step(chunk):
    return [process(x) for x in chunk]

def reduce_step(results):
    return sum(results, [])

chunks = [data[i:i+100] for i in range(0, len(data), 100)]
with ProcessPoolExecutor() as ex:
    mapped = list(ex.map(map_step, chunks))
final = reduce_step(mapped)
```

---

## 16. Типичные ошибки

### Передача больших данных в multiprocessing

```python
big_data = [...]    # 1 ГБ

with Pool() as p:
    p.map(process, big_data)    # ⚠️ pickle копирует на каждый воркер
```

Решения: shared_memory, mmap, или меньшие чанки.

### Forgot `if __name__ == "__main__":`

```python
# на Windows/macOS spawn — без guard будет рекурсивный запуск
from multiprocessing import Pool

def f(x): return x*2

# плохо:
with Pool() as p: p.map(f, range(10))    # FATAL

# хорошо:
if __name__ == "__main__":
    with Pool() as p:
        print(p.map(f, range(10)))
```

### lambda в multiprocessing

```python
with Pool() as p:
    p.map(lambda x: x*2, range(10))    # ⚠️ pickle не умеет lambda
```

Используй обычные функции (или `cloudpickle` если очень нужно).

### Слишком много потоков

```python
threads = [threading.Thread(target=fetch) for _ in range(10_000)]    # ⚠️
```

10к потоков — это 80 ГБ памяти на стеки. Используй пул или asyncio.

### Игнорирование исключений в потоках

```python
def worker():
    raise ValueError    # просто исчезнет, никто не узнает

t = threading.Thread(target=worker)
t.start()
t.join()    # никаких признаков ошибки
```

В `concurrent.futures` исключения сохраняются в Future:
```python
fut = ex.submit(worker)
fut.result()    # перевыбросит ValueError
```

---

## 17. Что нужно запомнить

- threading: дешёвые потоки, делят память, GIL ограничивает CPU-bound.
- multiprocessing: настоящий параллелизм, дорогая коммуникация через pickle.
- concurrent.futures: единый API, рекомендуемый для большинства случаев.
- I/O-bound → threading или asyncio. CPU-bound → multiprocessing.
- Синхронизация: Lock, RLock, Semaphore, Event, Queue.
- Race condition есть в threading, deadlock возможен — будь аккуратен.
- multiprocessing на macOS/Windows — spawn, нужен `if __name__ == "__main__":`.
- Поток нельзя убить — нужен флаг отмены.
- subprocess — для запуска внешних программ.
- Для проды — py-spy для профилирования.

После concurrency осталось 4 темы: типизация, продвинутые декораторы, тестирование, профилирование. Близко к финалу.
