# Корутины и asyncio — от 0 до 100%

asyncio — современный способ писать **высоконагруженные I/O** программы на Python. Веб-серверы (FastAPI, aiohttp), Telegram-боты (aiogram, python-telegram-bot), скрейперы, потоковые системы — всё на asyncio. Если ты планируешь работать в backend — это must-have.

asyncio — это **другой стиль мышления**. Не «делай это, потом то», а «начни эти 100 задач, реагируй когда любая закончится». Будем разбираться по шагам.

---

## 1. Зачем нужно

Возьмём задачу: скачать 100 веб-страниц.

### Синхронно

```python
import requests
import time

t0 = time.time()
for url in urls:
    requests.get(url)    # каждый занимает ~500 мс
print(time.time() - t0)    # ~50 секунд
```

49 секунд из 50 программа просто **ждёт сеть**, не делая ничего полезного. Это и есть «I/O-bound» проблема.

### Threading

```python
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=20) as ex:
    list(ex.map(requests.get, urls))    # ~3 секунды
```

Параллельные потоки скачивают одновременно. Но 20 потоков — это 20 OS-thread, ~20 МБ стека минимум. Для 1000 параллельных запросов — 1 ГБ только на стеки.

### asyncio

```python
import asyncio
import aiohttp

async def fetch(session, url):
    async with session.get(url) as resp:
        return await resp.text()

async def main():
    async with aiohttp.ClientSession() as session:
        return await asyncio.gather(*[fetch(session, u) for u in urls])

asyncio.run(main())    # ~1 секунда, без потоков
```

asyncio запускает **тысячи** задач в **одном** потоке. Без overhead на потоки. Это и есть «современный I/O Python».

---

## 2. Корутины — что это

**Корутина** — это функция, которая может «приостановиться» и «возобновиться». В Python для этого — синтаксис `async def`:

```python
async def hello():
    print("hello")
    await asyncio.sleep(1)
    print("world")
```

`async def` создаёт корутину. Когда ты её **вызываешь**, ты получаешь не результат, а **объект корутины**:

```python
c = hello()
print(c)    # <coroutine object hello at 0x...>
```

Чтобы запустить — нужен **event loop**.

---

## 3. Event loop

Event loop — сердце asyncio. Это бесконечный цикл, который:
1. Берёт следующую готовую к выполнению задачу.
2. Выполняет её до точки `await`.
3. Регистрирует ожидание (на дескриптор сокета, таймер, ...).
4. Берёт следующую готовую задачу.
5. Когда I/O готова — задача снова становится готовой.

```python
import asyncio

async def main():
    print("hello")
    await asyncio.sleep(1)
    print("world")

asyncio.run(main())
```

`asyncio.run` создаёт event loop, запускает корутину, дожидается завершения, закрывает loop.

Внутри `main()`:
- `print("hello")` — выполняется сразу.
- `await asyncio.sleep(1)` — корутина приостанавливается, loop регистрирует таймер на 1 сек, идёт обрабатывать другие задачи. Когда таймер срабатывает — корутина возобновляется.
- `print("world")` — продолжение.

В одном потоке можно запустить тысячи корутин — пока кто-то ждёт I/O, другие работают.

---

## 4. `await` — приостановить корутину

`await` выражение: «приостанови меня, пока этот объект не будет готов».

```python
async def fetch():
    response = await get_url()    # пауза до ответа
    data = await response.json()  # пауза до парсинга
    return data
```

`await` можно делать только над **awaitable** объектами:
- другая корутина: `await some_coroutine()`;
- задача: `await some_task`;
- future: `await some_future`;
- объект с `__await__`.

Внутри `async def` ты не вызываешь корутину напрямую — обязательно через `await`. Иначе:
```python
async def main():
    asyncio.sleep(1)    # ⚠️ создал корутину, но не запустил → warning
```

---

## 5. Запуск нескольких задач параллельно

`asyncio.gather` — самый частый способ:

```python
async def main():
    results = await asyncio.gather(
        fetch("url1"),
        fetch("url2"),
        fetch("url3"),
    )
    print(results)
```

Все три запускаются «одновременно», `await asyncio.gather` ждёт завершения всех. Возвращает список результатов в том же порядке.

С обработкой ошибок:
```python
results = await asyncio.gather(*coroutines, return_exceptions=True)
# результаты содержат исключения, не падают
```

### `asyncio.create_task` — фоновая задача

```python
async def main():
    task = asyncio.create_task(background_work())
    # делаем что-то ещё
    await task    # дождаться, если нужно
```

`create_task` запускает корутину в фоне, возвращает Task. Task — это «корутина с управлением» (можно отменить, ждать, узнать состояние).

---

## 6. Async-классы и контекстные менеджеры

### async with

```python
async def main():
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            text = await resp.text()
```

`async with` — асинхронная версия `with`. Класс должен иметь `__aenter__` и `__aexit__`:
```python
class AsyncResource:
    async def __aenter__(self):
        await self.acquire()
        return self
    async def __aexit__(self, *args):
        await self.release()
```

### async for

```python
async for line in async_iterator:
    process(line)
```

`async for` — для асинхронных итераторов. Класс с `__aiter__` и `__anext__`:
```python
class AsyncRange:
    def __init__(self, n):
        self.n = n
        self.i = 0
    def __aiter__(self):
        return self
    async def __anext__(self):
        if self.i >= self.n:
            raise StopAsyncIteration
        await asyncio.sleep(0.1)
        self.i += 1
        return self.i

async for x in AsyncRange(5):
    print(x)
```

---

## 7. Future, Task, Coroutine — что чем

- **Coroutine** — объект, который ты получаешь от `async def func()`. Сам не запускается.
- **Task** — обёртка вокруг корутины, которая планирует её в event loop. Запущена.
- **Future** — низкоуровневый «обещание результата». Task наследуется от Future.

```python
import asyncio

async def coro():
    return 42

c = coro()                          # Coroutine
t = asyncio.create_task(coro())      # Task — запущена в loop
f = asyncio.Future()                 # Future — пустое обещание
f.set_result(42)                     # вручную задать
```

В 99% работаешь с корутинами и тасками. Future — низкий уровень.

---

## 8. asyncio.sleep — не блокирующий sleep

```python
import asyncio
import time

# плохо — блокирует весь loop:
async def bad():
    time.sleep(1)    # ⚠️

# хорошо:
async def good():
    await asyncio.sleep(1)
```

`time.sleep` — синхронный, блокирует поток. Если в asyncio — все остальные задачи тоже встанут.

`asyncio.sleep` — корутина, которая отдаёт управление loop'у на время.

**Это общий принцип**: внутри async-кода нельзя делать долгие синхронные операции. Все «тяжёлые» операции должны быть async.

---

## 9. Обработка блокирующего кода

Что если у тебя есть синхронная функция, которую нужно вызвать в async-коде?

```python
import asyncio
import time

def blocking():
    time.sleep(2)
    return "done"

async def main():
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(None, blocking)
    # запустит blocking в потоке, не блокируя loop
```

`run_in_executor` запускает функцию в потоке (по умолчанию — ThreadPoolExecutor). Удобный shortcut в 3.9+:
```python
result = await asyncio.to_thread(blocking)
```

Используй для:
- старых синхронных библиотек;
- CPU-bound задач (но лучше ProcessPoolExecutor для них);
- работы с файлами (asyncio для файлов нет — используй `aiofiles` или `to_thread`).

---

## 10. Cancellation — отмена

Task можно отменить:
```python
async def main():
    task = asyncio.create_task(long_work())
    await asyncio.sleep(1)
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        print("cancelled")
```

Отмена — это **CancelledError**, поднятый внутри корутины на ближайшем `await`. Корутина может его поймать и сделать cleanup:
```python
async def long_work():
    try:
        await something()
    except asyncio.CancelledError:
        print("cleaning up")
        raise    # переподнять, чтобы task знала
```

В современном Python 3.11+ есть `asyncio.timeout`:
```python
async def main():
    try:
        async with asyncio.timeout(2):
            await slow()
    except TimeoutError:
        print("too slow")
```

Раньше — `asyncio.wait_for`:
```python
result = await asyncio.wait_for(slow(), timeout=2)
```

---

## 11. TaskGroup — структурированная конкурентность (3.11+)

Большой апгрейд. Раньше gather не идеально обрабатывал ошибки. Теперь:

```python
async def main():
    async with asyncio.TaskGroup() as tg:
        tg.create_task(work1())
        tg.create_task(work2())
        tg.create_task(work3())
    # все 3 завершились
```

Если хоть одна задача упала — все остальные **отменяются**, и `__aexit__` поднимает ExceptionGroup со всеми ошибками. Это «правильное» поведение.

Для нового кода — **используй TaskGroup**. gather оставь для библиотек, поддерживающих 3.10-.

---

## 12. Очереди и каналы

`asyncio.Queue` — для коммуникации между корутинами:
```python
queue = asyncio.Queue()

async def producer():
    for i in range(10):
        await queue.put(i)
        await asyncio.sleep(0.1)

async def consumer():
    while True:
        item = await queue.get()
        print(item)
        queue.task_done()

async def main():
    p = asyncio.create_task(producer())
    c = asyncio.create_task(consumer())
    await p
    await queue.join()
    c.cancel()

asyncio.run(main())
```

Pattern producer/consumer — один из самых частых.

---

## 13. Streams — TCP/UDP

Низкоуровневый сетевой API:
```python
async def echo_client():
    reader, writer = await asyncio.open_connection("example.com", 80)
    writer.write(b"GET / HTTP/1.0\r\n\r\n")
    await writer.drain()
    data = await reader.read(1000)
    writer.close()
    await writer.wait_closed()
    return data
```

Сервер:
```python
async def handle(reader, writer):
    data = await reader.read(100)
    writer.write(data)
    await writer.drain()
    writer.close()

server = await asyncio.start_server(handle, "0.0.0.0", 8888)
await server.serve_forever()
```

Для HTTP — лучше `aiohttp`. Для DB — `asyncpg` (Postgres), `aiomysql`, `motor` (MongoDB), `redis-py` (асинхронный режим).

---

## 14. Async-ко всему: экосистема

| Задача | Библиотека |
|---|---|
| HTTP-клиент | `aiohttp`, `httpx` (с async) |
| HTTP-сервер | `aiohttp`, `FastAPI`, `Starlette`, `Sanic` |
| Postgres | `asyncpg` |
| MySQL | `aiomysql` |
| Redis | `redis-py` (4.2+) |
| MongoDB | `motor` |
| Files | `aiofiles` |
| WebSocket | `websockets` |
| GraphQL | `graphql-core`, `strawberry` |
| Очереди | `arq`, `aiojobs` |

---

## 15. Типичные ошибки

### Забыл await

```python
async def main():
    result = fetch()        # ⚠️ корутина, не результат
    print(result)           # <coroutine object>
```

```python
async def main():
    result = await fetch()  # ✅
```

Аналогично:
```python
asyncio.create_task(coro)   # передал корутину
asyncio.create_task(coro())  # ✅ передал результат вызова
```

### Блокирующий код в asyncio

```python
async def main():
    time.sleep(5)              # ⚠️ блокирует
    # лучше: await asyncio.sleep(5)
    
    requests.get(url)          # ⚠️ блокирует
    # лучше: await session.get(url) с aiohttp
    
    big_dict = {i: i*2 for i in range(10_000_000)}  # ⚠️ долго в одном task
```

Любая медленная синхронная операция тормозит весь loop.

### Без TaskGroup забыли await

```python
async def main():
    asyncio.create_task(work())   # ⚠️ task создана но никто её не ждёт
    return                         # main выходит, task может не успеть
```

С TaskGroup `__aexit__` ждёт все.

### Не закрытые ресурсы

```python
async def main():
    session = aiohttp.ClientSession()
    resp = await session.get(url)
    # ⚠️ не закрыли session — warning
```

```python
async def main():
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.text()
```

### Смешивание sync и async

```python
def sync_func():
    return asyncio.run(coro())    # ⚠️ если уже есть loop — TypeError
```

Не вызывай `asyncio.run` если уже в async-контексте. Используй `await coro()`.

### Race conditions всё равно есть

GIL не спасает от race conditions в asyncio:
```python
counter = 0

async def increment():
    global counter
    cur = counter
    await asyncio.sleep(0)    # точка переключения!
    counter = cur + 1

await asyncio.gather(*[increment() for _ in range(100)])
print(counter)    # может быть < 100
```

Используй `asyncio.Lock`:
```python
lock = asyncio.Lock()

async def increment():
    global counter
    async with lock:
        counter += 1
```

---

## 16. Когда asyncio, когда нет

### Используй asyncio когда:

- много параллельных I/O (тысячи запросов, соединений);
- WebSocket-серверы, real-time приложения;
- современный backend (FastAPI, aiohttp);
- скрейпинг/парсинг с тысячами URL.

### Не используй когда:

- **CPU-bound** задачи — asyncio не поможет, нужен multiprocessing.
- Простой однократный скрипт без параллельности — обычный requests проще.
- Зависимости только синхронные (Django до 3.0, старые ORM).
- Команда не понимает async — будут баги.

### Гибридный подход

```python
# CPU-bound в executor:
result = await loop.run_in_executor(None, cpu_heavy)

# или ProcessPoolExecutor для настоящего параллелизма:
from concurrent.futures import ProcessPoolExecutor
with ProcessPoolExecutor() as ex:
    result = await loop.run_in_executor(ex, cpu_heavy)
```

---

## 17. Что нужно запомнить

- `async def` создаёт корутину. Корутина без `await`/event loop ничего не делает.
- `await coroutine` приостанавливает текущую корутину, возвращает управление loop.
- `asyncio.run(main())` — запуск точки входа.
- `asyncio.gather` — параллельный запуск нескольких корутин.
- `asyncio.create_task` — фоновая задача.
- `asyncio.TaskGroup` (3.11+) — структурированная конкурентность.
- `asyncio.Queue` для producer/consumer.
- `async with` / `async for` для асинхронных контекстов и итераторов.
- Не делай блокирующие операции в async-коде; используй `to_thread` или executor.
- Race conditions есть и в asyncio; используй `asyncio.Lock`.
- asyncio для I/O-bound, multiprocessing для CPU-bound.

После asyncio — следующая большая тема: **многопоточность и многопроцессность**. Когда что выбирать, GIL в реальной жизни, синхронизация.
