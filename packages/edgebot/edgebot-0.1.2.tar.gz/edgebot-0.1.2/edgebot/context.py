"""
Контекст сообщения с удобными методами для работы с обновлениями
"""

from typing import Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .bot import Bot

from .api import (send_message, edit_message_text, answer_callback_query,
                  send_photo, send_video, send_animation, send_sticker,
                  send_voice, send_audio, send_document)


class Context:
    """
    Контекст обработки обновления от Telegram.
    Предоставляет удобный доступ к данным и методы для ответа.
    
    Attributes:
        bot: Экземпляр бота
        update: Исходный update от Telegram
        message: Объект сообщения (если есть)
        callback_query: Объект callback query (если есть)
        chat_id: ID чата
        message_id: ID сообщения
        text: Текст сообщения
        voice: Объект голосового сообщения
        photo: Список фото (от маленького к большому)
        document: Объект документа
        video: Объект видео
        audio: Объект аудио
        sticker: Объект стикера
        animation: Объект анимации (GIF)
        document: Объект документа
        checklist: Объект чеклиста
        checklist_tasks_done: Информация о выполненных задачах чеклиста
        from_user: Информация об отправителе
        callback_data: Данные из callback кнопки
    """

    def __init__(self, bot: "Bot", update: dict[str, Any]):
        self.bot = bot
        self.update = update
        self.env = bot._env
        self.request = bot._cf_ctx
        self._parse_update()

    def _parse_update(self) -> None:
        """Извлекает основные поля из апдейта"""
        # Определяем тип апдейта
        if "callback_query" in self.update:
            self.callback_query = self.update["callback_query"]
            self.message = self.callback_query.get("message")
            self.callback_data = self.callback_query.get("data")
            self.from_user = self.callback_query.get("from")
        else:
            self.message = self.update.get("message") or self.update.get("edited_message")
            self.callback_query = None
            self.callback_data = None
            self.from_user = self.message.get("from") if self.message else None

        # Извлекаем общие поля
        if self.message:
            self.chat_id = self.message["chat"]["id"]
            self.message_id = self.message["message_id"]
            self.text = self.message.get("text", "")
            self.voice = self.message.get("voice")
            self.photo = self.message.get("photo")
            self.video = self.message.get("video")
            self.audio = self.message.get("audio")
            self.sticker = self.message.get("sticker")
            self.animation = self.message.get("animation")
            self.document = self.message.get("document")
            self.checklist = self.message.get("checklist")
            self.checklist_tasks_done = self.message.get("checklist_tasks_done")

            # Извлекаем команду если есть
            entities = self.message.get("entities", [])
            self.command = None
            for entity in entities:
                if entity.get("type") == "bot_command":
                    offset = entity.get("offset", 0)
                    length = entity.get("length", 0)
                    self.command = self.text[offset:offset + length]
                    break
        else:
            self.chat_id = None
            self.message_id = None
            self.text = ""
            self.voice = None
            self.photo = None
            self.video = None
            self.audio = None
            self.sticker = None
            self.animation = None
            self.document = None
            self.checklist = None
            self.checklist_tasks_done = None
            self.command = None

    async def reply(
            self,
            text: str,
            reply_markup: Optional[dict] = None,
            parse_mode: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Отвечает на текущее сообщение (с reply).
        
        Args:
            text: Текст ответа
            reply_markup: Клавиатура (можно использовать InlineKeyboard.build())
            parse_mode: Режим парсинга (HTML, Markdown)
        
        Returns:
            Ответ от Telegram API
        """
        if not self.chat_id or not self.message_id:
            raise ValueError("Cannot reply: chat_id or message_id is missing")

        return await send_message(
            self.bot.token,
            self.chat_id,
            text,
            reply_to_message_id=self.message_id,
            reply_markup=reply_markup,
            parse_mode=parse_mode or self.bot.parse_mode,
        )

    async def send(
            self,
            text: str,
            reply_markup: Optional[dict] = None,
            parse_mode: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Отправляет новое сообщение (без reply).
        
        Args:
            text: Текст сообщения
            reply_markup: Клавиатура
            parse_mode: Режим парсинга
        
        Returns:
            Ответ от Telegram API
        """
        if not self.chat_id:
            raise ValueError("Cannot send: chat_id is missing")

        return await send_message(
            self.bot.token,
            self.chat_id,
            text,
            reply_markup=reply_markup,
            parse_mode=parse_mode or self.bot.parse_mode,
        )

    async def answer_callback(
            self,
            text: Optional[str] = None,
            show_alert: bool = False,
    ) -> dict[str, Any]:
        """
        Отвечает на callback query (убирает "часики" на кнопке).
        
        Args:
            text: Текст уведомления
            show_alert: Показать как alert
        
        Returns:
            Ответ от Telegram API
        """
        if not self.callback_query:
            raise ValueError("Cannot answer callback: no callback_query in update")

        return await answer_callback_query(
            self.bot.token,
            self.callback_query["id"],
            text,
            show_alert,
        )

    async def edit_message(
            self,
            text: str,
            reply_markup: Optional[dict] = None,
            parse_mode: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Редактирует текущее сообщение (обычно используется в callback handlers).
        
        Args:
            text: Новый текст
            reply_markup: Обновленная клавиатура
            parse_mode: Режим парсинга
        
        Returns:
            Ответ от Telegram API
        """
        if not self.chat_id or not self.message_id:
            raise ValueError("Cannot edit message: chat_id or message_id is missing")

        return await edit_message_text(
            self.bot.token,
            self.chat_id,
            self.message_id,
            text,
            reply_markup=reply_markup,
            parse_mode=parse_mode or self.bot.parse_mode,
        )

    async def send_photo(self, photo: str, caption: Optional[str] = None,
                         reply_markup: Optional[dict] = None, parse_mode: Optional[str] = None) -> dict[str, Any]:
        if not self.chat_id:
            raise ValueError("Cannot send: chat_id is missing")
        return await send_photo(self.bot.token, self.chat_id, photo, caption, None,
                                reply_markup, parse_mode or self.bot.parse_mode)

    async def send_video(self, video: str, caption: Optional[str] = None,
                         reply_markup: Optional[dict] = None, parse_mode: Optional[str] = None) -> dict[str, Any]:
        if not self.chat_id:
            raise ValueError("Cannot send: chat_id is missing")
        return await send_video(self.bot.token, self.chat_id, video, caption, None,
                                reply_markup, parse_mode or self.bot.parse_mode)

    async def send_animation(self, animation: str, caption: Optional[str] = None,
                             reply_markup: Optional[dict] = None, parse_mode: Optional[str] = None) -> dict[str, Any]:
        if not self.chat_id:
            raise ValueError("Cannot send: chat_id is missing")
        return await send_animation(self.bot.token, self.chat_id, animation, caption, None,
                                    reply_markup, parse_mode or self.bot.parse_mode)

    async def send_sticker(self, sticker: str, reply_markup: Optional[dict] = None) -> dict[str, Any]:
        if not self.chat_id:
            raise ValueError("Cannot send: chat_id is missing")
        return await send_sticker(self.bot.token, self.chat_id, sticker, None, reply_markup)

    async def send_voice(self, voice: str, caption: Optional[str] = None,
                         reply_markup: Optional[dict] = None, parse_mode: Optional[str] = None) -> dict[str, Any]:
        if not self.chat_id:
            raise ValueError("Cannot send: chat_id is missing")
        return await send_voice(self.bot.token, self.chat_id, voice, caption, None,
                                reply_markup, parse_mode or self.bot.parse_mode)

    async def send_audio(self, audio: str, caption: Optional[str] = None,
                         reply_markup: Optional[dict] = None, parse_mode: Optional[str] = None,
                         title: Optional[str] = None, performer: Optional[str] = None) -> dict[str, Any]:
        if not self.chat_id:
            raise ValueError("Cannot send: chat_id is missing")
        return await send_audio(self.bot.token, self.chat_id, audio, caption, None,
                                reply_markup, parse_mode or self.bot.parse_mode, title, performer)

    async def send_document(self, document: str, caption: Optional[str] = None,
                            reply_markup: Optional[dict] = None, parse_mode: Optional[str] = None) -> dict[str, Any]:
        if not self.chat_id:
            raise ValueError("Cannot send: chat_id is missing")
        return await send_document(self.bot.token, self.chat_id, document, caption, None,
                                   reply_markup, parse_mode or self.bot.parse_mode)
