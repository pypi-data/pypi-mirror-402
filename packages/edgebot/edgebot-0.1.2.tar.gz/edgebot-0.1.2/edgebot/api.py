"""
Низкоуровневые функции для работы с Telegram Bot API
"""

from json import dumps
from typing import Any, Optional
from pyodide.ffi import to_js  # type: ignore[attr-defined]
from .utils import fetch


async def _send_media(
        token: str,
        chat_id: int,
        method: str,
        media_field: str,
        media: str,
        caption: Optional[str] = None,
        reply_to_message_id: Optional[int] = None,
        reply_markup: Optional[dict] = None,
        parse_mode: Optional[str] = None,
        **kwargs: Any,
) -> dict[str, Any]:
    api_url = f"https://api.telegram.org/bot{token}/{method}"
    payload: dict[str, Any] = {"chat_id": chat_id, media_field: media}

    if caption:
        payload["caption"] = caption
    if reply_to_message_id:
        payload["reply_to_message_id"] = reply_to_message_id
    if reply_markup:
        payload["reply_markup"] = reply_markup
    if parse_mode:
        payload["parse_mode"] = parse_mode
    payload.update(kwargs)

    options = to_js({"method": "POST", "headers": {"Content-Type": "application/json"}, "body": dumps(payload)})
    resp = await fetch(api_url, options)

    if not resp.ok:
        err_text = await resp.text()
        print(f"[error] {method} failed: status={resp.status} body={err_text}")
        raise Exception(f"Telegram API error: {resp.status}")

    return await resp.json()


async def send_message(
    token: str,
    chat_id: int,
    text: str,
    reply_to_message_id: Optional[int] = None,
    reply_markup: Optional[dict] = None,
    parse_mode: Optional[str] = None,
) -> dict[str, Any]:
    """
    Отправляет текстовое сообщение в чат.
    
    Args:
        token: Токен бота
        chat_id: ID чата
        text: Текст сообщения
        reply_to_message_id: ID сообщения для ответа (опционально)
        reply_markup: Клавиатура (inline или обычная)
        parse_mode: Режим парсинга (HTML, Markdown и т.д.)
    
    Returns:
        Ответ от Telegram API
    """
    api_url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    payload: dict[str, Any] = {
        "chat_id": chat_id,
        "text": text,
    }
    
    if reply_to_message_id:
        payload["reply_to_message_id"] = reply_to_message_id
    
    if reply_markup:
        payload["reply_markup"] = reply_markup
    
    if parse_mode:
        payload["parse_mode"] = parse_mode
    
    options = to_js({
        "method": "POST",
        "headers": {"Content-Type": "application/json"},
        "body": dumps(payload),
    })
    
    resp = await fetch(api_url, options)
    
    if not resp.ok:
        err_text = await resp.text()
        print(f"[error] sendMessage failed: status={resp.status} body={err_text}")
        raise Exception(f"Telegram API error: {resp.status}")
    
    return await resp.json()


async def edit_message_text(
    token: str,
    chat_id: int,
    message_id: int,
    text: str,
    reply_markup: Optional[dict] = None,
    parse_mode: Optional[str] = None,
) -> dict[str, Any]:
    """
    Редактирует текст существующего сообщения.
    
    Args:
        token: Токен бота
        chat_id: ID чата
        message_id: ID сообщения для редактирования
        text: Новый текст
        reply_markup: Обновленная клавиатура
        parse_mode: Режим парсинга
    
    Returns:
        Ответ от Telegram API
    """
    api_url = f"https://api.telegram.org/bot{token}/editMessageText"
    
    payload: dict[str, Any] = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
    }
    
    if reply_markup:
        payload["reply_markup"] = reply_markup
    
    if parse_mode:
        payload["parse_mode"] = parse_mode
    
    options = to_js({
        "method": "POST",
        "headers": {"Content-Type": "application/json"},
        "body": dumps(payload),
    })
    
    resp = await fetch(api_url, options)
    
    if not resp.ok:
        err_text = await resp.text()
        print(f"[error] editMessageText failed: status={resp.status} body={err_text}")
        raise Exception(f"Telegram API error: {resp.status}")
    
    return await resp.json()


async def answer_callback_query(
    token: str,
    callback_query_id: str,
    text: Optional[str] = None,
    show_alert: bool = False,
) -> dict[str, Any]:
    """
    Отвечает на callback query.
    
    Args:
        token: Токен бота
        callback_query_id: ID callback query
        text: Текст уведомления (опционально)
        show_alert: Показать как alert вместо уведомления
    
    Returns:
        Ответ от Telegram API
    """
    api_url = f"https://api.telegram.org/bot{token}/answerCallbackQuery"
    
    payload: dict[str, Any] = {
        "callback_query_id": callback_query_id,
    }
    
    if text:
        payload["text"] = text
    
    if show_alert:
        payload["show_alert"] = True
    
    options = to_js({
        "method": "POST",
        "headers": {"Content-Type": "application/json"},
        "body": dumps(payload),
    })
    
    resp = await fetch(api_url, options)
    
    if not resp.ok:
        err_text = await resp.text()
        print(f"[error] answerCallbackQuery failed: status={resp.status} body={err_text}")
        raise Exception(f"Telegram API error: {resp.status}")
    
    return await resp.json()


async def get_file(token: str, file_id: str) -> dict[str, Any]:
    """
    Получает информацию о файле (для загрузки голосовых, фото и т.д.).
    
    Args:
        token: Токен бота
        file_id: ID файла в Telegram
    
    Returns:
        Информация о файле с file_path для загрузки
    """
    api_url = f"https://api.telegram.org/bot{token}/getFile"
    
    payload = {"file_id": file_id}
    
    options = to_js({
        "method": "POST",
        "headers": {"Content-Type": "application/json"},
        "body": dumps(payload),
    })
    
    resp = await fetch(api_url, options)
    
    if not resp.ok:
        err_text = await resp.text()
        print(f"[error] getFile failed: status={resp.status} body={err_text}")
        raise Exception(f"Telegram API error: {resp.status}")
    
    return await resp.json()


async def send_photo(token: str, chat_id: int, photo: str, caption: Optional[str] = None,
                     reply_to_message_id: Optional[int] = None, reply_markup: Optional[dict] = None,
                     parse_mode: Optional[str] = None) -> dict[str, Any]:
    return await _send_media(token, chat_id, "sendPhoto", "photo", photo, caption,
                             reply_to_message_id, reply_markup, parse_mode)


async def send_video(token: str, chat_id: int, video: str, caption: Optional[str] = None,
                     reply_to_message_id: Optional[int] = None, reply_markup: Optional[dict] = None,
                     parse_mode: Optional[str] = None) -> dict[str, Any]:
    return await _send_media(token, chat_id, "sendVideo", "video", video, caption,
                             reply_to_message_id, reply_markup, parse_mode)


async def send_animation(token: str, chat_id: int, animation: str, caption: Optional[str] = None,
                         reply_to_message_id: Optional[int] = None, reply_markup: Optional[dict] = None,
                         parse_mode: Optional[str] = None) -> dict[str, Any]:
    return await _send_media(token, chat_id, "sendAnimation", "animation", animation, caption,
                             reply_to_message_id, reply_markup, parse_mode)


async def send_sticker(token: str, chat_id: int, sticker: str,
                       reply_to_message_id: Optional[int] = None,
                       reply_markup: Optional[dict] = None) -> dict[str, Any]:
    return await _send_media(token, chat_id, "sendSticker", "sticker", sticker,
                             None, reply_to_message_id, reply_markup, None)


async def send_voice(token: str, chat_id: int, voice: str, caption: Optional[str] = None,
                     reply_to_message_id: Optional[int] = None, reply_markup: Optional[dict] = None,
                     parse_mode: Optional[str] = None) -> dict[str, Any]:
    return await _send_media(token, chat_id, "sendVoice", "voice", voice, caption,
                             reply_to_message_id, reply_markup, parse_mode)


async def send_audio(token: str, chat_id: int, audio: str, caption: Optional[str] = None,
                     reply_to_message_id: Optional[int] = None, reply_markup: Optional[dict] = None,
                     parse_mode: Optional[str] = None, title: Optional[str] = None,
                     performer: Optional[str] = None) -> dict[str, Any]:
    kwargs = {}
    if title:
        kwargs["title"] = title
    if performer:
        kwargs["performer"] = performer
    return await _send_media(token, chat_id, "sendAudio", "audio", audio, caption,
                             reply_to_message_id, reply_markup, parse_mode, **kwargs)


async def send_document(token: str, chat_id: int, document: str, caption: Optional[str] = None,
                        reply_to_message_id: Optional[int] = None, reply_markup: Optional[dict] = None,
                        parse_mode: Optional[str] = None) -> dict[str, Any]:
    return await _send_media(token, chat_id, "sendDocument", "document", document, caption,
                             reply_to_message_id, reply_markup, parse_mode)
