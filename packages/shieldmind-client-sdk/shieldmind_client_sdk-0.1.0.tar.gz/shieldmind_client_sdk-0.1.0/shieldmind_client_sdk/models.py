"""
Модели данных для Shieldmind Client SDK
"""
from typing import Optional, List, Dict, Any
from dataclasses import dataclass


@dataclass
class Threat:
    """Модель угрозы"""
    type: str
    severity: str  # 'low' | 'medium' | 'high' | 'critical'
    description: str
    foundIn: str  # 'request' | 'response'
    details: Optional[Dict[str, Any]] = None

    @classmethod
    def from_dict(cls, data: dict) -> "Threat":
        return cls(
            type=data.get("type", ""),
            severity=data.get("severity", "low"),
            description=data.get("description", ""),
            foundIn=data.get("foundIn", "request"),
            details=data.get("details"),
        )


@dataclass
class ValidationResult:
    """Результат валидации запроса"""
    isSafe: bool
    threats: List[Threat]
    score: int  # 0-100, где 100 - полностью безопасно
    remaining: Optional[int] = None
    limit: Optional[int] = None
    window: Optional[str] = None
    similarPrompts: Optional[List[Dict[str, Any]]] = None

    @classmethod
    def from_dict(cls, data: dict) -> "ValidationResult":
        threats_data = data.get("threats", [])
        threats = [Threat.from_dict(t) if isinstance(t, dict) else t for t in threats_data]
        
        return cls(
            isSafe=data.get("isSafe", True),
            threats=threats,
            score=data.get("score", 100),
            remaining=data.get("remaining"),
            limit=data.get("limit"),
            window=data.get("window"),
            similarPrompts=data.get("similarPrompts"),
        )


@dataclass
class RemainingChecks:
    """Информация об оставшихся проверках"""
    remaining: int
    limit: int
    window: str  # 'day' | 'second'

    @classmethod
    def from_dict(cls, data: dict) -> "RemainingChecks":
        return cls(
            remaining=data.get("remaining", 0),
            limit=data.get("limit", 0),
            window=data.get("window", "day"),
        )
