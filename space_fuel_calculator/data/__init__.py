"""
Модуль данных для калькулятора топлива.

Содержит данные о планетах, двигателях и утилиты для работы с данными.
"""

from .planets import get_all_planets, get_destination_planets, get_planet_by_key
from .engines import get_all_engines, get_engine_by_key, get_engine_categories

__all__ = [
    'get_all_planets', 'get_destination_planets', 'get_planet_by_key',
    'get_all_engines', 'get_engine_by_key', 'get_engine_categories'
]