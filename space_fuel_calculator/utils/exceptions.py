"""
Пользовательские исключения для калькулятора топлива.
"""


class FuelCalculationError(Exception):
    """Базовый класс для ошибок расчета топлива."""
    pass


class InvalidInputError(FuelCalculationError):
    """Некорректные входные параметры."""
    pass


class PhysicsViolationError(FuelCalculationError):
    """Нарушение физических законов."""
    pass


class DataFormatError(FuelCalculationError):
    """Ошибки формата данных."""
    pass


class TrajectoryCalculationError(FuelCalculationError):
    """Ошибки расчета траектории."""
    pass


class EngineConfigurationError(FuelCalculationError):
    """Ошибки конфигурации двигателя."""
    pass