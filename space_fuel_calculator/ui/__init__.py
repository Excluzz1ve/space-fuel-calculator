"""
Пользовательский интерфейс для калькулятора топлива.

Содержит CLI интерфейс и утилиты для взаимодействия с пользователем.
"""

from .cli import run_cli, MissionCLI
from .formatter import ResultFormatter

__all__ = ['run_cli', 'MissionCLI', 'ResultFormatter']