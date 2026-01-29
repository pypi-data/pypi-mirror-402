"""
Pollinations AI - Простая Python библиотека для работы с LLM моделями
"""

from .client import PollinationsClient, ask, chat
from .models import Message, ChatResponse, Model

__version__ = "1.0.0"
__all__ = ["PollinationsClient", "Message", "ChatResponse", "Model", "ask", "chat"]
