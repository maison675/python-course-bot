FROM python:3.12-slim

WORKDIR /app

# Создаём непривилегированного пользователя для запуска кода
RUN useradd -m -u 1000 botuser

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY bot ./bot
COPY sandbox ./sandbox
COPY content ./content

RUN mkdir -p /app/data && chown -R botuser:botuser /app

USER botuser

CMD ["python", "-m", "bot.main"]
