"""
Модель планеты с орбитальными параметрами.
"""
from dataclasses import dataclass
from typing import Dict, Any
import json


@dataclass
class Planet:
    """
    Класс данных для планеты с орбитальными и физическими параметрами.
    
    Attributes:
        name: Название планеты
        mass: Масса планеты в килограммах
        radius: Радиус планеты в метрах
        orbital_radius: Орбитальный радиус от Солнца в метрах
        escape_velocity: Скорость убегания в м/с
    """
    name: str
    mass: float  # kg
    radius: float  # m
    orbital_radius: float  # m from Sun
    escape_velocity: float  # m/s
    
    def __post_init__(self):
        """Валидация параметров планеты после инициализации."""
        if not self.name or not isinstance(self.name, str):
            raise ValueError(f"Название планеты должно быть непустой строкой, получено: {self.name}")
        if self.mass <= 0:
            raise ValueError(f"Масса планеты должна быть положительной, получено: {self.mass}")
        if self.radius <= 0:
            raise ValueError(f"Радиус планеты должен быть положительным, получено: {self.radius}")
        if self.orbital_radius <= 0:
            raise ValueError(f"Орбитальный радиус должен быть положительным, получено: {self.orbital_radius}")
        if self.escape_velocity <= 0:
            raise ValueError(f"Скорость убегания должна быть положительной, получено: {self.escape_velocity}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразование в словарь для сериализации."""
        return {
            'name': self.name,
            'mass': self.mass,
            'radius': self.radius,
            'orbital_radius': self.orbital_radius,
            'escape_velocity': self.escape_velocity
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Planet':
        """Создание экземпляра из словаря."""
        return cls(
            name=data['name'],
            mass=data['mass'],
            radius=data['radius'],
            orbital_radius=data['orbital_radius'],
            escape_velocity=data['escape_velocity']
        )
    
    def to_json(self) -> str:
        """Сериализация в JSON."""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Planet':
        """Десериализация из JSON."""
        data = json.loads(json_str)
        return cls.from_dict(data)