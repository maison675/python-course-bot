# Файлы и JSON — от 0 до 100%

Файлы — это способ программы **запомнить что-то** между запусками. Закрыл программу — оперативная память очистилась, но файлы на диске остались. Поэтому без работы с файлами нельзя сохранять конфиги, логи, кэши, базы данных, картинки, документы.

JSON — это **формат текстовых файлов**, который идеально подходит для хранения структурированных данных Python. JSON ↔ dict — это мост между «памятью программы» и «текстовым файлом на диске». 99% веб-API общаются JSON-ом.

Разберём всё: открытие файлов, режимы, кодировки, контекстные менеджеры, JSON, CSV, типичные ошибки.

---

## 1. Открытие файла

```python
f = open("data.txt", "r", encoding="utf-8")
text = f.read()
f.close()
```

`open(path, mode, encoding=...)` возвращает **file object** — обёртку над OS-ным файловым дескриптором. Чтобы операционная система освободила ресурс — обязательно `close()`.

### Контекстный менеджер (with)

Лучше — через `with`:
```python
with open("data.txt", "r", encoding="utf-8") as f:
    text = f.read()
```

`with` гарантирует `close()` даже при исключении внутри. Это **стандарт** работы с файлами в Python — всегда with.

---

## 2. Режимы открытия

| Режим | Что делает |
|---|---|
| `"r"` | чтение (по умолчанию). Файл **должен существовать**. |
| `"w"` | запись. **Перезаписывает** файл. Создаёт новый, если нет. |
| `"a"` | добавление в конец (append). Создаёт, если нет. |
| `"x"` | создание. Падает с FileExistsError если уже есть. |
| `"r+"` | чтение и запись. Файл должен существовать. |
| `"w+"` | запись и чтение. Перезаписывает. |
| `"a+"` | добавление и чтение. |
| `"b"` | бинарный режим (вместе с другими: `"rb"`, `"wb"`, `"ab"`). |
| `"t"` | текстовый (по умолчанию). |

### Текстовый vs бинарный

```python
# текстовый — для строк, с кодировкой
with open("doc.txt", "r", encoding="utf-8") as f:
    text = f.read()    # str

# бинарный — для байтов
with open("image.png", "rb") as f:
    data = f.read()    # bytes
```

Бинарный режим **запрещает** `encoding`. В нём файл — просто байты, без интерпретации текста.

Используй бинарный для:
- картинок, видео, музыки, архивов;
- бинарных протоколов (msgpack, protobuf);
- когда не уверен в кодировке.

---

## 3. Кодировки

### Всегда указывай encoding!

```python
with open("file.txt", "r") as f:        # ⚠️ кодировка зависит от ОС
    ...

with open("file.txt", "r", encoding="utf-8") as f:   # ✅
    ...
```

Без `encoding` Python использует `locale.getpreferredencoding()`. На Linux/macOS — обычно UTF-8, на Windows — может быть cp1251 (русская). Это причина «иероглифов» при переносе скрипта между системами.

### Что брать

- **UTF-8** — стандарт. 99% случаев. Совместимо с ASCII (английский), поддерживает все языки и эмодзи.
- **cp1251**, **koi8-r** — старые русские. Если работаешь с легаси.
- **latin-1** — однобайтовая, никогда не падает при чтении (любой байт мапится).

### Если не знаешь кодировку

Библиотека `chardet`:
```python
import chardet

with open("unknown.txt", "rb") as f:
    raw = f.read()
result = chardet.detect(raw)
print(result)    # {'encoding': 'utf-8', 'confidence': 0.9}

text = raw.decode(result["encoding"])
```

### errors=

```python
with open("data.txt", "r", encoding="utf-8", errors="replace") as f:
    text = f.read()
```

Стратегии при ошибках декодирования:
- `"strict"` (по умолчанию) — падает.
- `"ignore"` — пропускает невалидные байты.
- `"replace"` — заменяет на `�` (U+FFFD).
- `"backslashreplace"` — заменяет на `\xHH`.

В продакшене — `"strict"` и обрабатывать исключение явно. Лучше падать сразу, чем тихо корраптить данные.

---

## 4. Чтение

### Всё разом

```python
with open("data.txt", "r", encoding="utf-8") as f:
    text = f.read()        # вся строка
```

Удобно для маленьких файлов. Не используй для больших — съест память.

### По строкам

```python
with open("data.txt", "r", encoding="utf-8") as f:
    for line in f:                    # ленивый итератор
        print(line.rstrip())          # rstrip убирает \n
```

Эффективно для файлов любого размера — читается по чанку.

### Список строк

```python
with open("data.txt", "r", encoding="utf-8") as f:
    lines = f.readlines()
# или
lines = list(f)        # эквивалент
```

В отличие от итератора — читает всё в память.

### Одна строка

```python
with open("data.txt", "r", encoding="utf-8") as f:
    first = f.readline()
    second = f.readline()
```

`readline` возвращает строку с `\n` в конце (или без, если последняя). Возвращает `""` на EOF.

### По чанку

```python
with open("big.bin", "rb") as f:
    while chunk := f.read(4096):    # walrus, Python 3.8+
        process(chunk)
```

Удобно для больших бинарных файлов.

---

## 5. Запись

### `f.write` — простая запись

```python
with open("output.txt", "w", encoding="utf-8") as f:
    f.write("Привет, мир!\n")
    f.write("Вторая строка\n")
```

`write` **не добавляет** `\n` — добавляй сам.

### Несколько строк за раз

```python
with open("output.txt", "w", encoding="utf-8") as f:
    f.writelines(["строка 1\n", "строка 2\n", "строка 3\n"])
```

### Через print

```python
with open("log.txt", "w", encoding="utf-8") as f:
    print("Запись 1", file=f)        # автоматически \n
    print("Запись 2", file=f)
```

Удобно — print имеет sep, end, форматирование.

### Append

```python
with open("log.txt", "a", encoding="utf-8") as f:
    f.write(f"[{datetime.now()}] Событие\n")
```

`"a"` дописывает в конец. Часто используется для логов.

---

## 6. Двоичные файлы

```python
# чтение
with open("photo.jpg", "rb") as f:
    data = f.read()           # bytes

# запись
with open("output.bin", "wb") as f:
    f.write(b"\x00\x01\x02")
```

Копирование файла:
```python
with open("src.bin", "rb") as src, open("dst.bin", "wb") as dst:
    while chunk := src.read(8192):
        dst.write(chunk)
```

### Курсор и seek

В файле есть **позиция чтения/записи** (cursor):
```python
with open("data.bin", "rb") as f:
    f.seek(100)               # перейти к байту 100
    chunk = f.read(50)        # прочитать 50 байт начиная с 100
    pos = f.tell()            # текущая позиция (150)
    f.seek(0)                 # вернуться к началу
    f.seek(0, 2)              # перейти к КОНЦУ (whence=2 — от конца)
```

`seek(offset, whence)`:
- whence=0 (по умолчанию) — от начала
- whence=1 — относительно текущей позиции
- whence=2 — от конца

---

## 7. JSON — общение с структурированными данными

JSON — текстовый формат, читаемый человеком, понятный любому языку программирования.

### Что есть в JSON

| Python | JSON |
|---|---|
| `dict` | object `{...}` |
| `list`, `tuple` | array `[...]` |
| `str` | string `"..."` |
| `int`, `float` | number |
| `True` | `true` |
| `False` | `false` |
| `None` | `null` |
| `bytes`, `set`, `complex`, ... | ❌ — нужен кастомный encoder |

### Сериализация (Python → JSON-строка)

```python
import json

data = {
    "name": "Alice",
    "age": 30,
    "hobbies": ["reading", "coding"],
    "is_admin": False,
    "spouse": None,
}

s = json.dumps(data)
print(s)
# {"name": "Alice", "age": 30, "hobbies": ["reading", "coding"], "is_admin": false, "spouse": null}

s_pretty = json.dumps(data, indent=2)
print(s_pretty)
# {
#   "name": "Alice",
#   "age": 30,
#   ...
# }

s_unicode = json.dumps(data, ensure_ascii=False)
# Сохраняет кириллицу как есть, не \u04XX
```

### Десериализация (JSON-строка → Python)

```python
s = '{"name": "Alice", "age": 30}'
data = json.loads(s)
print(data)              # {'name': 'Alice', 'age': 30}
print(data["name"])      # 'Alice'
```

### Файлы JSON

```python
import json

# запись в файл
with open("data.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

# чтение из файла
with open("data.json", "r", encoding="utf-8") as f:
    data = json.load(f)
```

`json.dump`/`json.load` — для файлов. `json.dumps`/`json.loads` — для строк.

### Пользовательские типы

```python
from datetime import datetime

data = {"now": datetime.now()}
json.dumps(data)    # TypeError: Object of type datetime is not JSON serializable

# через default:
json.dumps(data, default=str)    # datetime → str автоматически
```

Для серьёзной сериализации — `pydantic`, `dataclass-json`, или вручную:
```python
class Encoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

json.dumps(data, cls=Encoder)
```

---

## 8. CSV

CSV (Comma Separated Values) — табличный формат, базовый для Excel и баз данных.

```python
import csv

# чтение
with open("data.csv", "r", encoding="utf-8") as f:
    reader = csv.reader(f)
    for row in reader:
        print(row)        # row — list строк

# запись
with open("data.csv", "w", encoding="utf-8", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["name", "age", "city"])
    writer.writerow(["Alice", "30", "Moscow"])
    writer.writerow(["Bob", "25", "SPb"])
```

`newline=""` важен — без него на Windows будут лишние \r.

### С заголовками — DictReader/DictWriter

```python
with open("data.csv", "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        print(row["name"], row["age"])

with open("data.csv", "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["name", "age", "city"])
    writer.writeheader()
    writer.writerow({"name": "Alice", "age": 30, "city": "Moscow"})
```

Для больших объёмов — `pandas`:
```python
import pandas as pd
df = pd.read_csv("big.csv")
```

---

## 9. pathlib — современная работа с путями

```python
from pathlib import Path

p = Path("data") / "subdir" / "file.txt"
print(p)              # data/subdir/file.txt (или data\subdir\file.txt на Windows)

# атрибуты
p.parent              # Path('data/subdir')
p.name                # 'file.txt'
p.stem                # 'file'
p.suffix              # '.txt'
p.parts               # ('data', 'subdir', 'file.txt')

# проверки
p.exists()            # bool
p.is_file()
p.is_dir()
p.is_absolute()

# манипуляции
p.with_suffix(".bak")        # Path('.../file.bak')
p.with_name("newname.txt")
Path.cwd()                    # текущая директория
Path.home()                   # домашняя

# операции
p.read_text(encoding="utf-8")
p.write_text("hello", encoding="utf-8")
p.read_bytes()
p.write_bytes(b"\x00")

# создание/удаление
p.touch()                     # создать пустой
p.parent.mkdir(parents=True, exist_ok=True)
p.unlink()                    # удалить
p.rename(other_path)

# обход директории
for child in p.iterdir():
    print(child)

# маска
for py in Path(".").glob("*.py"):
    print(py)

for py in Path(".").rglob("*.py"):    # рекурсивно
    print(py)
```

`pathlib` идеально подходит для современных программ. `os.path` всё ещё используется в старом коде.

---

## 10. shutil — высокоуровневые операции

```python
import shutil

shutil.copy("src.txt", "dst.txt")
shutil.copy2("src.txt", "dst.txt")        # с метаданными (mtime, права)
shutil.copytree("src/", "dst/")           # рекурсивно директория
shutil.move("a.txt", "b.txt")
shutil.rmtree("dir/")                      # удалить директорию рекурсивно

shutil.disk_usage("/")                     # (total, used, free)
```

---

## 11. Временные файлы

```python
import tempfile

# временный файл
with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
    f.write("temp data")
    path = f.name
print(path)    # /tmp/tmpXXXXXX
# не удаляется автоматически благодаря delete=False

# временная директория
with tempfile.TemporaryDirectory() as tmp:
    print(tmp)    # /tmp/tmpXXXXXX
    # удаляется автоматически при выходе из with
```

Полезно для:
- скачивания и обработки файлов;
- тестов;
- кешей.

---

## 12. Чтение больших файлов

### Не читай всё разом

```python
with open("huge.txt", "r", encoding="utf-8") as f:
    text = f.read()    # ⚠️ если файл 10 ГБ — словишь MemoryError
```

### Читай построчно

```python
with open("huge.txt", "r", encoding="utf-8") as f:
    for line in f:
        process(line)
```

Память — только текущая строка.

### Читай по чанкам

```python
with open("huge.bin", "rb") as f:
    while chunk := f.read(8192):
        process(chunk)
```

8192 байт — типичный размер чанка (один блок диска).

### `mmap` — memory-mapped

```python
import mmap

with open("huge.txt", "r+b") as f:
    with mmap.mmap(f.fileno(), 0) as mm:
        # работаешь как со строкой/байтами, но физически читается с диска
        pos = mm.find(b"target")
```

Для очень больших файлов и random access — быстрее, чем seek+read.

---

## 13. Контекстные менеджеры — как они работают

`with open(...)` — это **контекстный менеджер**. Чтобы свой класс работал в `with`, нужны методы:
```python
class MyResource:
    def __enter__(self):
        print("opening")
        return self
    def __exit__(self, exc_type, exc_value, traceback):
        print("closing")
        return False    # False/None — не подавлять исключение

with MyResource() as r:
    print("inside")
```

Вывод:
```
opening
inside
closing
```

Если внутри `with` возникло исключение — `__exit__` всё равно вызывается. Это и обеспечивает гарантированное закрытие файла.

Для простых случаев — декоратор `contextlib.contextmanager`:
```python
from contextlib import contextmanager

@contextmanager
def my_resource():
    print("opening")
    try:
        yield "data"
    finally:
        print("closing")

with my_resource() as r:
    print(r)
```

---

## 14. Типичные ошибки

### Файл не закрылся

```python
f = open("data.txt", "r")
text = f.read()
# забыли f.close()
```

Решение — `with`.

### Перезаписал важный файл

```python
with open("important.txt", "w") as f:    # ⚠️ "w" перезаписывает!
    ...
```

Если файл существовал — содержимое потеряно. Используй `"a"` для добавления или `"x"` для строгого создания.

### Кодировка

```python
with open("file.txt", "r") as f:    # на Windows может быть cp1251
    ...
```

Всегда `encoding="utf-8"`.

### JSON и tuple

```python
data = (1, 2, 3)
s = json.dumps(data)
back = json.loads(s)
print(back)        # [1, 2, 3] — стало list, не tuple!
```

JSON не различает list и tuple — всегда list.

### Бинарный режим без `b`

```python
with open("img.jpg", "r") as f:    # ⚠️ UnicodeDecodeError или мусор
    ...
```

Для не-текстовых — обязательно `"rb"`.

### Encoding с binary режимом

```python
with open("file.bin", "rb", encoding="utf-8") as f:    # ⚠️ TypeError
    ...
```

Кодировка — только в текстовом режиме.

### CSV без `newline=""`

```python
with open("out.csv", "w") as f:    # на Windows будут лишние \r\r\n
    csv.writer(f).writerow(["a", "b"])
```

Используй `newline=""` всегда.

### Чтение JSON в неверной структуре

```python
data = json.load(f)
print(data["key"])    # TypeError если data — list, а не dict
```

Проверяй тип:
```python
if isinstance(data, dict):
    process_dict(data)
elif isinstance(data, list):
    process_list(data)
```

---

## 15. Что нужно запомнить

- Открывай файлы через `with open(...)`, всегда с `encoding="utf-8"`.
- Бинарный режим (`"rb"`/`"wb"`) — для не-текстовых файлов.
- Читай большие файлы построчно или по чанкам, не разом.
- JSON ↔ dict — `json.dumps`/`json.loads`/`json.dump`/`json.load`.
- `ensure_ascii=False, indent=2` — для красивого вывода.
- `pathlib.Path` — современный способ работать с путями.
- `shutil` для копирования/удаления, `tempfile` для временных.
- Не забывай `newline=""` для CSV.
- JSON не сохраняет tuple/set/datetime — нужен default или кастомный encoder.

После файлов осталось два важных столпа: **исключения** (как устроены ошибки) и **ООП**. Двигаемся дальше.
