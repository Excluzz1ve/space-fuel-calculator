"""
Тесты для проверки корректности настройки проекта.
"""

import pytest
import sys
from pathlib import Path

# Добавляем корневую директорию проекта в путь
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import space_fuel_calculator
from space_fuel_calculator.utils import constants, exceptions
from space_fuel_calculator import main


class TestProjectSetup:
    """Тесты настройки проекта."""
    
    def test_package_import(self):
        """Тест импорта основного пакета."""
        assert space_fuel_calculator.__version__ == "1.0.0"
        assert space_fuel_calculator.__author__ == "Space Mission Engineering Team"
    
    def test_constants_import(self):
        """Тест импорта констант."""
        assert constants.GRAVITATIONAL_CONSTANT > 0
        assert constants.STANDARD_GRAVITY > 0
        assert constants.EARTH_MASS > 0
    
    def test_exceptions_import(self):
        """Тест импорта исключений."""
        assert issubclass(exceptions.FuelCalculationError, Exception)
        assert issubclass(exceptions.InvalidInputError, exceptions.FuelCalculationError)
        assert issubclass(exceptions.PhysicsViolationError, exceptions.FuelCalculationError)
    
    def test_main_module_import(self):
        """Тест импорта главного модуля."""
        assert callable(main.main)
        assert callable(main.create_parser)
    
    def test_main_function_with_help(self):
        """Тест функции main с аргументом --help."""
        with pytest.raises(SystemExit) as exc_info:
            main.main(["--help"])
        assert exc_info.value.code == 0
    
    def test_main_function_with_version(self):
        """Тест функции main с аргументом --version."""
        with pytest.raises(SystemExit) as exc_info:
            main.main(["--version"])
        assert exc_info.value.code == 0