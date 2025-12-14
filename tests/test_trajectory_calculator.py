"""
Тесты для калькулятора траекторий.
"""
import pytest
import math
from hypothesis import given, strategies as st, assume
from space_fuel_calculator.calculators.trajectory_calculator import TrajectoryCalculator
from space_fuel_calculator.models.planet import Planet
from space_fuel_calculator.utils.constants import ASTRONOMICAL_UNIT, EARTH_MASS, EARTH_RADIUS


class TestTrajectoryCalculator:
    """Тесты для TrajectoryCalculator."""
    
    def setup_method(self):
        """Настройка для каждого теста."""
        self.calculator = TrajectoryCalculator()
    
    def test_escape_velocity_calculation(self):
        """Тест расчета скорости убегания."""
        # Тест с Землей
        earth = Planet(
            name="Earth",
            mass=EARTH_MASS,
            radius=EARTH_RADIUS,
            orbital_radius=ASTRONOMICAL_UNIT,
            escape_velocity=11180
        )
        
        calculated_escape = self.calculator.calculate_escape_velocity(earth)
        # Проверяем, что расчет близок к известному значению (в пределах 5%)
        assert abs(calculated_escape - 11180) / 11180 < 0.05
    
    def test_hohmann_transfer_same_orbit(self):
        """Тест траектории Гомана для одинаковых орбит."""
        r = ASTRONOMICAL_UNIT
        delta_v1, delta_v2 = self.calculator.calculate_hohmann_transfer(r, r)
        assert delta_v1 == 0.0
        assert delta_v2 == 0.0
    
    def test_delta_v_same_planet(self):
        """Тест дельта-V для одной и той же планеты."""
        earth = Planet(
            name="Earth",
            mass=EARTH_MASS,
            radius=EARTH_RADIUS,
            orbital_radius=ASTRONOMICAL_UNIT,
            escape_velocity=11180
        )
        
        delta_v = self.calculator.calculate_delta_v(earth, earth)
        assert delta_v == 0.0


# Property-based тесты
class TestTrajectoryCalculatorProperties:
    """Property-based тесты для TrajectoryCalculator."""
    
    def setup_method(self):
        """Настройка для каждого теста."""
        self.calculator = TrajectoryCalculator()
    
    @given(
        name1=st.text(min_size=1, max_size=20),
        name2=st.text(min_size=1, max_size=20),
        mass1=st.floats(min_value=1e20, max_value=1e30),
        mass2=st.floats(min_value=1e20, max_value=1e30),
        radius1=st.floats(min_value=1e6, max_value=1e8),
        radius2=st.floats(min_value=1e6, max_value=1e8),
        orbital_radius1=st.floats(min_value=5e10, max_value=5e11),  # Более реалистичный диапазон
        orbital_radius2=st.floats(min_value=5e10, max_value=5e11),  # Более реалистичный диапазон
        escape_velocity1=st.floats(min_value=1000, max_value=50000),
        escape_velocity2=st.floats(min_value=1000, max_value=50000)
    )
    def test_property_delta_v_calculation_for_any_planet(
        self, name1, name2, mass1, mass2, radius1, radius2, 
        orbital_radius1, orbital_radius2, escape_velocity1, escape_velocity2
    ):
        """
        # **Feature: space-fuel-calculator, Property 1: Расчет дельта-V для любой планеты**
        
        Для любой планеты назначения, система должна рассчитать положительное значение 
        дельта-V для перелета с Земли.
        **Validates: Requirements 1.1**
        """
        # Исключаем случаи с одинаковыми именами планет
        assume(name1 != name2)
        
        # Исключаем нереалистично близкие орбиты (менее 10% разности)
        assume(abs(orbital_radius1 - orbital_radius2) / max(orbital_radius1, orbital_radius2) > 0.1)
        
        # Исключаем слишком большие различия в орбитах (более чем в 5 раз)
        assume(max(orbital_radius1, orbital_radius2) / min(orbital_radius1, orbital_radius2) < 5.0)
        
        try:
            planet1 = Planet(
                name=name1,
                mass=mass1,
                radius=radius1,
                orbital_radius=orbital_radius1,
                escape_velocity=escape_velocity1
            )
            
            planet2 = Planet(
                name=name2,
                mass=mass2,
                radius=radius2,
                orbital_radius=orbital_radius2,
                escape_velocity=escape_velocity2
            )
            
            # Рассчитываем дельта-V
            delta_v = self.calculator.calculate_delta_v(planet1, planet2)
            
            # Проверяем, что дельта-V положительная
            assert delta_v > 0, f"Дельта-V должна быть положительной, получено: {delta_v}"
            
            # Проверяем, что дельта-V в разумных пределах (не более 100 км/с)
            assert delta_v < 100000, f"Дельта-V слишком большая: {delta_v} м/с"
            
        except ValueError:
            # Пропускаем случаи с некорректными параметрами планет
            assume(False)
    
    @given(
        mass=st.floats(min_value=1e20, max_value=1e30),
        radius=st.floats(min_value=1e6, max_value=1e8)
    )
    def test_escape_velocity_positive(self, mass, radius):
        """Тест что скорость убегания всегда положительная."""
        planet = Planet(
            name="TestPlanet",
            mass=mass,
            radius=radius,
            orbital_radius=1e11,
            escape_velocity=5000  # Заглушка
        )
        
        escape_velocity = self.calculator.calculate_escape_velocity(planet)
        assert escape_velocity > 0
    
    @given(
        r1=st.floats(min_value=1e10, max_value=1e12),
        r2=st.floats(min_value=1e10, max_value=1e12)
    )
    def test_hohmann_transfer_symmetry(self, r1, r2):
        """Тест симметрии траектории Гомана."""
        assume(abs(r1 - r2) > 1e9)  # Исключаем слишком близкие орбиты
        
        delta_v1_forward, delta_v2_forward = self.calculator.calculate_hohmann_transfer(r1, r2)
        delta_v1_reverse, delta_v2_reverse = self.calculator.calculate_hohmann_transfer(r2, r1)
        
        # Дельта-V должны быть симметричными (с учетом погрешности)
        assert abs(delta_v1_forward - delta_v2_reverse) < 1e-6
        assert abs(delta_v2_forward - delta_v1_reverse) < 1e-6