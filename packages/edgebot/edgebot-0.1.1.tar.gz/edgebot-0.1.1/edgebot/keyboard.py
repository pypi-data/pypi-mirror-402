"""
Классы для создания клавиатур (inline и обычных)
"""

from typing import Any, Optional


class InlineKeyboard:
    """
    Билдер для создания inline-клавиатур под сообщениями.
    
    Пример использования:
        keyboard = InlineKeyboard()
        keyboard.button('Кнопка 1', callback_data='btn1')
        keyboard.button('Кнопка 2', callback_data='btn2')
        keyboard.row()
        keyboard.button('Ссылка', url='https://example.com')
        
        await ctx.reply('Выбери действие:', reply_markup=keyboard.build())
    """
    
    def __init__(self):
        self.keyboard: list[list[dict[str, Any]]] = []
        self.current_row: list[dict[str, Any]] = []
    
    def button(
        self,
        text: str,
        callback_data: Optional[str] = None,
        url: Optional[str] = None,
    ) -> "InlineKeyboard":
        """
        Добавляет кнопку в текущий ряд.
        
        Args:
            text: Текст на кнопке
            callback_data: Данные для callback (взаимоисключающее с url)
            url: Ссылка (взаимоисключающее с callback_data)
        
        Returns:
            self для chaining
        """
        btn: dict[str, Any] = {"text": text}
        
        if callback_data:
            btn["callback_data"] = callback_data
        elif url:
            btn["url"] = url
        else:
            raise ValueError("Button must have either callback_data or url")
        
        self.current_row.append(btn)
        return self
    
    def row(self) -> "InlineKeyboard":
        """
        Завершает текущий ряд и начинает новый.
        
        Returns:
            self для chaining
        """
        if self.current_row:
            self.keyboard.append(self.current_row)
            self.current_row = []
        return self
    
    def build(self) -> dict[str, Any]:
        """
        Возвращает готовый reply_markup для отправки в Telegram API.
        
        Returns:
            Словарь с inline_keyboard
        """
        # Добавляем незавершенный ряд, если есть
        if self.current_row:
            self.keyboard.append(self.current_row)
            self.current_row = []
        
        return {"inline_keyboard": self.keyboard}

