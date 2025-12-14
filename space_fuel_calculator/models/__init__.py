"""
Модели данных для калькулятора топлива.

Содержит классы для планет, двигателей, миссий и результатов расчетов.
"""

from .planet import Planet
from .engine import (
    Engine, 
    EngineType, 
    ChemicalEngine, 
    IonEngine, 
    NuclearEngine,
    engine_from_dict,
    engine_from_json
)
from .mission import Mission, FuelResult

__all__ = [
    'Planet',
    'Engine',
    'EngineType',
    'ChemicalEngine',
    'IonEngine', 
    'NuclearEngine',
    'engine_from_dict',
    'engine_from_json',
    'Mission',
    'FuelResult'
]