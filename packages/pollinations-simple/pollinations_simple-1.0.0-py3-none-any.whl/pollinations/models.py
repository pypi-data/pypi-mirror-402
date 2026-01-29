"""
Модели данных для работы с Pollinations AI
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any


@dataclass
class Message:
    """Сообщение в чате"""
    role: str  # "user", "assistant", "system"
    content: str
    
    def to_dict(self) -> Dict[str, str]:
        return {"role": self.role, "content": self.content}


@dataclass
class Model:
    """Информация о модели"""
    name: str
    description: str
    tier: str
    vision: bool = False
    audio: bool = False
    tools: bool = False
    reasoning: bool = False
    aliases: List[str] = field(default_factory=list)
    input_modalities: List[str] = field(default_factory=list)
    output_modalities: List[str] = field(default_factory=list)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Model":
        return cls(
            name=data.get("name", ""),
            description=data.get("description", ""),
            tier=data.get("tier", "anonymous"),
            vision=data.get("vision", False),
            audio=data.get("audio", False),
            tools=data.get("tools", False),
            reasoning=data.get("reasoning", False),
            aliases=data.get("aliases", []),
            input_modalities=data.get("input_modalities", []),
            output_modalities=data.get("output_modalities", []),
        )


@dataclass
class ChatResponse:
    """Ответ от API чата"""
    content: str
    model: str
    finish_reason: str = "stop"
    usage: Optional[Dict[str, int]] = None
    raw_response: Optional[Dict[str, Any]] = None
    
    @property
    def text(self) -> str:
        """Псевдоним для content"""
        return self.content
