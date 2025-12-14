"""
Property-based тесты для сериализации моделей данных.

**Feature: space-fuel-calculator, Property 16: Round-trip сериализации миссии**
**Validates: Requirements 5.2, 5.3**
"""
import pytest
from hypothesis import given, strategies as st
from datetime import datetime, timezone
import json

from space_fuel_calculator.models import (
    Planet, 
    ChemicalEngine, 
    IonEngine, 
    NuclearEngine,
    Mission, 
    FuelResult
)


# Стратегии для генерации тестовых данных
@st.composite
def planet_strategy(draw):
    """Генерирует валидные планеты."""
    name = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc'))))
    mass = draw(st.floats(min_value=1e20, max_value=1e30, allow_nan=False, allow_infinity=False))
    radius = draw(st.floats(min_value=1e5, max_value=1e8, allow_nan=False, allow_infinity=False))
    orbital_radius = draw(st.floats(min_value=1e10, max_value=1e12, allow_nan=False, allow_infinity=False))
    escape_velocity = draw(st.floats(min_value=1000, max_value=100000, allow_nan=False, allow_infinity=False))
    
    return Planet(name, mass, radius, orbital_radius, escape_velocity)


@st.composite
def chemical_engine_strategy(draw):
    """Генерирует валидные химические двигатели."""
    name = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc'))))
    specific_impulse = draw(st.floats(min_value=100, max_value=500, allow_nan=False, allow_infinity=False))
    thrust = draw(st.floats(min_value=1000, max_value=10000000, allow_nan=False, allow_infinity=False))
    fuel_type = draw(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc'))))
    
    return ChemicalEngine(name, specific_impulse, thrust, fuel_type)


@st.composite
def ion_engine_strategy(draw):
    """Генерирует валидные ионные двигатели."""
    name = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc'))))
    specific_impulse = draw(st.floats(min_value=1000, max_value=10000, allow_nan=False, allow_infinity=False))
    thrust = draw(st.floats(min_value=0.001, max_value=10, allow_nan=False, allow_infinity=False))
    power_consumption = draw(st.floats(min_value=100, max_value=100000, allow_nan=False, allow_infinity=False))
    
    return IonEngine(name, specific_impulse, thrust, power_consumption)


@st.composite
def nuclear_engine_strategy(draw):
    """Генерирует валидные ядерные двигатели."""
    name = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc'))))
    specific_impulse = draw(st.floats(min_value=500, max_value=2000, allow_nan=False, allow_infinity=False))
    thrust = draw(st.floats(min_value=10000, max_value=1000000, allow_nan=False, allow_infinity=False))
    reactor_power = draw(st.floats(min_value=1e6, max_value=1e10, allow_nan=False, allow_infinity=False))
    propellant_type = draw(st.text(min_size=1, max_size=10, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))
    
    return NuclearEngine(name, specific_impulse, thrust, reactor_power, propellant_type)


@st.composite
def engine_strategy(draw):
    """Генерирует любой тип двигателя."""
    engine_type = draw(st.sampled_from(['chemical', 'ion', 'nuclear']))
    
    if engine_type == 'chemical':
        return draw(chemical_engine_strategy())
    elif engine_type == 'ion':
        return draw(ion_engine_strategy())
    else:
        return draw(nuclear_engine_strategy())


@st.composite
def fuel_result_strategy(draw):
    """Генерирует валидные результаты расчета топлива."""
    outbound_fuel = draw(st.floats(min_value=0, max_value=1e6, allow_nan=False, allow_infinity=False))
    return_fuel = draw(st.one_of(
        st.none(),
        st.floats(min_value=0, max_value=1e6, allow_nan=False, allow_infinity=False)
    ))
    total_fuel = draw(st.floats(min_value=0, max_value=2e6, allow_nan=False, allow_infinity=False))
    
    delta_v_outbound = draw(st.floats(min_value=0, max_value=50000, allow_nan=False, allow_infinity=False))
    delta_v_return = draw(st.one_of(
        st.none(),
        st.floats(min_value=0, max_value=50000, allow_nan=False, allow_infinity=False)
    ))
    total_delta_v = draw(st.floats(min_value=0, max_value=100000, allow_nan=False, allow_infinity=False))
    
    engine_used = draw(engine_strategy())
    trajectory_type = draw(st.sampled_from(['direct', 'hohmann', 'gravity_assist']))
    
    return FuelResult(
        outbound_fuel, return_fuel, total_fuel,
        delta_v_outbound, delta_v_return, total_delta_v,
        engine_used, trajectory_type
    )


@st.composite
def mission_strategy(draw):
    """Генерирует валидные миссии."""
    mission_id = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc'))))
    name = draw(st.text(min_size=1, max_size=100, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc', 'Zs'))))
    destination = draw(planet_strategy())
    payload_mass = draw(st.floats(min_value=0, max_value=1e6, allow_nan=False, allow_infinity=False))
    engine = draw(engine_strategy())
    use_gravity_assists = draw(st.booleans())
    
    # Генерируем дату в разумном диапазоне (naive datetime, затем добавляем UTC)
    naive_datetime = draw(st.datetimes(
        min_value=datetime(2020, 1, 1),
        max_value=datetime(2030, 12, 31)
    ))
    created_at = naive_datetime.replace(tzinfo=timezone.utc)
    
    fuel_requirements = draw(st.one_of(st.none(), fuel_result_strategy()))
    
    return Mission(
        mission_id, name, destination, payload_mass, engine,
        use_gravity_assists, created_at, fuel_requirements
    )


class TestModelsSerialization:
    """Тесты сериализации моделей данных."""
    
    @given(planet_strategy())
    def test_planet_round_trip_serialization(self, planet):
        """
        **Feature: space-fuel-calculator, Property 16: Round-trip сериализации миссии**
        **Validates: Requirements 5.2, 5.3**
        
        Для любой планеты, сериализация в JSON с последующей десериализацией 
        должна восстановить эквивалентную планету.
        """
        # Сериализация в JSON
        json_str = planet.to_json()
        
        # Проверяем, что JSON валиден
        json_data = json.loads(json_str)
        assert isinstance(json_data, dict)
        
        # Десериализация обратно
        restored_planet = Planet.from_json(json_str)
        
        # Проверяем эквивалентность
        assert restored_planet == planet
        assert restored_planet.name == planet.name
        assert restored_planet.mass == planet.mass
        assert restored_planet.radius == planet.radius
        assert restored_planet.orbital_radius == planet.orbital_radius
        assert restored_planet.escape_velocity == planet.escape_velocity
    
    @given(engine_strategy())
    def test_engine_round_trip_serialization(self, engine):
        """
        **Feature: space-fuel-calculator, Property 16: Round-trip сериализации миссии**
        **Validates: Requirements 5.2, 5.3**
        
        Для любого двигателя, сериализация в JSON с последующей десериализацией 
        должна восстановить эквивалентный двигатель.
        """
        # Сериализация в JSON
        json_str = engine.to_json()
        
        # Проверяем, что JSON валиден
        json_data = json.loads(json_str)
        assert isinstance(json_data, dict)
        
        # Десериализация обратно
        from space_fuel_calculator.models.engine import engine_from_json
        restored_engine = engine_from_json(json_str)
        
        # Проверяем эквивалентность
        assert restored_engine == engine
        assert restored_engine.name == engine.name
        assert restored_engine.specific_impulse == engine.specific_impulse
        assert restored_engine.thrust == engine.thrust
        assert restored_engine.engine_type == engine.engine_type
    
    @given(fuel_result_strategy())
    def test_fuel_result_round_trip_serialization(self, fuel_result):
        """
        **Feature: space-fuel-calculator, Property 16: Round-trip сериализации миссии**
        **Validates: Requirements 5.2, 5.3**
        
        Для любого результата расчета топлива, сериализация в JSON с последующей 
        десериализацией должна восстановить эквивалентный результат.
        """
        # Сериализация в JSON
        json_str = fuel_result.to_json()
        
        # Проверяем, что JSON валиден
        json_data = json.loads(json_str)
        assert isinstance(json_data, dict)
        
        # Десериализация обратно
        restored_result = FuelResult.from_json(json_str)
        
        # Проверяем эквивалентность
        assert restored_result == fuel_result
        assert restored_result.outbound_fuel == fuel_result.outbound_fuel
        assert restored_result.return_fuel == fuel_result.return_fuel
        assert restored_result.total_fuel == fuel_result.total_fuel
        assert restored_result.delta_v_outbound == fuel_result.delta_v_outbound
        assert restored_result.delta_v_return == fuel_result.delta_v_return
        assert restored_result.total_delta_v == fuel_result.total_delta_v
        assert restored_result.engine_used == fuel_result.engine_used
        assert restored_result.trajectory_type == fuel_result.trajectory_type
    
    @given(mission_strategy())
    def test_mission_round_trip_serialization(self, mission):
        """
        **Feature: space-fuel-calculator, Property 16: Round-trip сериализации миссии**
        **Validates: Requirements 5.2, 5.3**
        
        Для любой конфигурации миссии, сериализация в JSON с последующей 
        десериализацией должна восстановить эквивалентную конфигурацию.
        """
        # Сериализация в JSON
        json_str = mission.to_json()
        
        # Проверяем, что JSON валиден
        json_data = json.loads(json_str)
        assert isinstance(json_data, dict)
        
        # Десериализация обратно
        restored_mission = Mission.from_json(json_str)
        
        # Проверяем эквивалентность
        assert restored_mission == mission
        assert restored_mission.id == mission.id
        assert restored_mission.name == mission.name
        assert restored_mission.destination == mission.destination
        assert restored_mission.payload_mass == mission.payload_mass
        assert restored_mission.engine == mission.engine
        assert restored_mission.use_gravity_assists == mission.use_gravity_assists
        assert restored_mission.created_at == mission.created_at
        assert restored_mission.fuel_requirements == mission.fuel_requirements