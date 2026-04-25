# Производительность и профилирование — от 0 до 100%

Финальная тема курса. После всех 27 предыдущих — ты знаешь язык на уровне «понимаю, как работает». Теперь — как **быстро работает**, и что делать, когда не быстро.

Профайлинг — это **измерение**, оптимизация — **изменение**. Главное правило: **«сначала измерь, потом оптимизируй»**. Без профилирования любая оптимизация — гадание. С — точечная работа.

В этой теме — все основные инструменты, паттерны, антипаттерны, и пара слов про NumPy/Cython/Rust для случаев, когда чистый Python всё-таки слишком медленный.

---

## 1. Закон Кнута

> «Преждевременная оптимизация — корень всех зол.»  
> — Дональд Кнут

В контексте: 97% кода не нужно оптимизировать. Сложный код ради скорости — это техдолг. Оптимизируй только когда **измерил** медленное место и **доказал**, что его нужно ускорять.

**80/20 правило**: обычно 80% времени тратится в 20% кода. Найди эти 20% — и сосредоточься.

---

## 2. timeit — простое измерение

Для маленьких куски:
```python
import timeit

# простое:
timeit.timeit("[i*2 for i in range(1000)]", number=10000)
# 0.85 секунд за 10к итераций

# с setup:
timeit.timeit("sorted(data)", setup="data = [3, 1, 4, 1, 5]", number=100000)

# через CLI:
# python -m timeit "[i*2 for i in range(1000)]"
```

В Jupyter:
```python
%timeit [i*2 for i in range(1000)]
# 60 µs ± 3 µs per loop
```

`%timeit` автоматически выбирает количество запусков. Удобно для эксперимента.

### Сравнение вариантов

```python
import timeit

t1 = timeit.timeit("[i*2 for i in range(100)]", number=100000)
t2 = timeit.timeit("list(map(lambda x: x*2, range(100)))", number=100000)
t3 = timeit.timeit("res=[]\nfor i in range(100): res.append(i*2)", number=100000)
print(t1, t2, t3)
# 0.5  1.2  0.8
```

Comprehension быстрее `map(lambda)`, оба быстрее цикла с append.

---

## 3. cProfile — профайлинг функций

Для целой программы:
```python
import cProfile
import pstats

cProfile.run("main()", "profile.out")

stats = pstats.Stats("profile.out")
stats.sort_stats("cumulative")
stats.print_stats(20)    # топ 20 функций
```

Через CLI:
```bash
python -m cProfile -o profile.out script.py
python -m pstats profile.out
```

Вывод:
```
ncalls  tottime  percall  cumtime  percall filename:lineno(function)
   1000    0.500    0.001    0.500    0.001 mymodule.py:42(slow_func)
   ...
```

- `ncalls` — сколько раз вызвана.
- `tottime` — суммарное время **внутри** функции (без вложенных вызовов).
- `cumtime` — суммарное время **с** вложенными вызовами.
- `percall` — на один вызов.

### Что искать

- Функции с большим **cumtime** — где общая задержка.
- Функции с большим **tottime** — где «горячий» код.
- Большое `ncalls` — может, лишние вызовы (нет кэша, неэффективный цикл).

### snakeviz — визуализация

```bash
pip install snakeviz
snakeviz profile.out
```

Открывает интерактивный граф в браузере.

---

## 4. line_profiler — построчный

cProfile показывает per-function. Часто хочется per-line:
```bash
pip install line_profiler
```

```python
@profile    # декоратор от line_profiler (без import)
def slow():
    a = [i for i in range(1_000_000)]
    b = sum(a)
    c = [x**2 for x in a]
    return c
```

```bash
kernprof -l -v script.py
```

Вывод:
```
Line #      Hits         Time  Per Hit   Time%   Line Contents
==========================================================
     1                                           @profile
     2                                           def slow():
     3         1     46000.0  46000.0    35.5      a = [i for i in range(1_000_000)]
     4         1     12000.0  12000.0     9.3      b = sum(a)
     5         1     71000.0  71000.0    55.0      c = [x**2 for x in a]
     6         1         0.0      0.0     0.0      return c
```

55% времени в третьей строке — там и оптимизируй.

---

## 5. py-spy — sampling в проде

cProfile добавляет overhead. py-spy — sampling-профайлер, **не модифицирует** код:

```bash
pip install py-spy

# топ-функции живого процесса:
py-spy top --pid <PID>

# запись flame graph:
py-spy record -o profile.svg --pid <PID> --duration 30
```

Идеально для:
- проды;
- зависших процессов;
- демонов.

py-spy показывает что именно делает программа в момент проблемы.

---

## 6. memory_profiler — память построчно

```bash
pip install memory_profiler
```

```python
@profile
def func():
    a = [0] * 1_000_000      # ~7.6 MB
    b = [0] * 9_000_000      # ~68 MB
    return sum(b)
```

```bash
python -m memory_profiler script.py
```

Вывод:
```
Line #    Mem usage    Increment  Line Contents
================================================
     1     30.0 MiB     30.0 MiB   @profile
     2                             def func():
     3     37.6 MiB      7.6 MiB       a = [0] * 1_000_000
     4    105.6 MiB     68.0 MiB       b = [0] * 9_000_000
```

---

## 7. tracemalloc — встроенный

```python
import tracemalloc

tracemalloc.start()

# ... код

snapshot = tracemalloc.take_snapshot()
top = snapshot.statistics("lineno")
for stat in top[:10]:
    print(stat)
```

Не требует библиотек. Хорошо для диагностики утечек памяти.

---

## 8. Базовые оптимизации

### 1. Используй встроенные

`sum`, `max`, `min`, `sorted` — на C, быстрее любого pure-Python:
```python
# плохо:
total = 0
for x in data:
    total += x

# хорошо:
total = sum(data)
```

### 2. Comprehensions быстрее loop+append

```python
# медленнее:
result = []
for x in data:
    result.append(x*2)

# быстрее:
result = [x*2 for x in data]
```

### 3. Локальные переменные быстрее глобальных

```python
def slow():
    for _ in range(1_000_000):
        math.sqrt(2)    # каждый раз ищет math, потом sqrt

def fast():
    sqrt = math.sqrt    # сделали локальной
    for _ in range(1_000_000):
        sqrt(2)         # быстрее на ~20%
```

В CPython локальные доступаются через массив, глобальные — через dict.

### 4. set/dict для membership

```python
# O(n):
if x in some_list: ...

# O(1):
if x in some_set: ...
```

Для больших коллекций — set/dict в десятки раз быстрее list.

### 5. Не вычисляй то, что можно закэшировать

```python
@functools.cache    # или lru_cache
def expensive(x):
    return slow_calc(x)
```

### 6. Generator expression вместо list comprehension для агрегаций

```python
# не нужен список — генератор быстрее:
total = sum(x*2 for x in data)

# плохо:
total = sum([x*2 for x in data])
```

### 7. Joining строк

```python
# плохо — O(n²):
s = ""
for piece in pieces:
    s += piece

# хорошо — O(n):
s = "".join(pieces)
```

### 8. Slot для миллионов объектов

```python
class Point:
    __slots__ = ("x", "y")
```

См. тему 20.

---

## 9. Структуры данных и их сложность

| Операция | list | dict | set | deque |
|---|---|---|---|---|
| Доступ по индексу | O(1) | — | — | O(n) |
| Доступ по ключу | — | O(1) | — | — |
| Поиск (in) | O(n) | O(1) | O(1) | O(n) |
| append | O(1) am | — | — | O(1) |
| insert(0) | O(n) | — | — | O(1) |
| pop() | O(1) | — | — | O(1) |
| pop(0) | O(n) | — | — | O(1) |
| sort | O(n log n) | — | — | — |

Выбирай структуру под задачу:
- Стек/конец — list.
- Очередь — `collections.deque` (не list!).
- Уникальные элементы / membership — set.
- Сопоставление — dict.
- LRU — `OrderedDict` или `functools.lru_cache`.

---

## 10. NumPy — для числовых массивов

`for x in array: x*2` в pure Python — медленно. `array * 2` в NumPy — быстро (вектор):
```python
import numpy as np

a = np.arange(1_000_000)

# pure Python: ~50 ms
result = [x * 2 for x in a]

# numpy: ~1 ms
result = a * 2
```

50× быстрее. Причины:
- NumPy хранит данные в плотном C-массиве (нет Python-объектов).
- Операции реализованы в SIMD-оптимизированном C.
- GIL отпущен — можно параллелить.

NumPy — стандарт для:
- линейной алгебры (matmul, eigen);
- статистики;
- ML/data science.

Если у тебя горячий цикл с числами — переписать на NumPy ≈ один из лучших вариантов.

---

## 11. numba — JIT для NumPy-кода

```python
from numba import jit

@jit(nopython=True)
def slow_sum(arr):
    total = 0
    for x in arr:
        total += x
    return total

slow_sum(np.arange(1_000_000))    # на первом запуске JIT-компилируется
slow_sum(np.arange(1_000_000))    # на втором — быстро как C
```

Добавил декоратор → numba компилирует в нативный код. Поддерживает многие NumPy функции.

`@jit(parallel=True)` — параллелизм на нескольких ядрах.
`@jit(nopython=True, fastmath=True)` — агрессивные оптимизации.

---

## 12. Cython — Python с типами в C

```cython
# my.pyx
def slow_sum(int[:] arr):
    cdef int total = 0
    cdef int i
    for i in range(arr.shape[0]):
        total += arr[i]
    return total
```

Компиляция:
```bash
cythonize -i my.pyx
```

Генерирует `.so`, импортируешь как обычный модуль. С `cdef` типами — работает почти как C.

Используется в SciPy, scikit-learn, pandas (часть).

---

## 13. C-extensions и Rust

### CFFI / ctypes

Связь с готовой C-библиотекой:
```python
from ctypes import CDLL, c_int
lib = CDLL("./mylib.so")
lib.add(c_int(1), c_int(2))
```

### PyO3 (Rust)

```rust
use pyo3::prelude::*;

#[pyfunction]
fn fast_sum(data: Vec<i64>) -> i64 {
    data.iter().sum()
}
```

Скомпилируется в Python-модуль. Современный способ писать критические части.

Используется в `polars`, `pydantic-core`, `cryptography`, `tokenizers`.

---

## 14. asyncio для I/O

См. тему 23. Если задача I/O-bound (сеть, диск) — asyncio даёт огромный выигрыш без оптимизации pure-CPU кода.

---

## 15. multiprocessing для CPU

См. тему 24. Если задача CPU-bound и не помещается в одно ядро — Pool processes.

---

## 16. Кэширование на уровне приложения

### functools

```python
@functools.cache
def expensive(x): ...

@functools.lru_cache(maxsize=1000)
def cached(x): ...
```

### Внешние кэши

- **Redis** — для шарящегося кэша между процессами/серверами.
- **Memcached** — простой high-performance кэш.

---

## 17. Алгоритмы и сложность

Прежде чем оптимизировать в Python — посмотри на алгоритм. Замена O(n²) на O(n log n) или O(n) даёт **порядки** ускорения, что недостижимо никакими микрооптимизациями.

```python
# O(n²) — медленно для n=10000:
def has_duplicates(items):
    for i, a in enumerate(items):
        for b in items[i+1:]:
            if a == b:
                return True
    return False

# O(n) — быстро:
def has_duplicates(items):
    return len(items) != len(set(items))
```

```python
# O(n*m):
common = [x for x in a if x in b]    # b — list

# O(n+m):
b_set = set(b)
common = [x for x in a if x in b_set]
```

---

## 18. Профилирование процесса в проде

### py-spy attach

```bash
py-spy top --pid <PID>
```

Без перезапуска, минимальный overhead.

### Logging уровня INFO

Логи + время:
```python
log.info("Started query")
result = db.query(...)
log.info(f"Query took {time.time() - t0:.2f}s")
```

В сложных проектах — distributed tracing (OpenTelemetry, Datadog APM, New Relic).

### Метрики

Prometheus + Grafana — стандарт для метрик «сколько RPS, p99 latency, ...».

```python
from prometheus_client import Counter, Histogram
requests = Counter("requests_total", "Total requests")
latency = Histogram("request_duration_seconds", "Request latency")

@latency.time()
def handle_request():
    requests.inc()
    ...
```

---

## 19. Чек-лист оптимизации

Когда программа медленная:

1. **Воспроизвести**. Уменьшай ввод до минимального воспроизводящего.
2. **Профилировать**. cProfile / line_profiler / py-spy.
3. **Найти hot path**. 80% времени где?
4. **Понять что делает код**. Алгоритм правильный? Сложность ОК?
5. **Гипотезы**:
   - можно использовать встроенное (sum, max)?
   - есть лишние циклы / дубликаты вызовов?
   - подходящая структура данных?
   - можно закэшировать?
   - можно векторизовать (NumPy)?
6. **Применить одно изменение**. Замерить.
7. **Если мало — переходим к C/Cython/Rust**.
8. **Если очень много I/O — asyncio**.
9. **Если CPU-bound и можно параллелить — multiprocessing**.

---

## 20. Типичные ошибки

### Оптимизировать без замера

```python
# подозреваешь что dict медленнее list по памяти, переписал
```

И стало хуже. Без замера не знаешь.

### Микрооптимизации без выгоды

```python
# i = i + 1 vs i += 1 vs i = i.__add__(1)
```

Разница миллисекунды, код стал хуже. Не делай.

### Premature parallelization

Distrubuted, multiprocessing — добавляет сложность. Не лезь до тех пор, пока profiling не покажет, что нужно.

### Игнорирование алгоритма

```python
# делаешь O(n²) с Cython
# можно было сделать O(n log n) на чистом Python
```

Алгоритм важнее реализации.

### Кэш без TTL

```python
@cache
def get_user(id): ...
```

Кэш растёт неограниченно. После часа — сотни МБ. Используй `lru_cache(maxsize=...)`.

### Переиспользование объектов «для скорости»

```python
shared = []
def process():
    shared.clear()    # ⚠️ опасно если есть параллельность
```

Преждевременная микрооптимизация. Создавай новые объекты — обычно дешевле тестирования багов с shared state.

---

## 21. Что нужно запомнить

- Сначала измерь, потом оптимизируй (правило Кнута).
- timeit — для микро-замеров.
- cProfile — для функций.
- line_profiler — для строк.
- py-spy — для проды и зависших процессов.
- memory_profiler / tracemalloc — для памяти.
- Алгоритм важнее реализации; меняй O(n²) на O(n log n).
- Используй встроенные (sum, max, sorted).
- Comprehension быстрее loop+append.
- set/dict для membership — O(1) vs O(n).
- NumPy для числовых массивов; numba/Cython для горячих циклов.
- functools.cache для memoization.
- asyncio для I/O-bound; multiprocessing для CPU-bound.
- Не оптимизируй то, что не профилировал.

---

## Финал

Поздравляю. Ты прошёл **все 28 тем** курса. Что у тебя теперь есть:

- Полный обзор синтаксиса и структур данных Python.
- Понимание модели памяти, GIL, byte-кода.
- Знание ООП на уровне дескрипторов и метаклассов.
- Asyncio, threading, multiprocessing — умеешь выбирать.
- Современная типизация — на уровне production.
- Декораторы — продвинутые паттерны.
- Тестирование — pytest, mock, hypothesis.
- Профилирование — измерять, диагностировать, оптимизировать.

Это база уровня **«крепкий middle / приближается к senior»** по Python. Дальше — **практика**:

1. Сделай 3-5 своих проектов:
   - Telegram-бот с webhook и БД.
   - Web-API на FastAPI с тестами.
   - CLI-утилита с click.
   - Парсер сайта с asyncio.
   - Игра «змейка» с pygame.

2. Открой опенсорс-проект на GitHub и **пройди его насквозь**. Прочитай каждый модуль. Запусти тесты. Сделай маленький contrib.

3. Решай задачи на LeetCode / Codeforces — алгоритмы и структуры данных.

4. Читай PEP'ы — особенно про новые фичи (PEP 8, 484, 695, 703).

5. Подпишись на Real Python, Talk Python To Me podcast.

Удачи. Python — глубокий язык, и ты сделал серьёзный шаг по нему.
