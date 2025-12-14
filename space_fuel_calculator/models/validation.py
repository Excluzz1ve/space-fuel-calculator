"""
Модели данных для валидации миссий.

Содержит классы для валидации расчетов против реальных данных NASA/ESA.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum


class ConfidenceLevel(Enum):
    """Уровень доверия к валидации."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class MissionType(Enum):
    """Тип космической миссии."""
    FLYBY = "flyby"
    ORBITER = "orbiter"
    LANDER = "lander"
    SAMPLE_RETURN = "sample_return"
    CREWED = "crewed"


class TrajectoryType(Enum):
    """Тип траектории."""
    DIRECT = "direct"
    GRAVITY_ASSIST = "gravity_assist"
    COMPLEX = "complex"
    HOHMANN = "hohmann"


@dataclass
class ValidationResult:
    """
    Результат валидации расчетов против реальных данных.
    
    Attributes:
        valid: Прошла ли валидация успешно
        confidence: Уровень доверия к результату
        reference_mission: Название референсной миссии (если есть)
        note: Дополнительные комментарии
        sources: Список источников данных
        deviation_percent: Отклонение от референсных данных в процентах
    """
    valid: bool
    confidence: ConfidenceLevel
    reference_mission: Optional[str] = None
    note: str = ""
    sources: List[str] = field(default_factory=list)
    deviation_percent: Optional[float] = None
    
    def __post_init__(self):
        """Валидация после инициализации."""
        if isinstance(self.confidence, str):
            self.confidence = ConfidenceLevel(self.confidence)


@dataclass
class MissionReference:
    """
    Референсные данные реальной космической миссии.
    
    Attributes:
        name: Название миссии
        agency: Космическое агентство
        year: Год запуска
        delta_v: Дельта-V миссии в м/с
        mission_type: Тип миссии
        trajectory_type: Тип траектории
        sources: Список источников данных
        target_planet: Планета назначения
        notes: Дополнительные заметки
    """
    name: str
    agency: str
    year: int
    delta_v: float  # м/с
    mission_type: MissionType
    trajectory_type: TrajectoryType
    target_planet: str
    sources: List[str] = field(default_factory=list)
    notes: str = ""
    
    def __post_init__(self):
        """Валидация после инициализации."""
        if isinstance(self.mission_type, str):
            self.mission_type = MissionType(self.mission_type)
        if isinstance(self.trajectory_type, str):
            self.trajectory_type = TrajectoryType(self.trajectory_type)
        
        if self.delta_v < 0:
            raise ValueError(f"Дельта-V не может быть отрицательной: {self.delta_v}")
        
        if self.year < 1957:  # Начало космической эры
            raise ValueError(f"Год запуска не может быть раньше 1957: {self.year}")
        
        if not self.name.strip():
            raise ValueError("Название миссии не может быть пустым")
        
        if not self.agency.strip():
            raise ValueError("Название агентства не может быть пустым")
        
        if not self.target_planet.strip():
            raise ValueError("Планета назначения не может быть пустой")


@dataclass
class ValidationConfig:
    """
    Конфигурация для валидации миссий.
    
    Attributes:
        tolerance_percent: Допустимое отклонение в процентах
        min_confidence_threshold: Минимальный порог доверия
        require_sources: Требовать ли источники данных
        max_deviation_warning: Максимальное отклонение для предупреждения
    """
    tolerance_percent: float = 15.0
    min_confidence_threshold: ConfidenceLevel = ConfidenceLevel.MEDIUM
    require_sources: bool = True
    max_deviation_warning: float = 25.0
    
    def __post_init__(self):
        """Валидация после инициализации."""
        if isinstance(self.min_confidence_threshold, str):
            self.min_confidence_threshold = ConfidenceLevel(self.min_confidence_threshold)
        
        if self.tolerance_percent < 0 or self.tolerance_percent > 100:
            raise ValueError(f"Допуск должен быть от 0 до 100%: {self.tolerance_percent}")
        
        if self.max_deviation_warning < 0:
            raise ValueError(f"Максимальное отклонение не может быть отрицательным: {self.max_deviation_warning}")