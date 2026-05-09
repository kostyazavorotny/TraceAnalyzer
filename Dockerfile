# Используем Python на базе Debian для стабильности библиотек
FROM python:3.12-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копируем и устанавливаем зависимости
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Копируем код
COPY . .

# Пробрасываем порт Streamlit
EXPOSE 8501

# Команда запуска с отключением проверки обновлений
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
