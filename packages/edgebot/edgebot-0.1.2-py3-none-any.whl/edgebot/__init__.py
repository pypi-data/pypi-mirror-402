"""
EdgeBot - SDK для создания Telegram ботов на Cloudflare Workers
"""

__version__ = "0.1.2"

from .bot import Bot
from .context import Context
from .keyboard import InlineKeyboard
from .utils import sleep

__all__ = ["Bot", "Context", "InlineKeyboard", "sleep", "__version__"]