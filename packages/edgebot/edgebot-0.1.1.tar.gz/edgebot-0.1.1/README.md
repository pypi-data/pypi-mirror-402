# EdgeBot SDK

SDK для создания Telegram ботов на Cloudflare Workers с использованием Pyodide.

## Описание

EdgeBot — это минималистичный, типизированный SDK для разработки Telegram ботов, работающих на edge-инфраструктуре Cloudflare Workers. Библиотека предоставляет декларативный API для обработки различных типов обновлений от Telegram и упрощает взаимодействие с Bot API.

## Установка

```bash
pip install edgebot
```

## Архитектура

SDK состоит из трех основных компонентов:

- **Bot** — класс для регистрации обработчиков и маршрутизации обновлений
- **Context** — объект контекста с данными обновления и методами для ответа
- **InlineKeyboard** — builder для создания inline-клавиатур

## API Reference

### Bot

Основной класс для создания экземпляра бота и регистрации обработчиков.

#### Конструктор

```python
Bot(token: str, parse_mode: Optional[str] = None)
```

**Параметры:**
- `token` — токен Telegram бота
- `parse_mode` — режим форматирования по умолчанию (`"HTML"`, `"Markdown"`, `"MarkdownV2"`)

#### Методы регистрации обработчиков

Все декораторы принимают асинхронную функцию с сигнатурой `async def handler(ctx: Context) -> None`.

##### Текстовые сообщения и команды

- `@bot.on_message` — обработчик всех текстовых сообщений
- `@bot.on_command(command: str)` — обработчик команды (например, `"/start"`)

##### Callback queries

- `@bot.on_callback` — обработчик нажатий на inline-кнопки

##### Медиа-контент

- `@bot.on_photo` — обработчик фотографий
- `@bot.on_video` — обработчик видео
- `@bot.on_audio` — обработчик аудиофайлов
- `@bot.on_voice` — обработчик голосовых сообщений
- `@bot.on_document` — обработчик документов
- `@bot.on_sticker` — обработчик стикеров
- `@bot.on_animation` — обработчик GIF-анимаций

##### Специальные типы

- `@bot.on_checklist` — обработчик чеклистов
- `@bot.on_checklist_tasks_done` — обработчик завершенных задач чеклиста

#### Обработка обновлений

```python
async def process_update(update: dict[str, Any]) -> None
```

Обрабатывает входящее обновление от Telegram, вызывая соответствующие зарегистрированные обработчики.

**Параметры:**
- `update` — словарь с данными обновления от Telegram API

---

### Context

Объект контекста, передаваемый в каждый обработчик. Предоставляет доступ к данным обновления и методы для отправки ответов.

#### Атрибуты данных

##### Общие

- `update: dict` — исходное обновление от Telegram
- `chat_id: Optional[int]` — ID чата
- `message_id: Optional[int]` — ID сообщения
- `from_user: Optional[dict]` — информация об отправителе
- `message: Optional[dict]` — объект сообщения

##### Текст и команды

- `text: str` — текст сообщения
- `command: Optional[str]` — команда (например, `"/start"`), если присутствует

##### Callback

- `callback_query: Optional[dict]` — объект callback query
- `callback_data: Optional[str]` — данные callback-кнопки

##### Медиа

- `photo: Optional[list[dict]]` — массив фотографий разного разрешения
- `video: Optional[dict]` — объект видео
- `audio: Optional[dict]` — объект аудио
- `voice: Optional[dict]` — объект голосового сообщения
- `document: Optional[dict]` — объект документа
- `sticker: Optional[dict]` — объект стикера
- `animation: Optional[dict]` — объект GIF-анимации

##### Специальные

- `checklist: Optional[dict]` — объект чеклиста
- `checklist_tasks_done: Optional[dict]` — информация о завершенных задачах

#### Методы отправки

##### Текстовые сообщения

```python
async def reply(
    text: str,
    reply_markup: Optional[dict] = None,
    parse_mode: Optional[str] = None
) -> dict
```

Отправляет ответ с reply на текущее сообщение.

```python
async def send(
    text: str,
    reply_markup: Optional[dict] = None,
    parse_mode: Optional[str] = None
) -> dict
```

Отправляет новое сообщение без reply.

```python
async def edit_message(
    text: str,
    reply_markup: Optional[dict] = None,
    parse_mode: Optional[str] = None
) -> dict
```

Редактирует текущее сообщение (используется в callback-обработчиках).

##### Медиа

```python
async def send_photo(
    photo: str,
    caption: Optional[str] = None,
    reply_markup: Optional[dict] = None,
    parse_mode: Optional[str] = None
) -> dict
```

Отправляет фотографию по `file_id` или URL.

```python
async def send_video(
    video: str,
    caption: Optional[str] = None,
    reply_markup: Optional[dict] = None,
    parse_mode: Optional[str] = None
) -> dict
```

Отправляет видео по `file_id` или URL.

```python
async def send_animation(
    animation: str,
    caption: Optional[str] = None,
    reply_markup: Optional[dict] = None,
    parse_mode: Optional[str] = None
) -> dict
```

Отправляет GIF-анимацию по `file_id` или URL.

```python
async def send_sticker(
    sticker: str,
    reply_markup: Optional[dict] = None
) -> dict
```

Отправляет стикер по `file_id`.

```python
async def send_voice(
    voice: str,
    caption: Optional[str] = None,
    reply_markup: Optional[dict] = None,
    parse_mode: Optional[str] = None
) -> dict
```

Отправляет голосовое сообщение по `file_id`.

```python
async def send_audio(
    audio: str,
    caption: Optional[str] = None,
    reply_markup: Optional[dict] = None,
    parse_mode: Optional[str] = None,
    title: Optional[str] = None,
    performer: Optional[str] = None
) -> dict
```

Отправляет аудиофайл по `file_id` или URL.

```python
async def send_document(
    document: str,
    caption: Optional[str] = None,
    reply_markup: Optional[dict] = None,
    parse_mode: Optional[str] = None
) -> dict
```

Отправляет документ по `file_id` или URL.

##### Callback queries

```python
async def answer_callback(
    text: Optional[str] = None,
    show_alert: bool = False
) -> dict
```

Отвечает на callback query (убирает индикатор загрузки на кнопке).

---

### InlineKeyboard

Builder для создания inline-клавиатур.

#### Методы

```python
def button(
    text: str,
    callback_data: Optional[str] = None,
    url: Optional[str] = None
) -> InlineKeyboard
```

Добавляет кнопку в текущий ряд. Параметры `callback_data` и `url` взаимоисключающие.

**Параметры:**
- `text` — текст кнопки
- `callback_data` — данные для callback
- `url` — URL для кнопки-ссылки

**Возвращает:** `self` для chaining.

```python
def row() -> InlineKeyboard
```

Завершает текущий ряд и начинает новый.

**Возвращает:** `self` для chaining.

```python
def build() -> dict
```

Возвращает готовую структуру `reply_markup` для Telegram API.

**Пример:**

```python
keyboard = InlineKeyboard()
keyboard.button("Кнопка 1", callback_data="btn1")
keyboard.button("Кнопка 2", callback_data="btn2")
keyboard.row()
keyboard.button("Ссылка", url="https://example.com")

await ctx.reply("Выберите действие:", reply_markup=keyboard.build())
```

---

## Пример использования

### Универсальный эхо-бот

Бот, который идентифицирует тип входящего контента и отправляет его обратно.

```python
from workers import Response, WorkerEntrypoint
from edgebot import Bot, Context

class Default(WorkerEntrypoint):
    def __init__(self, env):
        super().__init__(env)
        self.bot = Bot(env.BOT_TOKEN)
        self.setup_handlers()
    
    def setup_handlers(self):
        @self.bot.on_command("/start")
        async def start(ctx: Context):
            await ctx.reply(
                "Эхо-бот запущен.\n"
                "Отправьте любой контент: текст, фото, видео, аудио, "
                "голосовое сообщение, документ, стикер или GIF."
            )
        
        @self.bot.on_message
        async def echo_text(ctx: Context):
            await ctx.reply(f"📝 Текст: {ctx.text}")
        
        @self.bot.on_photo
        async def echo_photo(ctx: Context):
            file_id = ctx.photo[-1]["file_id"]
            caption = "📷 Фото"
            await ctx.send_photo(file_id, caption=caption)
        
        @self.bot.on_video
        async def echo_video(ctx: Context):
            file_id = ctx.video["file_id"]
            caption = "🎬 Видео"
            await ctx.send_video(file_id, caption=caption)
        
        @self.bot.on_audio
        async def echo_audio(ctx: Context):
            file_id = ctx.audio["file_id"]
            title = ctx.audio.get("title", "Unknown")
            performer = ctx.audio.get("performer", "Unknown")
            caption = f"🎵 Аудио: {performer} - {title}"
            await ctx.send_audio(file_id, caption=caption)
        
        @self.bot.on_voice
        async def echo_voice(ctx: Context):
            file_id = ctx.voice["file_id"]
            duration = ctx.voice.get("duration", 0)
            caption = f"🎤 Голосовое сообщение ({duration} сек.)"
            await ctx.send_voice(file_id, caption=caption)
        
        @self.bot.on_document
        async def echo_document(ctx: Context):
            file_id = ctx.document["file_id"]
            file_name = ctx.document.get("file_name", "document")
            caption = f"📄 Документ: {file_name}"
            await ctx.send_document(file_id, caption=caption)
        
        @self.bot.on_sticker
        async def echo_sticker(ctx: Context):
            file_id = ctx.sticker["file_id"]
            await ctx.send_sticker(file_id)
        
        @self.bot.on_animation
        async def echo_animation(ctx: Context):
            file_id = ctx.animation["file_id"]
            caption = "🎞️ GIF-анимация"
            await ctx.send_animation(file_id, caption=caption)
    
    async def fetch(self, request):
        update = await request.json()
        await self.bot.process_update(update)
        return Response('{"ok": true}')
```

---

## Обработка ошибок

Все исключения в обработчиках логируются в консоль. Рекомендуется оборачивать критичные участки в `try-except`:

```python
@bot.on_message
async def handler(ctx: Context):
    try:
        # ваш код
        await ctx.reply("OK")
    except Exception as e:
        print(f"[error] handler failed: {e}")
        await ctx.reply("Произошла ошибка")
```

---

## Интеграция с Cloudflare KV

Для сохранения состояния используйте Cloudflare KV:

```python
class Default(WorkerEntrypoint):
    def __init__(self, env):
        super().__init__(env)
        self.bot = Bot(env.BOT_TOKEN)
        self.kv = env.BOT_STATE
    
    # в обработчиках:
    # await self.kv.put(key, value)
    # value = await self.kv.get(key)
```

---

## Лицензия

MIT
