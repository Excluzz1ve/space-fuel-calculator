"""
Property-based тесты для валидации структуры данных.

**Feature: space-fuel-calculator, Property 18: Валидация структуры данных**
**Validates: Requirements 5.5**
"""
import pytest
from hypothesis import given, strategies as st
import json
from datetime import datetime, timezone

from space_fuel_calculator.models import (
    Planet, 
    ChemicalEngine, 
    IonEngine, 
    NuclearEngine,
    Mission, 
    FuelResult,
    engine_from_dict
)


class TestDataValidation:
    """Тесты валидации структуры данных."""
    
    @given(st.dictionaries(
        keys=st.sampled_from(['name', 'mass', 'radius', 'orbital_radius', 'escape_velocity']),
        values=st.one_of(
            st.text(),
            st.floats(allow_nan=True, allow_infinity=True),
            st.integers(),
            st.none()
        ),
        min_size=0,
        max_size=10
    ))
    def test_planet_validation_rejects_invalid_data(self, invalid_data):
        """
        **Feature: space-fuel-calculator, Property 18: Валидация структуры данных**
        **Validates: Requirements 5.5**
        
        Для любого некорректного словаря данных планеты, парсинг должен 
        валидировать структуру и отклонять некорректные файлы.
        """
        # Проверяем, что некорректные данные отклоняются
        try:
            planet = Planet.from_dict(invalid_data)
            # Если создание прошло успешно, проверяем, что данные действительно валидны
            assert isinstance(planet.name, str) and len(planet.name) > 0
            assert isinstance(planet.mass, (int, float)) and planet.mass > 0
            assert isinstance(planet.radius, (int, float)) and planet.radius > 0
            assert isinstance(planet.orbital_radius, (int, float)) and planet.orbital_radius > 0
            assert isinstance(planet.escape_velocity, (int, float)) and planet.escape_velocity > 0
        except (KeyError, TypeError, ValueError):
            # Ожидаемое поведение для некорректных данных
            pass
    
    @given(st.dictionaries(
        keys=st.sampled_from(['type', 'name', 'specific_impulse', 'thrust', 'fuel_type', 'power_consumption', 'reactor_power', 'propellant_type']),
        values=st.one_of(
            st.text(),
            st.floats(allow_nan=True, allow_infinity=True),
            st.integers(),
            st.none()
        ),
        min_size=0,
        max_size=10
    ))
    def test_engine_validation_rejects_invalid_data(self, invalid_data):
        """
        **Feature: space-fuel-calculator, Property 18: Валидация структуры данных**
        **Validates: Requirements 5.5**
        
        Для любого некорректного словаря данных двигателя, парсинг должен 
        валидировать структуру и отклонять некорректные файлы.
        """
        # Проверяем, что некорректные данные отклоняются
        try:
            engine = engine_from_dict(invalid_data)
            # Если создание прошло успешно, проверяем, что данные действительно валидны
            assert isinstance(engine.name, str) and len(engine.name) > 0
            assert isinstance(engine.specific_impulse, (int, float)) and engine.specific_impulse > 0
            assert isinstance(engine.thrust, (int, float)) and engine.thrust > 0
        except (KeyError, TypeError, ValueError):
            # Ожидаемое поведение для некорректных данных
            pass
    
    @given(st.dictionaries(
        keys=st.sampled_from([
            'outbound_fuel', 'return_fuel', 'total_fuel',
            'delta_v_outbound', 'delta_v_return', 'total_delta_v',
            'engine_used', 'trajectory_type'
        ]),
        values=st.one_of(
            st.text(),
            st.floats(allow_nan=True, allow_infinity=True),
            st.integers(),
            st.none(),
            st.dictionaries(keys=st.text(), values=st.text())
        ),
        min_size=0,
        max_size=10
    ))
    def test_fuel_result_validation_rejects_invalid_data(self, invalid_data):
        """
        **Feature: space-fuel-calculator, Property 18: Валидация структуры данных**
        **Validates: Requirements 5.5**
        
        Для любого некорректного словаря данных результата топлива, парсинг должен 
        валидировать структуру и отклонять некорректные файлы.
        """
        # Проверяем, что некорректные данные отклоняются
        try:
            fuel_result = FuelResult.from_dict(invalid_data)
            # Если создание прошло успешно, проверяем, что данные действительно валидны
            assert isinstance(fuel_result.outbound_fuel, (int, float)) and fuel_result.outbound_fuel >= 0
            assert fuel_result.return_fuel is None or (isinstance(fuel_result.return_fuel, (int, float)) and fuel_result.return_fuel >= 0)
            assert isinstance(fuel_result.total_fuel, (int, float)) and fuel_result.total_fuel >= 0
            assert isinstance(fuel_result.delta_v_outbound, (int, float)) and fuel_result.delta_v_outbound >= 0
            assert fuel_result.delta_v_return is None or (isinstance(fuel_result.delta_v_return, (int, float)) and fuel_result.delta_v_return >= 0)
            assert isinstance(fuel_result.total_delta_v, (int, float)) and fuel_result.total_delta_v >= 0
            assert isinstance(fuel_result.trajectory_type, str) and len(fuel_result.trajectory_type) > 0
        except (KeyError, TypeError, ValueError):
            # Ожидаемое поведение для некорректных данных
            pass
    
    @given(st.dictionaries(
        keys=st.sampled_from([
            'id', 'name', 'destination', 'payload_mass', 'engine',
            'use_gravity_assists', 'created_at', 'fuel_requirements'
        ]),
        values=st.one_of(
            st.text(),
            st.floats(allow_nan=True, allow_infinity=True),
            st.integers(),
            st.none(),
            st.dictionaries(keys=st.text(), values=st.text()),
            st.booleans()
        ),
        min_size=0,
        max_size=10
    ))
    def test_mission_validation_rejects_invalid_data(self, invalid_data):
        """
        **Feature: space-fuel-calculator, Property 18: Валидация структуры данных**
        **Validates: Requirements 5.5**
        
        Для любого некорректного словаря данных миссии, парсинг должен 
        валидировать структуру и отклонять некорректные файлы.
        """
        # Проверяем, что некорректные данные отклоняются
        try:
            mission = Mission.from_dict(invalid_data)
            # Если создание прошло успешно, проверяем, что данные действительно валидны
            assert isinstance(mission.id, str) and len(mission.id) > 0
            assert isinstance(mission.name, str) and len(mission.name) > 0
            assert isinstance(mission.payload_mass, (int, float)) and mission.payload_mass >= 0
            assert isinstance(mission.use_gravity_assists, bool)
            assert isinstance(mission.created_at, datetime)
        except (KeyError, TypeError, ValueError):
            # Ожидаемое поведение для некорректных данных
            pass
    
    @given(st.text())
    def test_json_validation_rejects_malformed_json(self, malformed_json):
        """
        **Feature: space-fuel-calculator, Property 18: Валидация структуры данных**
        **Validates: Requirements 5.5**
        
        Для любой некорректной JSON строки, парсинг должен отклонить данные 
        и выбросить соответствующее исключение.
        """
        # Исключаем валидные JSON строки из теста
        try:
            json.loads(malformed_json)
            # Если JSON валиден, пропускаем тест
            return
        except json.JSONDecodeError:
            # Это то, что мы хотим протестировать
            pass
        
        # Проверяем, что все модели корректно отклоняют некорректный JSON
        with pytest.raises((json.JSONDecodeError, ValueError, KeyError, TypeError)):
            Planet.from_json(malformed_json)
        
        with pytest.raises((json.JSONDecodeError, ValueError, KeyError, TypeError)):
            from space_fuel_calculator.models.engine import engine_from_json
            engine_from_json(malformed_json)
        
        with pytest.raises((json.JSONDecodeError, ValueError, KeyError, TypeError)):
            FuelResult.from_json(malformed_json)
        
        with pytest.raises((json.JSONDecodeError, ValueError, KeyError, TypeError)):
            Mission.from_json(malformed_json)
    
    def test_negative_values_are_rejected(self):
        """
        **Feature: space-fuel-calculator, Property 18: Валидация структуры данных**
        **Validates: Requirements 5.5**
        
        Проверяем, что отрицательные значения корректно отклоняются.
        """
        # Тест для Planet с отрицательными значениями
        with pytest.raises(ValueError):
            Planet("Test", -1000, 1000, 1000, 1000)  # отрицательная масса
        
        with pytest.raises(ValueError):
            Planet("Test", 1000, -1000, 1000, 1000)  # отрицательный радиус
        
        # Тест для Engine с отрицательными значениями
        with pytest.raises(ValueError):
            ChemicalEngine("Test", -100, 1000, "fuel")  # отрицательный удельный импульс
        
        with pytest.raises(ValueError):
            ChemicalEngine("Test", 100, -1000, "fuel")  # отрицательная тяга
        
        # Тест для FuelResult с отрицательными значениями
        engine = ChemicalEngine("Test", 300, 1000, "fuel")
        
        with pytest.raises(ValueError):
            FuelResult(-1000, 1000, 2000, 1000, 1000, 2000, engine, "direct")  # отрицательное топливо
        
        # Тест для Mission с отрицательной массой полезной нагрузки
        earth = Planet("Earth", 5.972e24, 6.371e6, 1.496e11, 11200)
        
        with pytest.raises(ValueError):
            Mission("id", "name", earth, -1000, engine, False, datetime.now(timezone.utc))
    
    def test_empty_strings_are_rejected(self):
        """
        **Feature: space-fuel-calculator, Property 18: Валидация структуры данных**
        **Validates: Requirements 5.5**
        
        Проверяем, что пустые строки корректно отклоняются.
        """
        # Тест для Mission с пустыми строками
        earth = Planet("Earth", 5.972e24, 6.371e6, 1.496e11, 11200)
        engine = ChemicalEngine("Test", 300, 1000, "fuel")
        
        with pytest.raises(ValueError):
            Mission("", "name", earth, 1000, engine, False, datetime.now(timezone.utc))  # пустой ID
        
        with pytest.raises(ValueError):
            Mission("id", "", earth, 1000, engine, False, datetime.now(timezone.utc))  # пустое имя