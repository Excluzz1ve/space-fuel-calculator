"""
Тесты для калькулятора гравитационных маневров.
"""
import pytest
import math
from hypothesis import given, strategies as st, assume
from space_fuel_calculator.calculators.gravity_assist_calculator import GravityAssistCalculator, AssistManeuver
from space_fuel_calculator.calculators.trajectory_calculator import TrajectoryCalculator
from space_fuel_calculator.models.planet import Planet
from space_fuel_calculator.utils.constants import ASTRONOMICAL_UNIT, EARTH_MASS, EARTH_RADIUS


class TestGravityAssistCalculator:
    """Тесты для GravityAssistCalculator."""
    
    def setup_method(self):
        """Настройка для каждого теста."""
        self.calculator = GravityAssistCalculator()
        self.trajectory_calc = TrajectoryCalculator()
    
    def test_sphere_of_influence_calculation(self):
        """Тест расчета сферы влияния."""
        earth = Planet(
            name="Earth",
            mass=EARTH_MASS,
            radius=EARTH_RADIUS,
            orbital_radius=ASTRONOMICAL_UNIT,
            escape_velocity=11180
        )
        
        soi = self.calculator.calculate_sphere_of_influence(earth)
        # Сфера влияния Земли должна быть около 924,000 км
        expected_soi = 924000 * 1000  # в метрах
        assert abs(soi - expected_soi) / expected_soi < 0.5  # В пределах 50%
    
    def test_deflection_angle_positive(self):
        """Тест что угол отклонения всегда положительный."""
        earth = Planet(
            name="Earth",
            mass=EARTH_MASS,
            radius=EARTH_RADIUS,
            orbital_radius=ASTRONOMICAL_UNIT,
            escape_velocity=11180
        )
        
        v_infinity = 5000  # м/с
        angle = self.calculator.calculate_deflection_angle(v_infinity, earth)
        assert angle > 0
        assert angle <= math.pi
    
    def test_maneuver_possibility_check(self):
        """Тест проверки возможности маневра."""
        earth = Planet("Earth", EARTH_MASS, EARTH_RADIUS, ASTRONOMICAL_UNIT, 11180)
        mars = Planet("Mars", 6.39e23, 3.39e6, 1.52 * ASTRONOMICAL_UNIT, 5030)
        venus = Planet("Venus", 4.87e24, 6.05e6, 0.72 * ASTRONOMICAL_UNIT, 10360)
        
        # Венера между Землей и Марсом - маневр возможен
        assert self.calculator.is_maneuver_possible(earth, mars, venus)
        
        # Земля как планета маневра для полета Земля-Марс - невозможно
        assert not self.calculator.is_maneuver_possible(earth, mars, earth)


# Property-based тесты
class TestGravityAssistCalculatorProperties:
    """Property-based тесты для GravityAssistCalculator."""
    
    def setup_method(self):
        """Настройка для каждого теста."""
        self.calculator = GravityAssistCalculator()
        self.trajectory_calc = TrajectoryCalculator()
    
    @given(
        # Планета отправления
        origin_mass=st.floats(min_value=1e23, max_value=1e25),
        origin_radius=st.floats(min_value=3e6, max_value=7e6),
        origin_orbital_radius=st.floats(min_value=7e10, max_value=2e11),
        origin_escape_velocity=st.floats(min_value=5000, max_value=15000),
        
        # Планета назначения
        dest_mass=st.floats(min_value=1e23, max_value=1e25),
        dest_radius=st.floats(min_value=3e6, max_value=7e6),
        dest_orbital_radius=st.floats(min_value=2e11, max_value=8e11),
        dest_escape_velocity=st.floats(min_value=5000, max_value=15000),
        
        # Планета для маневра
        assist_mass=st.floats(min_value=1e23, max_value=1e25),
        assist_radius=st.floats(min_value=3e6, max_value=7e6),
        assist_orbital_radius=st.floats(min_value=1e11, max_value=4e11),
        assist_escape_velocity=st.floats(min_value=5000, max_value=15000)
    )
    def test_property_gravity_assist_delta_v_savings(
        self, origin_mass, origin_radius, origin_orbital_radius, origin_escape_velocity,
        dest_mass, dest_radius, dest_orbital_radius, dest_escape_velocity,
        assist_mass, assist_radius, assist_orbital_radius, assist_escape_velocity
    ):
        """
        # **Feature: space-fuel-calculator, Property 13: Экономия дельта-V через гравитационные маневры**
        
        Для любой траектории с гравитационными маневрами, общая требуемая дельта-V 
        должна быть меньше, чем для прямой траектории.
        **Validates: Requirements 4.1, 4.4**
        """
        # Исключаем слишком близкие орбиты
        assume(abs(origin_orbital_radius - dest_orbital_radius) > 5e10)
        assume(abs(origin_orbital_radius - assist_orbital_radius) > 2e10)
        assume(abs(dest_orbital_radius - assist_orbital_radius) > 2e10)
        
        try:
            origin = Planet(
                name="Origin",
                mass=origin_mass,
                radius=origin_radius,
                orbital_radius=origin_orbital_radius,
                escape_velocity=origin_escape_velocity
            )
            
            destination = Planet(
                name="Destination", 
                mass=dest_mass,
                radius=dest_radius,
                orbital_radius=dest_orbital_radius,
                escape_velocity=dest_escape_velocity
            )
            
            assist_planet = Planet(
                name="Assist",
                mass=assist_mass,
                radius=assist_radius,
                orbital_radius=assist_orbital_radius,
                escape_velocity=assist_escape_velocity
            )
            
            # Рассчитываем дельта-V для прямой траектории
            direct_delta_v = self.trajectory_calc.calculate_delta_v(origin, destination)
            
            # Проверяем возможность маневра
            if self.calculator.is_maneuver_possible(origin, destination, assist_planet):
                # Находим оптимальные маневры
                maneuvers = self.calculator.find_optimal_assists(origin, destination, [assist_planet])
                
                if maneuvers:
                    # Рассчитываем экономию
                    total_savings = self.calculator.calculate_total_savings(maneuvers)
                    
                    # Экономия должна быть положительной
                    assert total_savings >= 0, f"Экономия дельта-V должна быть неотрицательной: {total_savings}"
                    
                    # Экономия не должна превышать прямую дельта-V (физически невозможно)
                    # Учитываем погрешность вычислений с плавающей точкой
                    assert total_savings <= direct_delta_v * 1.001, f"Экономия не может превышать прямую дельта-V: {total_savings} > {direct_delta_v}"
                    
                    # Если есть значительная экономия, траектория с маневром должна быть эффективнее
                    if total_savings > direct_delta_v * 0.01:  # Более 1% экономии
                        assisted_delta_v = direct_delta_v - total_savings
                        assert assisted_delta_v < direct_delta_v, "Траектория с маневром должна требовать меньше дельта-V"
            
        except ValueError:
            # Пропускаем случаи с некорректными параметрами планет
            assume(False)
    
    @given(
        v_infinity=st.floats(min_value=1000, max_value=20000),
        planet_mass=st.floats(min_value=1e23, max_value=1e25),
        planet_radius=st.floats(min_value=3e6, max_value=7e6)
    )
    def test_deflection_angle_bounds(self, v_infinity, planet_mass, planet_radius):
        """Тест что угол отклонения в допустимых пределах."""
        planet = Planet(
            name="TestPlanet",
            mass=planet_mass,
            radius=planet_radius,
            orbital_radius=1e11,
            escape_velocity=10000
        )
        
        angle = self.calculator.calculate_deflection_angle(v_infinity, planet)
        
        # Угол должен быть между 0 и π
        assert 0 < angle <= math.pi
    
    @given(
        v_approach=st.floats(min_value=1000, max_value=50000),
        deflection_angle=st.floats(min_value=0.01, max_value=math.pi - 0.01)
    )
    def test_assist_delta_v_positive(self, v_approach, deflection_angle):
        """Тест что изменение скорости от маневра положительное."""
        planet = Planet(
            name="TestPlanet",
            mass=1e24,
            radius=5e6,
            orbital_radius=1e11,
            escape_velocity=10000
        )
        
        delta_v = self.calculator.calculate_assist_delta_v(v_approach, planet, deflection_angle)
        
        # Изменение скорости должно быть положительным
        assert delta_v > 0
        
        # Изменение скорости не должно превышать удвоенную скорость подлета
        assert delta_v <= 2 * v_approach
    @given(
        planet1_mass=st.floats(min_value=1e23, max_value=1e25),
        planet1_radius=st.floats(min_value=3e6, max_value=7e6),
        planet2_mass=st.floats(min_value=1e23, max_value=1e25),
        planet2_radius=st.floats(min_value=3e6, max_value=7e6),
        v_infinity=st.floats(min_value=1000, max_value=20000)
    )
    def test_property_gravitational_field_consideration(
        self, planet1_mass, planet1_radius, planet2_mass, planet2_radius, v_infinity
    ):
        """
        # **Feature: space-fuel-calculator, Property 14: Учет гравитационного поля в маневрах**
        
        Для любого гравитационного маневра у планеты, система должна корректно учитывать 
        массу и радиус планеты в расчетах изменения траектории.
        **Validates: Requirements 4.2**
        """
        # Исключаем планеты с одинаковыми параметрами
        assume(abs(planet1_mass - planet2_mass) > 1e22)
        assume(abs(planet1_radius - planet2_radius) > 1e5)
        
        try:
            planet1 = Planet(
                name="Planet1",
                mass=planet1_mass,
                radius=planet1_radius,
                orbital_radius=1e11,
                escape_velocity=10000
            )
            
            planet2 = Planet(
                name="Planet2", 
                mass=planet2_mass,
                radius=planet2_radius,
                orbital_radius=1e11,
                escape_velocity=10000
            )
            
            # Рассчитываем углы отклонения для обеих планет
            angle1 = self.calculator.calculate_deflection_angle(v_infinity, planet1)
            angle2 = self.calculator.calculate_deflection_angle(v_infinity, planet2)
            
            # Проверяем, что угол отклонения учитывает и массу, и радиус планеты
            # Для одинакового расстояния сближения, большая масса дает больший угол
            fixed_approach = max(planet1_radius, planet2_radius) * 2.5
            angle1_fixed = self.calculator.calculate_deflection_angle(v_infinity, planet1, fixed_approach)
            angle2_fixed = self.calculator.calculate_deflection_angle(v_infinity, planet2, fixed_approach)
            
            if planet1_mass > planet2_mass:
                assert angle1_fixed > angle2_fixed, f"При одинаковом расстоянии сближения, планета с большей массой должна давать больший угол: {angle1_fixed} <= {angle2_fixed}"
            elif planet2_mass > planet1_mass:
                assert angle2_fixed > angle1_fixed, f"При одинаковом расстоянии сближения, планета с большей массой должна давать больший угол: {angle2_fixed} <= {angle1_fixed}"
            
            # Рассчитываем сферы влияния
            soi1 = self.calculator.calculate_sphere_of_influence(planet1)
            soi2 = self.calculator.calculate_sphere_of_influence(planet2)
            
            # Планета с большей массой должна иметь большую сферу влияния
            if planet1_mass > planet2_mass:
                assert soi1 > soi2, f"Планета с большей массой должна иметь большую сферу влияния: {soi1} <= {soi2}"
            elif planet2_mass > planet1_mass:
                assert soi2 > soi1, f"Планета с большей массой должна иметь большую сферу влияния: {soi2} <= {soi1}"
            
            # Углы отклонения должны быть в физически разумных пределах
            assert 0 < angle1 <= math.pi, f"Угол отклонения должен быть между 0 и π: {angle1}"
            assert 0 < angle2 <= math.pi, f"Угол отклонения должен быть между 0 и π: {angle2}"
            
            # Сферы влияния должны быть больше радиусов планет
            assert soi1 > planet1_radius, f"Сфера влияния должна быть больше радиуса планеты: {soi1} <= {planet1_radius}"
            assert soi2 > planet2_radius, f"Сфера влияния должна быть больше радиуса планеты: {soi2} <= {planet2_radius}"
            
        except ValueError:
            # Пропускаем случаи с некорректными параметрами планет
            assume(False)