"""
Модели миссии и результатов расчетов топлива.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional
import json

from .planet import Planet
from .engine import Engine, engine_from_dict


@dataclass
class FuelResult:
    """
    Результаты расчета топлива для космической миссии.
    
    Attributes:
        outbound_fuel: Топливо для полета туда в кг
        return_fuel: Топливо для обратного полета в кг (может быть None для односторонних миссий)
        total_fuel: Общее количество топлива в кг
        delta_v_outbound: Дельта-V для полета туда в м/с
        delta_v_return: Дельта-V для обратного полета в м/с (может быть None)
        total_delta_v: Общая дельта-V в м/с
        engine_used: Использованный двигатель
        trajectory_type: Тип траектории ("direct", "hohmann", "gravity_assist")
    """
    outbound_fuel: float  # kg
    return_fuel: Optional[float]  # kg
    total_fuel: float  # kg
    delta_v_outbound: float  # m/s
    delta_v_return: Optional[float]  # m/s
    total_delta_v: float  # m/s
    engine_used: Engine
    trajectory_type: str
    
    def __post_init__(self):
        """Валидация результатов расчета."""
        if self.outbound_fuel < 0:
            raise ValueError(f"Топливо для полета туда не может быть отрицательным: {self.outbound_fuel}")
        if self.return_fuel is not None and self.return_fuel < 0:
            raise ValueError(f"Топливо для обратного полета не может быть отрицательным: {self.return_fuel}")
        if self.total_fuel < 0:
            raise ValueError(f"Общее топливо не может быть отрицательным: {self.total_fuel}")
        if self.delta_v_outbound < 0:
            raise ValueError(f"Дельта-V для полета туда не может быть отрицательной: {self.delta_v_outbound}")
        if self.delta_v_return is not None and self.delta_v_return < 0:
            raise ValueError(f"Дельта-V для обратного полета не может быть отрицательной: {self.delta_v_return}")
        if self.total_delta_v < 0:
            raise ValueError(f"Общая дельта-V не может быть отрицательной: {self.total_delta_v}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразование в словарь для сериализации."""
        return {
            'outbound_fuel': self.outbound_fuel,
            'return_fuel': self.return_fuel,
            'total_fuel': self.total_fuel,
            'delta_v_outbound': self.delta_v_outbound,
            'delta_v_return': self.delta_v_return,
            'total_delta_v': self.total_delta_v,
            'engine_used': self.engine_used.to_dict(),
            'trajectory_type': self.trajectory_type
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FuelResult':
        """Создание экземпляра из словаря."""
        return cls(
            outbound_fuel=data['outbound_fuel'],
            return_fuel=data['return_fuel'],
            total_fuel=data['total_fuel'],
            delta_v_outbound=data['delta_v_outbound'],
            delta_v_return=data['delta_v_return'],
            total_delta_v=data['total_delta_v'],
            engine_used=engine_from_dict(data['engine_used']),
            trajectory_type=data['trajectory_type']
        )
    
    def to_json(self) -> str:
        """Сериализация в JSON."""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'FuelResult':
        """Десериализация из JSON."""
        data = json.loads(json_str)
        return cls.from_dict(data)


@dataclass
class Mission:
    """
    Конфигурация космической миссии.
    
    Attributes:
        id: Уникальный идентификатор миссии
        name: Название миссии
        destination: Планета назначения
        payload_mass: Масса полезной нагрузки в кг
        engine: Используемый двигатель
        use_gravity_assists: Использовать ли гравитационные маневры
        created_at: Время создания миссии
        fuel_requirements: Результаты расчета топлива (может быть None до расчета)
    """
    id: str
    name: str
    destination: Planet
    payload_mass: float  # kg
    engine: Engine
    use_gravity_assists: bool
    created_at: datetime
    fuel_requirements: Optional[FuelResult] = None
    
    def __post_init__(self):
        """Валидация параметров миссии."""
        if not self.id:
            raise ValueError("ID миссии не может быть пустым")
        if not self.name:
            raise ValueError("Название миссии не может быть пустым")
        if self.payload_mass < 0:
            raise ValueError(f"Масса полезной нагрузки не может быть отрицательной: {self.payload_mass}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразование в словарь для сериализации."""
        return {
            'id': self.id,
            'name': self.name,
            'destination': self.destination.to_dict(),
            'payload_mass': self.payload_mass,
            'engine': self.engine.to_dict(),
            'use_gravity_assists': self.use_gravity_assists,
            'created_at': self.created_at.isoformat(),
            'fuel_requirements': self.fuel_requirements.to_dict() if self.fuel_requirements else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Mission':
        """Создание экземпляра из словаря."""
        return cls(
            id=data['id'],
            name=data['name'],
            destination=Planet.from_dict(data['destination']),
            payload_mass=data['payload_mass'],
            engine=engine_from_dict(data['engine']),
            use_gravity_assists=data['use_gravity_assists'],
            created_at=datetime.fromisoformat(data['created_at']),
            fuel_requirements=FuelResult.from_dict(data['fuel_requirements']) if data['fuel_requirements'] else None
        )
    
    def to_json(self) -> str:
        """Сериализация в JSON."""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Mission':
        """Десериализация из JSON."""
        data = json.loads(json_str)
        return cls.from_dict(data)