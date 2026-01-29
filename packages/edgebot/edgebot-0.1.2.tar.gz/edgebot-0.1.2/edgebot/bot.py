"""
Основной класс бота с системой обработчиков
"""

from typing import Any, Callable, Awaitable, Optional
from .context import Context


HandlerFunc = Callable[[Context], Awaitable[None]]


class Bot:
    """
    Главный класс SDK для создания Telegram ботов.
    
    Пример использования:
        bot = Bot(token)
        
        @bot.on_command('/start')
        async def start(ctx):
            await ctx.reply('Привет!')
        
        @bot.on_message
        async def echo(ctx):
            await ctx.reply(f'Ты написал: {ctx.text}')
        
        await bot.process_update(update)
    """
    
    def __init__(self, token: str, parse_mode: Optional[str] = None):
        """
        Args:
            token: Токен Telegram бота
            parse_mode: Форматирование по умолчанию (например, "Markdown" или "HTML")
        """
        self.token = token
        self.parse_mode = parse_mode
        self._env = None        # Переменные и объекты окружения Cloudflare Workers
        self._cf_ctx = None     # Контекст запроса в Cloudflare Workers
        self._handlers: dict[str, list[Any]] = {
            "message": [],      # обработчики текстовых сообщений
            "command": [],      # обработчики команд (список кортежей (команда, функция))
            "callback": [],     # обработчики callback от кнопок
            "voice": [],        # обработчики голосовых сообщений
            "photo": [],        # обработчики фото
            "video": [],        # обработчики видео
            "audio": [],        # обработчики аудио
            "sticker": [],      # обработчики стикеров
            "animation": [],    # обработчики анимаций (GIF)
            "document": [],     # обработчики документов
            "checklist": [],    # обработчики чеклистов
            "checklist_tasks_done": [],  # обработчики выполненных задач чеклиста
        }
    
    def env(self, env: Any) -> "Bot":
        self._env = env
        return self
    
    def ctx(self, ctx: Any) -> "Bot":
        self._cf_ctx = ctx
        return self
    
    def on_message(self, func: HandlerFunc) -> HandlerFunc:
        """
        Декоратор для регистрации обработчика текстовых сообщений.
        
        Args:
            func: Async функция-обработчик
        
        Returns:
            Та же функция (для возможности использования как декоратор)
        """
        self._handlers["message"].append(func)
        return func
    
    def on_command(self, command: str) -> Callable[[HandlerFunc], HandlerFunc]:
        """
        Декоратор для регистрации обработчика команды.
        
        Args:
            command: Команда (например, '/start' или '/help')
        
        Returns:
            Декоратор
        """
        def decorator(func: HandlerFunc) -> HandlerFunc:
            self._handlers["command"].append((command, func))
            return func
        return decorator
    
    def on_callback(self, func: HandlerFunc) -> HandlerFunc:
        """
        Декоратор для регистрации обработчика нажатий на inline кнопки.
        
        Args:
            func: Async функция-обработчик
        
        Returns:
            Та же функция
        """
        self._handlers["callback"].append(func)
        return func
    
    def on_voice(self, func: HandlerFunc) -> HandlerFunc:
        """
        Декоратор для регистрации обработчика голосовых сообщений.
        
        Args:
            func: Async функция-обработчик
        
        Returns:
            Та же функция
        """
        self._handlers["voice"].append(func)
        return func
    
    def on_photo(self, func: HandlerFunc) -> HandlerFunc:
        """
        Декоратор для регистрации обработчика фото.
        
        Args:
            func: Async функция-обработчик
        
        Returns:
            Та же функция
        """
        self._handlers["photo"].append(func)
        return func
    
    def on_video(self, func: HandlerFunc) -> HandlerFunc:
        """
        Декоратор для регистрации обработчика видео.
        
        Args:
            func: Async функция-обработчик
        
        Returns:
            Та же функция
        """
        self._handlers["video"].append(func)
        return func
    
    def on_audio(self, func: HandlerFunc) -> HandlerFunc:
        """
        Декоратор для регистрации обработчика аудио.
        
        Args:
            func: Async функция-обработчик
        
        Returns:
            Та же функция
        """
        self._handlers["audio"].append(func)
        return func
    
    def on_sticker(self, func: HandlerFunc) -> HandlerFunc:
        """
        Декоратор для регистрации обработчика стикеров.
        
        Args:
            func: Async функция-обработчик
        
        Returns:
            Та же функция
        """
        self._handlers["sticker"].append(func)
        return func
    
    def on_animation(self, func: HandlerFunc) -> HandlerFunc:
        """
        Декоратор для регистрации обработчика анимаций (GIF).
        
        Args:
            func: Async функция-обработчик
        
        Returns:
            Та же функция
        """
        self._handlers["animation"].append(func)
        return func
    
    def on_document(self, func: HandlerFunc) -> HandlerFunc:
        """
        Декоратор для регистрации обработчика документов.
        
        Args:
            func: Async функция-обработчик
        
        Returns:
            Та же функция
        """
        self._handlers["document"].append(func)
        return func
    
    def on_checklist(self, func: HandlerFunc) -> HandlerFunc:
        """
        Декоратор для регистрации обработчика чеклистов.
        
        Args:
            func: Async функция-обработчик
        
        Returns:
            Та же функция
        """
        self._handlers["checklist"].append(func)
        return func
    
    def on_checklist_tasks_done(self, func: HandlerFunc) -> HandlerFunc:
        """
        Декоратор для регистрации обработчика выполненных задач чеклиста.
        
        Args:
            func: Async функция-обработчик
        
        Returns:
            Та же функция
        """
        self._handlers["checklist_tasks_done"].append(func)
        return func
    
    async def process_update(self, update: dict[str, Any]) -> None:
        """
        Обрабатывает апдейт от Telegram, вызывая соответствующие обработчики.
        
        Args:
            update: Словарь с апдейтом от Telegram
        """
        ctx = Context(self, update)
        
        # Обрабатываем callback query
        if ctx.callback_query:
            for handler in self._handlers["callback"]:
                try:
                    await handler(ctx)
                except Exception as e:
                    print(f"[error] callback handler failed: {e}")
            return
        
        # Обрабатываем команды
        if ctx.command:
            for command, handler in self._handlers["command"]:
                if ctx.command == command or ctx.text.startswith(command):
                    try:
                        await handler(ctx)
                    except Exception as e:
                        print(f"[error] command handler for {command} failed: {e}")
            return
        
        # Обрабатываем голосовые сообщения
        if ctx.voice:
            for handler in self._handlers["voice"]:
                try:
                    await handler(ctx)
                except Exception as e:
                    print(f"[error] voice handler failed: {e}")
            return
        
        # Обрабатываем фото
        if ctx.photo:
            for handler in self._handlers["photo"]:
                try:
                    await handler(ctx)
                except Exception as e:
                    print(f"[error] photo handler failed: {e}")
            return
        
        # Обрабатываем видео
        if ctx.video:
            for handler in self._handlers["video"]:
                try:
                    await handler(ctx)
                except Exception as e:
                    print(f"[error] video handler failed: {e}")
            return
        
        # Обрабатываем аудио
        if ctx.audio:
            for handler in self._handlers["audio"]:
                try:
                    await handler(ctx)
                except Exception as e:
                    print(f"[error] audio handler failed: {e}")
            return
        
        # Обрабатываем стикеры
        if ctx.sticker:
            for handler in self._handlers["sticker"]:
                try:
                    await handler(ctx)
                except Exception as e:
                    print(f"[error] sticker handler failed: {e}")
            return
        
        # Обрабатываем анимации (GIF)
        if ctx.animation:
            for handler in self._handlers["animation"]:
                try:
                    await handler(ctx)
                except Exception as e:
                    print(f"[error] animation handler failed: {e}")
            return
        
        # Обрабатываем документы
        if ctx.document:
            for handler in self._handlers["document"]:
                try:
                    await handler(ctx)
                except Exception as e:
                    print(f"[error] document handler failed: {e}")
            return
        
        # Обрабатываем выполненные задачи чеклиста
        if ctx.checklist_tasks_done:
            for handler in self._handlers["checklist_tasks_done"]:
                try:
                    await handler(ctx)
                except Exception as e:
                    print(f"[error] checklist_tasks_done handler failed: {e}")
            return
        
        # Обрабатываем чеклисты
        if ctx.checklist:
            for handler in self._handlers["checklist"]:
                try:
                    await handler(ctx)
                except Exception as e:
                    print(f"[error] checklist handler failed: {e}")
            return
        
        # Обрабатываем текстовые сообщения
        if ctx.text:
            for handler in self._handlers["message"]:
                try:
                    await handler(ctx)
                except Exception as e:
                    print(f"[error] message handler failed: {e}")
            return

