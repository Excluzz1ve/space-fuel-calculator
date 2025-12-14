"""
Property-based тесты для калькулятора топлива.
"""

import pytest
import math
import sys
from pathlib import Path
from hypothesis import given, strategies as st, assume, settings

# Добавляем корневую директорию проекта в путь
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from space_fuel_calculator.calculators import FuelCalculator
from space_fuel_calculator.models.engine import ChemicalEngine, IonEngine, NuclearEngine
from space_fuel_calculator.utils.exceptions import InvalidInputError, PhysicsViolationError


# Стандартное ускорение свободного падения на Земле (м/с²)
STANDARD_GRAVITY = 9.80665


class TestFuelCalculatorProperties:
    """Property-based тесты для FuelCalculator."""
    
    def setup_method(self):
        """Настройка для каждого теста."""
        self.calculator = FuelCalculator()
    
    @given(
        delta_v=st.floats(min_value=100, max_value=15000),  # Разумные значения дельта-V
        payload_mass=st.floats(min_value=1, max_value=100000),  # От 1 кг до 100 тонн
        specific_impulse=st.floats(min_value=200, max_value=500),  # Типичные значения для химических двигателей
        thrust=st.floats(min_value=1000, max_value=10000000)  # От 1 кН до 10 МН
    )
    @settings(max_examples=100)
    def test_tsiolkovsky_equation_property(self, delta_v, payload_mass, specific_impulse, thrust):
        # Фильтруем комбинации, которые приводят к нереалистичным отношениям масс
        exhaust_velocity = specific_impulse * STANDARD_GRAVITY
        mass_ratio = math.exp(delta_v / exhaust_velocity)
        assume(mass_ratio <= 1000)  # Ограничиваем практическими пределами ракетостроения
        """
        **Feature: space-fuel-calculator, Property 2: Соответствие уравнению Циолковского**
        
        Для любых входных параметров (дельта-V, масса полезной нагрузки, удельный импульс),
        рассчитанная масса топлива должна соответствовать уравнению Циолковского:
        m_fuel = m_payload × (exp(Δv/(Isp×g₀)) - 1)
        
        **Validates: Requirements 1.2**
        """
        # Создаем двигатель с заданными параметрами
        engine = ChemicalEngine(
            name="Test Engine",
            specific_impulse=specific_impulse,
            thrust=thrust,
            fuel_type="Test Fuel"
        )
        
        # Выполняем расчет
        result = self.calculator.calculate_fuel_mass(delta_v, payload_mass, engine)
        
        # Вычисляем ожидаемую массу топлива по уравнению Циолковского
        exhaust_velocity = specific_impulse * STANDARD_GRAVITY
        mass_ratio = math.exp(delta_v / exhaust_velocity)
        expected_fuel_mass = payload_mass * (mass_ratio - 1)
        
        # Проверяем соответствие с небольшой погрешностью для вычислений с плавающей точкой
        relative_error = abs(result.total_fuel - expected_fuel_mass) / expected_fuel_mass
        assert relative_error < 1e-10, (
            f"Расчетная масса топлива {result.total_fuel:.6f} кг не соответствует "
            f"уравнению Циолковского {expected_fuel_mass:.6f} кг. "
            f"Относительная ошибка: {relative_error:.2e}"
        )
        
        # Проверяем, что результат содержит правильные значения
        assert result.delta_v_outbound == delta_v
        assert result.total_delta_v == delta_v
        assert result.engine_used == engine
        assert result.outbound_fuel == result.total_fuel
        assert result.return_fuel is None
        assert result.delta_v_return is None
    
    @given(
        delta_v=st.floats(min_value=100, max_value=15000),
        payload_mass=st.floats(min_value=1, max_value=100000),
        specific_impulse=st.floats(min_value=200, max_value=500),
        thrust=st.floats(min_value=1000, max_value=10000000)
    )
    @settings(max_examples=100)
    def test_fuel_mass_always_positive(self, delta_v, payload_mass, specific_impulse, thrust):
        # Фильтруем комбинации, которые приводят к нереалистичным отношениям масс
        exhaust_velocity = specific_impulse * STANDARD_GRAVITY
        mass_ratio = math.exp(delta_v / exhaust_velocity)
        assume(mass_ratio <= 1000)  # Ограничиваем практическими пределами ракетостроения
        """
        Дополнительное свойство: масса топлива всегда должна быть положительной
        для положительных входных параметров.
        """
        engine = ChemicalEngine(
            name="Test Engine",
            specific_impulse=specific_impulse,
            thrust=thrust,
            fuel_type="Test Fuel"
        )
        
        result = self.calculator.calculate_fuel_mass(delta_v, payload_mass, engine)
        
        assert result.total_fuel > 0, f"Масса топлива должна быть положительной, получено: {result.total_fuel}"
        assert result.outbound_fuel > 0, f"Масса топлива для прямого полета должна быть положительной"
    
    @given(
        delta_v=st.floats(min_value=100, max_value=15000),
        payload_mass1=st.floats(min_value=1, max_value=50000),
        payload_mass2=st.floats(min_value=1, max_value=50000),
        specific_impulse=st.floats(min_value=200, max_value=500),
        thrust=st.floats(min_value=1000, max_value=10000000)
    )
    @settings(max_examples=100)
    def test_payload_mass_monotonicity_property(self, delta_v, payload_mass1, payload_mass2, specific_impulse, thrust):
        """
        **Feature: space-fuel-calculator, Property 3: Монотонность по массе полезной нагрузки**
        
        Для любого фиксированного двигателя и траектории, увеличение массы полезной нагрузки
        должно приводить к увеличению требуемой массы топлива.
        
        **Validates: Requirements 1.3**
        """
        # Фильтруем комбинации, которые приводят к нереалистичным отношениям масс
        exhaust_velocity = specific_impulse * STANDARD_GRAVITY
        mass_ratio = math.exp(delta_v / exhaust_velocity)
        assume(mass_ratio <= 1000)  # Ограничиваем практическими пределами ракетостроения
        
        # Убеждаемся, что массы различны для проверки монотонности
        assume(payload_mass1 != payload_mass2)
        
        # Создаем двигатель с заданными параметрами
        engine = ChemicalEngine(
            name="Test Engine",
            specific_impulse=specific_impulse,
            thrust=thrust,
            fuel_type="Test Fuel"
        )
        
        # Выполняем расчеты для обеих масс
        result1 = self.calculator.calculate_fuel_mass(delta_v, payload_mass1, engine)
        result2 = self.calculator.calculate_fuel_mass(delta_v, payload_mass2, engine)
        
        # Проверяем монотонность: большая масса полезной нагрузки -> больше топлива
        if payload_mass1 < payload_mass2:
            assert result1.total_fuel < result2.total_fuel, (
                f"Нарушение монотонности: для массы {payload_mass1:.2f} кг получено "
                f"{result1.total_fuel:.2f} кг топлива, а для массы {payload_mass2:.2f} кг "
                f"получено {result2.total_fuel:.2f} кг топлива"
            )
        else:  # payload_mass1 > payload_mass2
            assert result1.total_fuel > result2.total_fuel, (
                f"Нарушение монотонности: для массы {payload_mass1:.2f} кг получено "
                f"{result1.total_fuel:.2f} кг топлива, а для массы {payload_mass2:.2f} кг "
                f"получено {result2.total_fuel:.2f} кг топлива"
            )
    
    @given(
        delta_v=st.one_of(
            st.floats(min_value=-10000, max_value=-1),  # Отрицательные значения
            st.floats(min_value=60000, max_value=100000),  # Слишком большие значения
            st.just(float('inf')),  # Бесконечность
            st.just(float('nan'))   # NaN
        ),
        payload_mass=st.one_of(
            st.floats(min_value=-10000, max_value=0),  # Отрицательные и нулевые значения
            st.just(float('inf')),  # Бесконечность
            st.just(float('nan'))   # NaN
        ),
        specific_impulse=st.floats(min_value=200, max_value=500),
        thrust=st.floats(min_value=1000, max_value=10000000)
    )
    @settings(max_examples=100)
    def test_physical_realism_validation_property(self, delta_v, payload_mass, specific_impulse, thrust):
        """
        **Feature: space-fuel-calculator, Property 20: Валидация физической реалистичности**
        
        Для любых входных параметров, система должна отклонять физически нереалистичные
        значения (отрицательные массы, сверхсветовые скорости).
        
        **Validates: Requirements 6.3**
        """
        # Создаем двигатель с заданными параметрами
        engine = ChemicalEngine(
            name="Test Engine",
            specific_impulse=specific_impulse,
            thrust=thrust,
            fuel_type="Test Fuel"
        )
        
        # Система должна отклонить нереалистичные параметры
        with pytest.raises((InvalidInputError, PhysicsViolationError, ValueError)):
            self.calculator.calculate_fuel_mass(delta_v, payload_mass, engine)
    
    @given(
        payload_mass=st.floats(min_value=1, max_value=10000),
        planet_mass=st.floats(min_value=1e20, max_value=1e26),  # Массы планет
        planet_radius=st.floats(min_value=1e6, max_value=1e7),  # Радиусы планет
        orbital_radius=st.floats(min_value=1e10, max_value=1e12),  # Орбитальные радиусы
        escape_velocity=st.floats(min_value=1000, max_value=20000),  # Скорости убегания
        specific_impulse=st.floats(min_value=200, max_value=500),
        thrust=st.floats(min_value=1000, max_value=10000000)
    )
    @settings(max_examples=20)
    def test_return_flight_positive_delta_v_property(self, payload_mass, planet_mass, planet_radius, 
                                                   orbital_radius, escape_velocity, specific_impulse, thrust):
        """
        **Feature: space-fuel-calculator, Property 5: Положительная дельта-V для обратного полета**
        
        Для любой планеты назначения, система должна рассчитать положительное значение
        дельта-V для возвращения на Землю.
        
        **Validates: Requirements 2.1**
        """
        from space_fuel_calculator.models.planet import Planet
        
        # Ограничиваем значения для избежания экстремальных случаев
        assume(escape_velocity < 15000)  # Разумный предел для скорости убегания
        assume(orbital_radius > 5e10)    # Минимальный орбитальный радиус
        
        # Создаем планету с заданными параметрами
        planet = Planet(
            name="Test Planet",
            mass=planet_mass,
            radius=planet_radius,
            orbital_radius=orbital_radius,
            escape_velocity=escape_velocity
        )
        
        # Создаем двигатель
        engine = ChemicalEngine(
            name="Test Engine",
            specific_impulse=specific_impulse,
            thrust=thrust,
            fuel_type="Test Fuel"
        )
        
        # Проверяем, что расчет не приведет к экстремальным значениям дельта-V
        GM_SUN = 1.327e20
        EARTH_ORBITAL_RADIUS = 1.496e11
        delta_v_earth_escape = math.sqrt(GM_SUN / EARTH_ORBITAL_RADIUS)
        delta_v_destination_capture = math.sqrt(GM_SUN / orbital_radius)
        delta_v_outbound = abs(delta_v_destination_capture - delta_v_earth_escape)
        delta_v_return = delta_v_outbound + escape_velocity
        
        # Проверяем, что каждая дельта-V не превышает пределы mass_ratio
        exhaust_velocity = specific_impulse * 9.80665
        mass_ratio_outbound = math.exp(delta_v_outbound / exhaust_velocity)
        mass_ratio_return = math.exp(delta_v_return / exhaust_velocity)
        
        # Ограничиваем отношения масс для избежания превышения практических пределов
        assume(mass_ratio_outbound <= 1000)
        assume(mass_ratio_return <= 1000)
        
        # Выполняем расчет полета туда и обратно
        result = self.calculator.calculate_round_trip_fuel(planet, payload_mass, engine)
        
        # Проверяем, что дельта-V для обратного полета положительная
        assert result.delta_v_return > 0, (
            f"Дельта-V для обратного полета должна быть положительной, "
            f"получено: {result.delta_v_return} м/с"
        )
        
        # Проверяем, что общая дельта-V больше дельта-V прямого полета
        assert result.total_delta_v > result.delta_v_outbound, (
            f"Общая дельта-V ({result.total_delta_v} м/с) должна быть больше "
            f"дельта-V прямого полета ({result.delta_v_outbound} м/с)"
        )
        
        # Проверяем, что топливо для обратного полета положительное
        assert result.return_fuel > 0, (
            f"Топливо для обратного полета должно быть положительным, "
            f"получено: {result.return_fuel} кг"
        )
    
    @given(
        payload_mass=st.floats(min_value=100, max_value=5000),
        escape_velocity1=st.floats(min_value=2000, max_value=8000),  # Меньшая гравитация
        escape_velocity2=st.floats(min_value=8000, max_value=15000), # Большая гравитация
        orbital_radius=st.floats(min_value=1e11, max_value=5e11),   # Фиксированный орбитальный радиус
        specific_impulse=st.floats(min_value=300, max_value=450),   # Хорошие двигатели
        thrust=st.floats(min_value=1000000, max_value=10000000)
    )
    @settings(max_examples=20)
    def test_gravity_influence_on_energy_property(self, payload_mass, escape_velocity1, escape_velocity2, 
                                                orbital_radius, specific_impulse, thrust):
        """
        **Feature: space-fuel-calculator, Property 6: Влияние гравитации на энергозатраты**
        
        Для любых двух планет с разной гравитацией, планета с большей гравитацией
        должна требовать больше энергии для взлета.
        
        **Validates: Requirements 2.2**
        """
        from space_fuel_calculator.models.planet import Planet
        
        # Убеждаемся, что скорости убегания различны
        assume(escape_velocity1 != escape_velocity2)
        
        # Создаем две планеты с разными скоростями убегания, но одинаковыми орбитальными радиусами
        planet1 = Planet(
            name="Low Gravity Planet",
            mass=1e24,  # Фиксированная масса
            radius=5e6,  # Фиксированный радиус
            orbital_radius=orbital_radius,
            escape_velocity=escape_velocity1
        )
        
        planet2 = Planet(
            name="High Gravity Planet", 
            mass=2e24,  # Фиксированная масса
            radius=5e6,  # Фиксированный радиус
            orbital_radius=orbital_radius,
            escape_velocity=escape_velocity2
        )
        
        # Создаем двигатель
        engine = ChemicalEngine(
            name="Test Engine",
            specific_impulse=specific_impulse,
            thrust=thrust,
            fuel_type="Test Fuel"
        )
        
        # Проверяем, что расчеты не превысят практические пределы
        GM_SUN = 1.327e20
        EARTH_ORBITAL_RADIUS = 1.496e11
        delta_v_earth_escape = math.sqrt(GM_SUN / EARTH_ORBITAL_RADIUS)
        delta_v_destination_capture = math.sqrt(GM_SUN / orbital_radius)
        delta_v_outbound = abs(delta_v_destination_capture - delta_v_earth_escape)
        
        delta_v_return1 = delta_v_outbound + escape_velocity1
        delta_v_return2 = delta_v_outbound + escape_velocity2
        
        exhaust_velocity = specific_impulse * 9.80665
        mass_ratio1 = math.exp(delta_v_return1 / exhaust_velocity)
        mass_ratio2 = math.exp(delta_v_return2 / exhaust_velocity)
        
        assume(mass_ratio1 <= 1000)
        assume(mass_ratio2 <= 1000)
        
        # Выполняем расчеты для обеих планет
        result1 = self.calculator.calculate_round_trip_fuel(planet1, payload_mass, engine)
        result2 = self.calculator.calculate_round_trip_fuel(planet2, payload_mass, engine)
        
        # Проверяем влияние гравитации: планета с большей скоростью убегания требует больше энергии
        if escape_velocity1 < escape_velocity2:
            assert result1.total_fuel < result2.total_fuel, (
                f"Планета с большей гравитацией должна требовать больше топлива: "
                f"планета1 (escape_v={escape_velocity1:.0f}) -> {result1.total_fuel:.2f} кг, "
                f"планета2 (escape_v={escape_velocity2:.0f}) -> {result2.total_fuel:.2f} кг"
            )
            assert result1.delta_v_return < result2.delta_v_return, (
                f"Планета с большей гравитацией должна требовать больше дельта-V для возвращения: "
                f"планета1 -> {result1.delta_v_return:.0f} м/с, "
                f"планета2 -> {result2.delta_v_return:.0f} м/с"
            )
        else:  # escape_velocity1 > escape_velocity2
            assert result1.total_fuel > result2.total_fuel, (
                f"Планета с большей гравитацией должна требовать больше топлива: "
                f"планета1 (escape_v={escape_velocity1:.0f}) -> {result1.total_fuel:.2f} кг, "
                f"планета2 (escape_v={escape_velocity2:.0f}) -> {result2.total_fuel:.2f} кг"
            )
            assert result1.delta_v_return > result2.delta_v_return, (
                f"Планета с большей гравитацией должна требовать больше дельта-V для возвращения: "
                f"планета1 -> {result1.delta_v_return:.0f} м/с, "
                f"планета2 -> {result2.delta_v_return:.0f} м/с"
            )
    
    @given(
        payload_mass=st.floats(min_value=100, max_value=5000),
        orbital_radius=st.floats(min_value=1.5e11, max_value=4e11),
        escape_velocity=st.floats(min_value=3000, max_value=10000),
        specific_impulse=st.floats(min_value=300, max_value=450),
        thrust=st.floats(min_value=1000000, max_value=10000000)
    )
    @settings(max_examples=20)
    def test_mission_fuel_additivity_property(self, payload_mass, orbital_radius, escape_velocity, 
                                            specific_impulse, thrust):
        """
        **Feature: space-fuel-calculator, Property 7: Аддитивность топлива миссии**
        
        Для любой миссии туда и обратно, общая масса топлива должна равняться
        сумме топлива для прямого и обратного полетов.
        
        **Validates: Requirements 2.3**
        """
        from space_fuel_calculator.models.planet import Planet
        
        # Создаем планету
        planet = Planet(
            name="Test Planet",
            mass=1e24,
            radius=5e6,
            orbital_radius=orbital_radius,
            escape_velocity=escape_velocity
        )
        
        # Создаем двигатель
        engine = ChemicalEngine(
            name="Test Engine",
            specific_impulse=specific_impulse,
            thrust=thrust,
            fuel_type="Test Fuel"
        )
        
        # Проверяем, что расчеты не превысят практические пределы
        GM_SUN = 1.327e20
        EARTH_ORBITAL_RADIUS = 1.496e11
        delta_v_earth_escape = math.sqrt(GM_SUN / EARTH_ORBITAL_RADIUS)
        delta_v_destination_capture = math.sqrt(GM_SUN / orbital_radius)
        delta_v_outbound = abs(delta_v_destination_capture - delta_v_earth_escape)
        delta_v_return = delta_v_outbound + escape_velocity
        
        exhaust_velocity = specific_impulse * 9.80665
        mass_ratio_outbound = math.exp(delta_v_outbound / exhaust_velocity)
        mass_ratio_return = math.exp(delta_v_return / exhaust_velocity)
        
        assume(mass_ratio_outbound <= 1000)
        assume(mass_ratio_return <= 1000)
        
        # Выполняем расчет полета туда и обратно
        round_trip_result = self.calculator.calculate_round_trip_fuel(planet, payload_mass, engine)
        
        # Выполняем отдельные расчеты для прямого и обратного полетов
        outbound_result = self.calculator.calculate_fuel_mass(delta_v_outbound, payload_mass, engine)
        return_result = self.calculator.calculate_fuel_mass(delta_v_return, payload_mass, engine)
        
        # Проверяем аддитивность: общее топливо = топливо туда + топливо обратно
        expected_total_fuel = outbound_result.total_fuel + return_result.total_fuel
        
        # Допускаем небольшую погрешность из-за вычислений с плавающей точкой
        relative_error = abs(round_trip_result.total_fuel - expected_total_fuel) / expected_total_fuel
        assert relative_error < 1e-10, (
            f"Нарушение аддитивности топлива: "
            f"общее топливо {round_trip_result.total_fuel:.6f} кг != "
            f"сумма этапов {expected_total_fuel:.6f} кг "
            f"(относительная ошибка: {relative_error:.2e})"
        )
        
        # Проверяем, что компоненты результата соответствуют отдельным расчетам
        assert round_trip_result.outbound_fuel == outbound_result.total_fuel, (
            f"Топливо прямого полета не соответствует: "
            f"{round_trip_result.outbound_fuel} != {outbound_result.total_fuel}"
        )
        
        assert round_trip_result.return_fuel == return_result.total_fuel, (
            f"Топливо обратного полета не соответствует: "
            f"{round_trip_result.return_fuel} != {return_result.total_fuel}"
        )
    
    @given(
        delta_v=st.floats(min_value=1000, max_value=10000),
        payload_mass=st.floats(min_value=100, max_value=10000),
        specific_impulse=st.floats(min_value=200, max_value=500),
        thrust=st.floats(min_value=1000, max_value=10000000),
        fuel_type=st.text(min_size=1, max_size=20),
        power_consumption=st.floats(min_value=1000, max_value=100000),
        reactor_power=st.floats(min_value=10000, max_value=1000000),
        propellant_type=st.text(min_size=1, max_size=20)
    )
    @settings(max_examples=100)
    def test_engine_parameter_correctness_property(self, delta_v, payload_mass, specific_impulse, 
                                                 thrust, fuel_type, power_consumption, 
                                                 reactor_power, propellant_type):
        """
        **Feature: space-fuel-calculator, Property 9: Корректность параметров двигателя**
        
        Для любого выбранного двигателя, система должна использовать соответствующий
        удельный импульс в расчетах топлива.
        
        **Validates: Requirements 3.2**
        """
        # Фильтруем комбинации, которые приводят к нереалистичным отношениям масс
        exhaust_velocity = specific_impulse * STANDARD_GRAVITY
        mass_ratio = math.exp(delta_v / exhaust_velocity)
        assume(mass_ratio <= 1000)  # Ограничиваем практическими пределами ракетостроения
        
        # Создаем различные типы двигателей с одинаковым удельным импульсом
        chemical_engine = ChemicalEngine(
            name="Chemical Test Engine",
            specific_impulse=specific_impulse,
            thrust=thrust,
            fuel_type=fuel_type
        )
        
        ion_engine = IonEngine(
            name="Ion Test Engine", 
            specific_impulse=specific_impulse,
            thrust=thrust,
            power_consumption=power_consumption
        )
        
        nuclear_engine = NuclearEngine(
            name="Nuclear Test Engine",
            specific_impulse=specific_impulse,
            thrust=thrust,
            reactor_power=reactor_power,
            propellant_type=propellant_type
        )
        
        # Выполняем расчеты для всех типов двигателей
        chemical_result = self.calculator.calculate_fuel_mass(delta_v, payload_mass, chemical_engine)
        ion_result = self.calculator.calculate_fuel_mass(delta_v, payload_mass, ion_engine)
        nuclear_result = self.calculator.calculate_fuel_mass(delta_v, payload_mass, nuclear_engine)
        
        # Проверяем, что система использует правильный удельный импульс для каждого двигателя
        # Все двигатели имеют одинаковый удельный импульс, поэтому результаты должны быть одинаковыми
        
        # Вычисляем ожидаемую массу топлива по уравнению Циолковского
        expected_fuel_mass = payload_mass * (mass_ratio - 1)
        
        # Проверяем химический двигатель
        relative_error_chemical = abs(chemical_result.total_fuel - expected_fuel_mass) / expected_fuel_mass
        assert relative_error_chemical < 1e-10, (
            f"Химический двигатель: расчетная масса топлива {chemical_result.total_fuel:.6f} кг "
            f"не соответствует ожидаемой {expected_fuel_mass:.6f} кг для Isp={specific_impulse:.1f}с. "
            f"Относительная ошибка: {relative_error_chemical:.2e}"
        )
        
        # Проверяем ионный двигатель
        relative_error_ion = abs(ion_result.total_fuel - expected_fuel_mass) / expected_fuel_mass
        assert relative_error_ion < 1e-10, (
            f"Ионный двигатель: расчетная масса топлива {ion_result.total_fuel:.6f} кг "
            f"не соответствует ожидаемой {expected_fuel_mass:.6f} кг для Isp={specific_impulse:.1f}с. "
            f"Относительная ошибка: {relative_error_ion:.2e}"
        )
        
        # Проверяем ядерный двигатель
        relative_error_nuclear = abs(nuclear_result.total_fuel - expected_fuel_mass) / expected_fuel_mass
        assert relative_error_nuclear < 1e-10, (
            f"Ядерный двигатель: расчетная масса топлива {nuclear_result.total_fuel:.6f} кг "
            f"не соответствует ожидаемой {expected_fuel_mass:.6f} кг для Isp={specific_impulse:.1f}с. "
            f"Относительная ошибка: {relative_error_nuclear:.2e}"
        )
        
        # Проверяем, что результаты содержат правильные ссылки на двигатели
        assert chemical_result.engine_used == chemical_engine, (
            "Результат должен содержать ссылку на использованный химический двигатель"
        )
        assert ion_result.engine_used == ion_engine, (
            "Результат должен содержать ссылку на использованный ионный двигатель"
        )
        assert nuclear_result.engine_used == nuclear_engine, (
            "Результат должен содержать ссылку на использованный ядерный двигатель"
        )
        
        # Проверяем, что все результаты имеют одинаковые значения топлива (поскольку Isp одинаковый)
        assert abs(chemical_result.total_fuel - ion_result.total_fuel) < 1e-10, (
            f"Результаты для химического и ионного двигателей должны быть одинаковыми при одинаковом Isp: "
            f"{chemical_result.total_fuel:.6f} != {ion_result.total_fuel:.6f}"
        )
        
        assert abs(chemical_result.total_fuel - nuclear_result.total_fuel) < 1e-10, (
            f"Результаты для химического и ядерного двигателей должны быть одинаковыми при одинаковом Isp: "
            f"{chemical_result.total_fuel:.6f} != {nuclear_result.total_fuel:.6f}"
        )

    @given(
        delta_v=st.floats(min_value=1000, max_value=10000),
        payload_mass=st.floats(min_value=100, max_value=10000),
        specific_impulse1=st.floats(min_value=200, max_value=400),  # Химические двигатели
        specific_impulse2=st.floats(min_value=3000, max_value=8000),  # Ионные двигатели
        thrust=st.floats(min_value=1000, max_value=10000000),
        fuel_type=st.text(min_size=1, max_size=20),
        power_consumption=st.floats(min_value=1000, max_value=100000)
    )
    @settings(max_examples=100)
    def test_engine_fuel_consumption_differences_property(self, delta_v, payload_mass, specific_impulse1, 
                                                        specific_impulse2, thrust, fuel_type, power_consumption):
        """
        **Feature: space-fuel-calculator, Property 10: Различие двигателей по расходу топлива**
        
        Для любых двух разных типов двигателей при одинаковых условиях миссии,
        система должна показать разные значения расхода топлива.
        
        **Validates: Requirements 3.3**
        """
        # Убеждаемся, что удельные импульсы различны
        assume(abs(specific_impulse1 - specific_impulse2) > 100)  # Значительная разница
        
        # Фильтруем комбинации, которые приводят к нереалистичным отношениям масс
        exhaust_velocity1 = specific_impulse1 * STANDARD_GRAVITY
        exhaust_velocity2 = specific_impulse2 * STANDARD_GRAVITY
        mass_ratio1 = math.exp(delta_v / exhaust_velocity1)
        mass_ratio2 = math.exp(delta_v / exhaust_velocity2)
        assume(mass_ratio1 <= 1000)  # Ограничиваем практическими пределами ракетостроения
        assume(mass_ratio2 <= 1000)
        
        # Создаем два двигателя с разными удельными импульсами
        chemical_engine = ChemicalEngine(
            name="Chemical Engine",
            specific_impulse=specific_impulse1,
            thrust=thrust,
            fuel_type=fuel_type
        )
        
        ion_engine = IonEngine(
            name="Ion Engine",
            specific_impulse=specific_impulse2,
            thrust=thrust,
            power_consumption=power_consumption
        )
        
        # Выполняем расчеты для обоих двигателей при одинаковых условиях миссии
        chemical_result = self.calculator.calculate_fuel_mass(delta_v, payload_mass, chemical_engine)
        ion_result = self.calculator.calculate_fuel_mass(delta_v, payload_mass, ion_engine)
        
        # Проверяем, что расход топлива различается между двигателями
        fuel_difference = abs(chemical_result.total_fuel - ion_result.total_fuel)
        relative_difference = fuel_difference / min(chemical_result.total_fuel, ion_result.total_fuel)
        
        # Должна быть значительная разница в расходе топлива (более 1%)
        assert relative_difference > 0.01, (
            f"Двигатели с разными удельными импульсами должны показывать разный расход топлива: "
            f"химический (Isp={specific_impulse1:.0f}с) -> {chemical_result.total_fuel:.2f} кг, "
            f"ионный (Isp={specific_impulse2:.0f}с) -> {ion_result.total_fuel:.2f} кг, "
            f"относительная разница: {relative_difference:.1%}"
        )
        
        # Проверяем, что двигатель с большим удельным импульсом требует меньше топлива
        if specific_impulse1 < specific_impulse2:
            assert chemical_result.total_fuel > ion_result.total_fuel, (
                f"Двигатель с меньшим удельным импульсом должен требовать больше топлива: "
                f"химический (Isp={specific_impulse1:.0f}с) -> {chemical_result.total_fuel:.2f} кг, "
                f"ионный (Isp={specific_impulse2:.0f}с) -> {ion_result.total_fuel:.2f} кг"
            )
        else:  # specific_impulse1 > specific_impulse2
            assert chemical_result.total_fuel < ion_result.total_fuel, (
                f"Двигатель с меньшим удельным импульсом должен требовать больше топлива: "
                f"химический (Isp={specific_impulse1:.0f}с) -> {chemical_result.total_fuel:.2f} кг, "
                f"ионный (Isp={specific_impulse2:.0f}с) -> {ion_result.total_fuel:.2f} кг"
            )
        
        # Проверяем, что результаты содержат правильные ссылки на двигатели
        assert chemical_result.engine_used == chemical_engine, (
            "Результат должен содержать ссылку на использованный химический двигатель"
        )
        assert ion_result.engine_used == ion_engine, (
            "Результат должен содержать ссылку на использованный ионный двигатель"
        )
        
        # Проверяем, что оба результата имеют одинаковые дельта-V (поскольку условия миссии одинаковы)
        assert chemical_result.delta_v_outbound == delta_v, (
            f"Дельта-V в результате химического двигателя должна соответствовать входной: "
            f"{chemical_result.delta_v_outbound} != {delta_v}"
        )
        assert ion_result.delta_v_outbound == delta_v, (
            f"Дельта-V в результате ионного двигателя должна соответствовать входной: "
            f"{ion_result.delta_v_outbound} != {delta_v}"
        )

    @given(
        delta_v=st.floats(min_value=1000, max_value=15000),
        payload_mass=st.floats(min_value=100, max_value=10000),
        specific_impulse=st.floats(min_value=3000, max_value=8000),  # Типичные значения для ионных двигателей
        thrust=st.floats(min_value=0.01, max_value=1.0),  # Низкая тяга ионных двигателей (Н)
        power_consumption=st.floats(min_value=1000, max_value=50000)  # Потребляемая мощность (Вт)
    )
    @settings(max_examples=100)
    def test_ion_engine_energy_consumption_property(self, delta_v, payload_mass, specific_impulse, 
                                                  thrust, power_consumption):
        """
        **Feature: space-fuel-calculator, Property 11: Особенности ионных двигателей**
        
        Для любого ионного двигателя, система должна рассчитывать энергопотребление
        с учетом увеличенного времени полета.
        
        **Validates: Requirements 3.4**
        """
        # Фильтруем комбинации, которые приводят к нереалистичным отношениям масс
        exhaust_velocity = specific_impulse * STANDARD_GRAVITY
        mass_ratio = math.exp(delta_v / exhaust_velocity)
        assume(mass_ratio <= 1000)  # Ограничиваем практическими пределами ракетостроения
        
        # Создаем ионный двигатель
        ion_engine = IonEngine(
            name="Test Ion Engine",
            specific_impulse=specific_impulse,
            thrust=thrust,
            power_consumption=power_consumption
        )
        
        # Выполняем расчет топлива
        result = self.calculator.calculate_fuel_mass(delta_v, payload_mass, ion_engine)
        
        # Проверяем, что результат содержит правильную ссылку на ионный двигатель
        assert result.engine_used == ion_engine, (
            "Результат должен содержать ссылку на использованный ионный двигатель"
        )
        
        # Проверяем, что ионный двигатель имеет характерные особенности
        assert ion_engine.engine_type.value == "ion", (
            f"Тип двигателя должен быть 'ion', получено: {ion_engine.engine_type.value}"
        )
        
        # Проверяем, что ионный двигатель имеет высокий удельный импульс (>2000с)
        assert ion_engine.specific_impulse > 2000, (
            f"Ионный двигатель должен иметь высокий удельный импульс (>2000с), "
            f"получено: {ion_engine.specific_impulse:.0f}с"
        )
        
        # Проверяем, что ионный двигатель имеет низкую тягу (<10 Н)
        assert ion_engine.thrust < 10, (
            f"Ионный двигатель должен иметь низкую тягу (<10 Н), "
            f"получено: {ion_engine.thrust:.3f} Н"
        )
        
        # Проверяем, что ионный двигатель имеет определенное энергопотребление
        assert ion_engine.power_consumption > 0, (
            f"Ионный двигатель должен иметь положительное энергопотребление, "
            f"получено: {ion_engine.power_consumption:.0f} Вт"
        )
        
        # Расчет времени полета для ионного двигателя
        # Время = масса_топлива * удельный_импульс * g0 / тяга
        fuel_mass = result.total_fuel
        flight_time = (fuel_mass * specific_impulse * STANDARD_GRAVITY) / thrust  # секунды
        
        # Проверяем, что время полета положительное и конечное
        assert flight_time > 0, (
            f"Время полета должно быть положительным, получено: {flight_time:.0f} секунд"
        )
        
        assert math.isfinite(flight_time), (
            f"Время полета должно быть конечным, получено: {flight_time}"
        )
        
        # Ионные двигатели характеризуются длительным временем работы
        # Проверяем, что время полета больше, чем у химических двигателей
        # (для сравнения используем гипотетический химический двигатель с высокой тягой)
        chemical_thrust = 1000000  # 1 МН - типичная тяга химического двигателя
        chemical_flight_time = (fuel_mass * specific_impulse * STANDARD_GRAVITY) / chemical_thrust
        
        assert flight_time > chemical_flight_time, (
            f"Ионный двигатель должен иметь большее время полета чем химический: "
            f"ионный {flight_time:.0f}с vs химический {chemical_flight_time:.0f}с"
        )
        
        # Расчет общего энергопотребления
        total_energy_consumption = power_consumption * flight_time  # Вт⋅с = Дж
        
        # Проверяем, что энергопотребление положительное и разумное
        assert total_energy_consumption > 0, (
            f"Общее энергопотребление должно быть положительным, "
            f"получено: {total_energy_consumption:.0f} Дж"
        )
        
        # Проверяем соотношение энергии к массе топлива (должно быть высоким для ионных двигателей)
        energy_per_kg_fuel = total_energy_consumption / fuel_mass  # Дж/кг
        
        # Ионные двигатели должны иметь высокое соотношение энергии к массе топлива
        # по сравнению с химическими двигателями (>10 МДж/кг)
        assert energy_per_kg_fuel > 10e6, (
            f"Ионный двигатель должен иметь высокое соотношение энергии к массе топлива (>10 МДж/кг), "
            f"получено: {energy_per_kg_fuel/1e6:.1f} МДж/кг"
        )
        
        # Проверяем, что результат содержит корректные значения
        assert result.total_fuel > 0, (
            f"Масса топлива должна быть положительной, получено: {result.total_fuel:.2f} кг"
        )
        
        assert result.delta_v_outbound == delta_v, (
            f"Дельта-V должна соответствовать входному значению: {result.delta_v_outbound} != {delta_v}"
        )
        
        # Проверяем физическую реалистичность: ионные двигатели требуют меньше топлива
        # при том же удельном импульсе, но больше времени и энергии
        exhaust_velocity_check = specific_impulse * STANDARD_GRAVITY
        expected_fuel_mass = payload_mass * (math.exp(delta_v / exhaust_velocity_check) - 1)
        
        relative_error = abs(result.total_fuel - expected_fuel_mass) / expected_fuel_mass
        assert relative_error < 1e-10, (
            f"Расчет топлива для ионного двигателя должен соответствовать уравнению Циолковского: "
            f"расчетная масса {result.total_fuel:.6f} кг != ожидаемая {expected_fuel_mass:.6f} кг, "
            f"относительная ошибка: {relative_error:.2e}"
        )

    @given(
        delta_v=st.floats(min_value=500, max_value=12000),  # Практический диапазон дельта-V
        payload_mass=st.floats(min_value=10, max_value=50000),  # От 10 кг до 50 тонн
        specific_impulse=st.floats(min_value=250, max_value=450),  # Химические двигатели
        thrust=st.floats(min_value=100000, max_value=5000000)  # От 100 кН до 5 МН
    )
    @settings(max_examples=100)
    def test_tsiolkovsky_equation_accuracy_property(self, delta_v, payload_mass, specific_impulse, thrust):
        """
        **Feature: space-fuel-calculator, Property 19: Точность уравнения Циолковского**
        
        Для любых известных тестовых случаев, результаты расчетов должны соответствовать
        ожидаемым значениям с заданной точностью.
        
        **Validates: Requirements 6.1**
        """
        # Фильтруем комбинации, которые приводят к нереалистичным отношениям масс
        exhaust_velocity = specific_impulse * STANDARD_GRAVITY
        mass_ratio = math.exp(delta_v / exhaust_velocity)
        assume(mass_ratio <= 100)  # Ограничиваем практическими пределами для высокой точности
        
        # Создаем двигатель с заданными параметрами
        engine = ChemicalEngine(
            name="Accuracy Test Engine",
            specific_impulse=specific_impulse,
            thrust=thrust,
            fuel_type="Test Propellant"
        )
        
        # Выполняем расчет
        result = self.calculator.calculate_fuel_mass(delta_v, payload_mass, engine)
        
        # Вычисляем точное значение по уравнению Циолковского
        # m_fuel = m_payload × (exp(Δv/(Isp×g₀)) - 1)
        exact_fuel_mass = payload_mass * (mass_ratio - 1)
        
        # Проверяем точность расчета (требуем высокую точность для математических вычислений)
        absolute_error = abs(result.total_fuel - exact_fuel_mass)
        relative_error = absolute_error / exact_fuel_mass if exact_fuel_mass > 0 else 0
        
        # Требуем точность лучше 1e-12 (машинная точность для double precision)
        assert relative_error < 1e-12, (
            f"Недостаточная точность расчета по уравнению Циолковского:\n"
            f"  Входные параметры: Δv={delta_v:.1f} м/с, m_payload={payload_mass:.1f} кг, Isp={specific_impulse:.1f} с\n"
            f"  Расчетная масса топлива: {result.total_fuel:.12f} кг\n"
            f"  Точная масса топлива:    {exact_fuel_mass:.12f} кг\n"
            f"  Абсолютная ошибка:       {absolute_error:.2e} кг\n"
            f"  Относительная ошибка:    {relative_error:.2e} ({relative_error*100:.2e}%)\n"
            f"  Требуемая точность:      < 1e-12"
        )
        
        # Дополнительные проверки точности для компонентов результата
        assert result.delta_v_outbound == delta_v, (
            f"Дельта-V в результате должна точно соответствовать входному значению: "
            f"{result.delta_v_outbound} != {delta_v}"
        )
        
        assert result.total_delta_v == delta_v, (
            f"Общая дельта-V должна соответствовать входному значению для односторонней миссии: "
            f"{result.total_delta_v} != {delta_v}"
        )
        
        assert result.outbound_fuel == result.total_fuel, (
            f"Для односторонней миссии топливо прямого полета должно равняться общему топливу: "
            f"{result.outbound_fuel} != {result.total_fuel}"
        )
        
        assert result.return_fuel is None, (
            "Для односторонней миссии топливо обратного полета должно быть None"
        )
        
        assert result.delta_v_return is None, (
            "Для односторонней миссии дельта-V обратного полета должна быть None"
        )
        
        assert result.engine_used == engine, (
            "Результат должен содержать ссылку на использованный двигатель"
        )
        
        # Проверяем физическую корректность результата
        assert result.total_fuel > 0, (
            f"Масса топлива должна быть положительной: {result.total_fuel}"
        )
        
        assert math.isfinite(result.total_fuel), (
            f"Масса топлива должна быть конечным числом: {result.total_fuel}"
        )
        
        # Проверяем разумность результата (масса топлива не должна быть чрезмерно большой)
        fuel_to_payload_ratio = result.total_fuel / payload_mass
        assert fuel_to_payload_ratio < 100, (
            f"Отношение массы топлива к полезной нагрузке слишком велико: "
            f"{fuel_to_payload_ratio:.1f} (топливо: {result.total_fuel:.1f} кг, "
            f"полезная нагрузка: {payload_mass:.1f} кг)"
        )

    def test_tsiolkovsky_equation_known_values(self):
        """
        Тест с известными значениями для проверки точности.
        """
        # Известный пример: дельта-V = 3000 м/с, Isp = 300 с, масса полезной нагрузки = 1000 кг
        engine = ChemicalEngine(
            name="Test Engine",
            specific_impulse=300,
            thrust=1000000,
            fuel_type="RP-1/LOX"
        )
        
        result = self.calculator.calculate_fuel_mass(3000, 1000, engine)
        
        # Ожидаемый результат по уравнению Циолковского
        # m_fuel = 1000 * (exp(3000/(300*9.80665)) - 1) ≈ 1772.41 кг
        expected_fuel = 1000 * (math.exp(3000 / (300 * STANDARD_GRAVITY)) - 1)
        
        assert abs(result.total_fuel - expected_fuel) < 0.01, (
            f"Ожидалось {expected_fuel:.2f} кг, получено {result.total_fuel:.2f} кг"
        )


class TestFuelCalculatorValidation:
    """Тесты валидации входных параметров."""
    
    def setup_method(self):
        """Настройка для каждого теста."""
        self.calculator = FuelCalculator()
        self.engine = ChemicalEngine(
            name="Test Engine",
            specific_impulse=300,
            thrust=1000000,
            fuel_type="RP-1/LOX"
        )
    
    def test_negative_delta_v_raises_error(self):
        """Тест на отрицательную дельта-V."""
        with pytest.raises(InvalidInputError, match="Дельта-V не может быть отрицательной"):
            self.calculator.calculate_fuel_mass(-1000, 1000, self.engine)
    
    def test_zero_payload_mass_raises_error(self):
        """Тест на нулевую массу полезной нагрузки."""
        with pytest.raises(InvalidInputError, match="Масса полезной нагрузки должна быть положительной"):
            self.calculator.calculate_fuel_mass(3000, 0, self.engine)
    
    def test_negative_payload_mass_raises_error(self):
        """Тест на отрицательную массу полезной нагрузки."""
        with pytest.raises(InvalidInputError, match="Масса полезной нагрузки должна быть положительной"):
            self.calculator.calculate_fuel_mass(3000, -100, self.engine)
    
    def test_unrealistic_delta_v_raises_error(self):
        """Тест на нереалистично высокую дельта-V."""
        with pytest.raises(PhysicsViolationError, match="превышает физически реалистичные пределы"):
            self.calculator.calculate_fuel_mass(60000, 1000, self.engine)
    
    def test_invalid_engine_type_raises_error(self):
        """Тест на некорректный тип двигателя."""
        with pytest.raises(InvalidInputError, match="Двигатель должен быть экземпляром Engine"):
            self.calculator.calculate_fuel_mass(3000, 1000, "not an engine")
    
    def test_non_numeric_delta_v_raises_error(self):
        """Тест на нечисловую дельта-V."""
        with pytest.raises(InvalidInputError, match="Дельта-V должна быть числом"):
            self.calculator.calculate_fuel_mass("3000", 1000, self.engine)
    
    def test_non_numeric_payload_mass_raises_error(self):
        """Тест на нечисловую массу полезной нагрузки."""
        with pytest.raises(InvalidInputError, match="Масса полезной нагрузки должна быть числом"):
            self.calculator.calculate_fuel_mass(3000, "1000", self.engine)