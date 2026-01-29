# 🤖 TG Runner CLI

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)
![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20macOS%20%7C%20Windows-lightgrey)

**CLI для запуска Telegram-ботов через TG Runner**

[Быстрый старт](#-быстрый-старт) •
[Команды](#-команды) •
[Режимы деплоя](#-режимы-деплоя)

</div>

---

## ✨ Возможности

- 🚀 **Три режима деплоя**: код, Docker, Git
- 📊 **Полное управление**: start, stop, logs, status
- 🔒 **Изоляция**: каждый бот в Docker-контейнере
- 🎨 **Красивый UI**: цветной вывод с Rich

---

## 📦 Установка

```bash
pip install tg-runner-cli
```

---

## 🚀 Быстрый старт

### 1. Настройка

```bash
export TG_RUNNER_URL=http://your-orchestrator:8000
export TG_RUNNER_TOKEN=your-token
```

### 2. Запуск бота

```bash
# Простой бот из файла
tg-runner start my-bot --simple bot.py \
  -r "aiogram>=3.0" \
  -e "BOT_TOKEN=123:ABC..."

# Из Git репозитория
tg-runner start my-bot --git https://github.com/user/bot.git \
  -e "BOT_TOKEN=123:ABC..."
```

### 3. Управление

```bash
tg-runner list              # Список ботов
tg-runner status my-bot     # Статус
tg-runner logs my-bot       # Логи
tg-runner stop my-bot       # Остановка
```

---

## 📋 Команды

| Команда | Описание |
|---------|----------|
| `start` | Запустить бота |
| `stop` | Остановить бота |
| `update` | Обновить код бота |
| `restart` | Перезапустить |
| `list` | Список всех ботов |
| `status` | Статус бота |
| `logs` | Логи бота |

---

## 🎯 Режимы деплоя

### 1️⃣ Simple — Код напрямую

```bash
# Один файл
tg-runner start bot --simple bot.py -r "aiogram>=3.0"

# Несколько файлов
tg-runner start bot --simple main.py handlers.py -r "aiogram,aiohttp"

# Inline код
tg-runner start bot --simple --inline --code 'print("Hello")'
```

### 2️⃣ Custom — Dockerfile/Git

```bash
# Из директории с Dockerfile
tg-runner start bot --custom ./my-project/

# Из Git репозитория
tg-runner start bot --git https://github.com/user/bot.git --branch main
```

### 3️⃣ Image — Готовый Docker-образ

```bash
tg-runner start bot --image ghcr.io/user/my-bot:v1.0

# С авторизацией
tg-runner start bot --image registry.com/bot:latest \
  --registry-user user --registry-pass token
```

---

## 📝 Пример бота

**bot.py:**
```python
import asyncio, os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

bot = Bot(token=os.environ["BOT_TOKEN"])
dp = Dispatcher()

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("Привет! 👋")

@dp.message()
async def echo(message: types.Message):
    await message.answer(message.text)

asyncio.run(dp.start_polling(bot))
```

**Запуск:**
```bash
tg-runner start echo-bot --simple bot.py \
  -r "aiogram>=3.0" \
  -e "BOT_TOKEN=123:ABC..."
```

---

## ⚙️ Конфигурация

| Переменная | Описание |
|------------|----------|
| `TG_RUNNER_URL` | URL оркестратора |
| `TG_RUNNER_TOKEN` | Токен клиента |

Или через флаги:
```bash
tg-runner --url http://localhost:8000 --token mytoken start ...
```

---

## 🔗 Экосистема TG Runner

| Компонент | Описание |
|-----------|----------|
| [tg-runner-orchestrator](https://github.com/TimaxLacs/tg-runner-orchestrator) | Orchestrator |
| [tg-runner-worker](https://github.com/TimaxLacs/tg-runner-worker) | Worker |
| [tg-runner-cli](https://github.com/TimaxLacs/tg-runner-cli) | CLI (этот репо) |

---

## 🔒 Лимиты

| Параметр | Значение |
|----------|----------|
| Макс. ботов | 3 |
| Время работы | 24 часа |
| RAM | 256 MB |
| CPU | 0.5 cores |

---

## 📄 Лицензия

MIT License

---

<div align="center">

Made with ❤️ by [TimaxLacs](https://github.com/TimaxLacs)

</div>
