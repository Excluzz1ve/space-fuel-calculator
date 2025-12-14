"""
Модели двигателей для космических аппаратов.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any, Union
import json


class EngineType(Enum):
    """Типы ракетных двигателей."""
    CHEMICAL = "chemical"
    ION = "ion"
    NUCLEAR = "nuclear"


@dataclass
class Engine(ABC):
    """
    Абстрактный базовый класс для ракетных двигателей.
    
    Attributes:
        name: Название двигателя
        specific_impulse: Удельный импульс в секундах
        thrust: Тяга в Ньютонах
    """
    name: str
    specific_impulse: float  # seconds
    thrust: float  # Newtons
    
    def __post_init__(self):
        """Валидация параметров двигателя после инициализации."""
        if not self.name or not isinstance(self.name, str):
            raise ValueError(f"Название двигателя должно быть непустой строкой, получено: {self.name}")
        if self.specific_impulse <= 0:
            raise ValueError(f"Удельный импульс должен быть положительным, получено: {self.specific_impulse}")
        if self.thrust <= 0:
            raise ValueError(f"Тяга должна быть положительной, получено: {self.thrust}")
    
    @property
    @abstractmethod
    def engine_type(self) -> EngineType:
        """Тип двигателя."""
        pass
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Преобразование в словарь для сериализации."""
        pass
    
    @classmethod
    @abstractmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Engine':
        """Создание экземпляра из словаря."""
        pass
    
    def to_json(self) -> str:
        """Сериализация в JSON."""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


@dataclass
class ChemicalEngine(Engine):
    """
    Химический ракетный двигатель.
    
    Attributes:
        fuel_type: Тип топлива (например, "RP-1/LOX", "LH2/LOX")
    """
    fuel_type: str
    
    @property
    def engine_type(self) -> EngineType:
        return EngineType.CHEMICAL
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразование в словарь для сериализации."""
        return {
            'type': 'chemical',
            'name': self.name,
            'specific_impulse': self.specific_impulse,
            'thrust': self.thrust,
            'fuel_type': self.fuel_type
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChemicalEngine':
        """Создание экземпляра из словаря."""
        return cls(
            name=data['name'],
            specific_impulse=data['specific_impulse'],
            thrust=data['thrust'],
            fuel_type=data['fuel_type']
        )


@dataclass
class IonEngine(Engine):
    """
    Ионный двигатель.
    
    Attributes:
        power_consumption: Потребляемая мощность в Ваттах
    """
    power_consumption: float  # Watts
    
    def __post_init__(self):
        """Валидация параметров ионного двигателя."""
        super().__post_init__()
        if self.power_consumption <= 0:
            raise ValueError(f"Потребляемая мощность должна быть положительной, получено: {self.power_consumption}")
    
    @property
    def engine_type(self) -> EngineType:
        return EngineType.ION
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразование в словарь для сериализации."""
        return {
            'type': 'ion',
            'name': self.name,
            'specific_impulse': self.specific_impulse,
            'thrust': self.thrust,
            'power_consumption': self.power_consumption
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'IonEngine':
        """Создание экземпляра из словаря."""
        return cls(
            name=data['name'],
            specific_impulse=data['specific_impulse'],
            thrust=data['thrust'],
            power_consumption=data['power_consumption']
        )


@dataclass
class NuclearEngine(Engine):
    """
    Ядерный ракетный двигатель.
    
    Attributes:
        reactor_power: Мощность реактора в Ваттах
        propellant_type: Тип рабочего тела (например, "H2", "NH3")
    """
    reactor_power: float  # Watts
    propellant_type: str
    
    def __post_init__(self):
        """Валидация параметров ядерного двигателя."""
        super().__post_init__()
        if self.reactor_power <= 0:
            raise ValueError(f"Мощность реактора должна быть положительной, получено: {self.reactor_power}")
    
    @property
    def engine_type(self) -> EngineType:
        return EngineType.NUCLEAR
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразование в словарь для сериализации."""
        return {
            'type': 'nuclear',
            'name': self.name,
            'specific_impulse': self.specific_impulse,
            'thrust': self.thrust,
            'reactor_power': self.reactor_power,
            'propellant_type': self.propellant_type
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NuclearEngine':
        """Создание экземпляра из словаря."""
        return cls(
            name=data['name'],
            specific_impulse=data['specific_impulse'],
            thrust=data['thrust'],
            reactor_power=data['reactor_power'],
            propellant_type=data['propellant_type']
        )


def engine_from_dict(data: Dict[str, Any]) -> Engine:
    """
    Фабричная функция для создания двигателя из словаря.
    
    Args:
        data: Словарь с данными двигателя, должен содержать поле 'type'
        
    Returns:
        Экземпляр соответствующего класса двигателя
        
    Raises:
        ValueError: Если тип двигателя неизвестен
        TypeError: Если data не является словарем
    """
    if not isinstance(data, dict):
        raise TypeError(f"Данные двигателя должны быть словарем, получено: {type(data)}")
    
    engine_type = data.get('type')
    
    if engine_type == 'chemical':
        return ChemicalEngine.from_dict(data)
    elif engine_type == 'ion':
        return IonEngine.from_dict(data)
    elif engine_type == 'nuclear':
        return NuclearEngine.from_dict(data)
    else:
        raise ValueError(f"Неизвестный тип двигателя: {engine_type}")


def engine_from_json(json_str: str) -> Engine:
    """
    Десериализация двигателя из JSON.
    
    Args:
        json_str: JSON строка с данными двигателя
        
    Returns:
        Экземпляр соответствующего класса двигателя
    """
    data = json.loads(json_str)
    return engine_from_dict(data)