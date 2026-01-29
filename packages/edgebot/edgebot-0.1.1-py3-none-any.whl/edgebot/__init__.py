"""
EdgeBot - SDK для создания Telegram ботов на Cloudflare Workers
"""

__version__ = "0.1.1"

from edgebot.bot import Bot
from edgebot.context import Context
from edgebot.keyboard import InlineKeyboard
from edgebot.utils import sleep

__all__ = ["Bot", "Context", "InlineKeyboard", "sleep", "__version__"]