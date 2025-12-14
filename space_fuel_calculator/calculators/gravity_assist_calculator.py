"""
Калькулятор гравитационных маневров для экономии топлива.
"""
import math
from typing import List, Tuple, Optional
from dataclasses import dataclass
from ..models.planet import Planet
from ..utils.constants import GRAVITATIONAL_CONSTANT, SOLAR_MASS


@dataclass
class AssistManeuver:
    """
    Данные о гравитационном маневре.
    
    Attributes:
        assist_planet: Планета для маневра
        delta_v_savings: Экономия дельта-V в м/с
        approach_distance: Расстояние сближения с планетой в м
        deflection_angle: Угол отклонения траектории в радианах
    """
    assist_planet: Planet
    delta_v_savings: float
    approach_distance: float
    deflection_angle: float


class GravityAssistCalculator:
    """
    Калькулятор для расчета гравитационных маневров и экономии дельта-V.
    
    Использует принципы орбитальной механики для вычисления возможности
    и эффективности гравитационных маневров при межпланетных полетах.
    """
    
    def __init__(self):
        """Инициализация калькулятора гравитационных маневров."""
        self.solar_mu = GRAVITATIONAL_CONSTANT * SOLAR_MASS
        # Минимальное безопасное расстояние сближения (в радиусах планеты)
        self.min_approach_factor = 2.0
    
    def calculate_sphere_of_influence(self, planet: Planet) -> float:
        """
        Рассчитать сферу влияния планеты (радиус Хилла).
        
        Args:
            planet: Планета для расчета
            
        Returns:
            Радиус сферы влияния в метрах
        """
        if planet.orbital_radius <= 0 or planet.mass <= 0:
            raise ValueError("Некорректные параметры планеты для расчета сферы влияния")
        
        # Упрощенная формула сферы влияния: r_soi = a * (m/3M)^(2/5)
        # где a - орбитальный радиус, m - масса планеты, M - масса Солнца
        mass_ratio = planet.mass / SOLAR_MASS
        soi_radius = planet.orbital_radius * (mass_ratio / 3.0) ** (2.0/5.0)
        
        return soi_radius
    
    def calculate_hyperbolic_excess_velocity(self, v_infinity: float, planet: Planet) -> float:
        """
        Рассчитать гиперболическую избыточную скорость при подлете к планете.
        
        Args:
            v_infinity: Скорость на бесконечности относительно планеты в м/с
            planet: Планета для маневра
            
        Returns:
            Скорость в перицентре гиперболы в м/с
        """
        if v_infinity < 0:
            raise ValueError("Скорость на бесконечности должна быть неотрицательной")
        
        planet_mu = GRAVITATIONAL_CONSTANT * planet.mass
        min_approach = planet.radius * self.min_approach_factor
        
        # v_periapsis = sqrt(v_infinity^2 + 2*mu/r_periapsis)
        v_periapsis = math.sqrt(v_infinity**2 + 2 * planet_mu / min_approach)
        
        return v_periapsis
    
    def calculate_deflection_angle(self, v_infinity: float, planet: Planet, 
                                 approach_distance: Optional[float] = None) -> float:
        """
        Рассчитать угол отклонения траектории при гравитационном маневре.
        
        Args:
            v_infinity: Скорость на бесконечности относительно планеты в м/с
            planet: Планета для маневра
            approach_distance: Расстояние сближения (по умолчанию минимальное безопасное)
            
        Returns:
            Угол отклонения в радианах
        """
        if v_infinity <= 0:
            raise ValueError("Скорость на бесконечности должна быть положительной")
        
        if approach_distance is None:
            approach_distance = planet.radius * self.min_approach_factor
        
        if approach_distance <= planet.radius:
            raise ValueError("Расстояние сближения не может быть меньше радиуса планеты")
        
        planet_mu = GRAVITATIONAL_CONSTANT * planet.mass
        
        # Угол отклонения: delta = 2 * arcsin(mu / (r * v_infinity^2))
        # Но используем более точную формулу через эксцентриситет
        specific_energy = v_infinity**2 / 2
        semi_major_axis = -planet_mu / (2 * specific_energy)  # Отрицательная для гиперболы
        
        eccentricity = math.sqrt(1 + (approach_distance * v_infinity**2) / planet_mu)
        
        # Угол отклонения через эксцентриситет
        deflection_angle = 2 * math.asin(1 / eccentricity)
        
        return deflection_angle
    
    def calculate_assist_delta_v(self, v_approach: float, planet: Planet, 
                               deflection_angle: float) -> float:
        """
        Рассчитать изменение скорости от гравитационного маневра.
        
        Args:
            v_approach: Скорость подлета к планете в м/с
            planet: Планета для маневра
            deflection_angle: Угол отклонения траектории в радианах
            
        Returns:
            Изменение скорости в м/с
        """
        if v_approach <= 0:
            raise ValueError("Скорость подлета должна быть положительной")
        
        if not (0 <= deflection_angle <= math.pi):
            raise ValueError("Угол отклонения должен быть от 0 до π радиан")
        
        # Изменение скорости при гравитационном маневре
        # Δv = 2 * v_infinity * sin(δ/2), где δ - угол отклонения
        delta_v = 2 * v_approach * math.sin(deflection_angle / 2)
        
        return delta_v
    
    def is_maneuver_possible(self, origin: Planet, destination: Planet, 
                           assist_planet: Planet) -> bool:
        """
        Проверить возможность гравитационного маневра с геометрической точки зрения.
        
        Args:
            origin: Планета отправления
            destination: Планета назначения
            assist_planet: Планета для маневра
            
        Returns:
            True, если маневр геометрически возможен
        """
        # Исключаем планеты отправления и назначения
        if (assist_planet.name == origin.name or 
            assist_planet.name == destination.name):
            return False
        
        # Простая проверка: планета маневра должна быть между отправлением и назначением
        # или обеспечивать выгодную траекторию
        
        r_origin = origin.orbital_radius
        r_destination = destination.orbital_radius
        r_assist = assist_planet.orbital_radius
        
        # Маневр возможен, если планета маневра находится в "разумном" положении
        min_radius = min(r_origin, r_destination)
        max_radius = max(r_origin, r_destination)
        
        # Планета маневра должна быть в пределах расширенного диапазона орбит
        return (min_radius * 0.5 <= r_assist <= max_radius * 2.0)
    
    def find_optimal_assists(self, origin: Planet, destination: Planet, 
                           available_planets: List[Planet]) -> List[AssistManeuver]:
        """
        Найти оптимальные гравитационные маневры для заданной траектории.
        
        Args:
            origin: Планета отправления
            destination: Планета назначения
            available_planets: Список доступных планет для маневров
            
        Returns:
            Список возможных маневров, отсортированный по экономии дельта-V
        """
        maneuvers = []
        
        for planet in available_planets:
            # Исключаем планеты отправления и назначения
            if planet.name == origin.name or planet.name == destination.name:
                continue
            
            # Проверяем возможность маневра
            if not self.is_maneuver_possible(origin, destination, planet):
                continue
            
            try:
                # Более реалистичная оценка экономии дельта-V
                # Используем орбитальные скорости планет
                v_origin = math.sqrt(self.solar_mu / origin.orbital_radius)
                v_destination = math.sqrt(self.solar_mu / destination.orbital_radius)
                v_assist = math.sqrt(self.solar_mu / planet.orbital_radius)
                
                # Приблизительная скорость подлета (относительная скорость)
                v_approach = abs(v_assist - v_origin) * 0.3  # Более консервативная оценка
                
                # Ограничиваем максимальный угол отклонения
                max_deflection = min(
                    self.calculate_deflection_angle(v_approach, planet),
                    math.pi / 3  # Максимум 60 градусов для реалистичности
                )
                
                # Экономия дельта-V (консервативная оценка)
                # Ограничиваем экономию максимум 20% от скорости подлета
                raw_savings = self.calculate_assist_delta_v(v_approach, planet, max_deflection)
                delta_v_savings = min(raw_savings, v_approach * 0.2)
                
                # Минимальное расстояние сближения
                approach_distance = planet.radius * self.min_approach_factor
                
                maneuver = AssistManeuver(
                    assist_planet=planet,
                    delta_v_savings=delta_v_savings,
                    approach_distance=approach_distance,
                    deflection_angle=max_deflection
                )
                
                maneuvers.append(maneuver)
                
            except (ValueError, ZeroDivisionError):
                # Пропускаем планеты с некорректными параметрами
                continue
        
        # Сортируем по убыванию экономии дельта-V
        maneuvers.sort(key=lambda m: m.delta_v_savings, reverse=True)
        
        return maneuvers
    
    def calculate_total_savings(self, maneuvers: List[AssistManeuver]) -> float:
        """
        Рассчитать общую экономию дельта-V от последовательности маневров.
        
        Args:
            maneuvers: Список маневров
            
        Returns:
            Общая экономия дельта-V в м/с
        """
        if not maneuvers:
            return 0.0
        
        # Простое суммирование (в реальности взаимодействие сложнее)
        total_savings = sum(maneuver.delta_v_savings for maneuver in maneuvers)
        
        # Применяем коэффициент эффективности для множественных маневров
        efficiency_factor = 1.0 - 0.1 * (len(maneuvers) - 1)  # Снижение на 10% за каждый дополнительный маневр
        efficiency_factor = max(0.5, efficiency_factor)  # Минимум 50% эффективности
        
        return total_savings * efficiency_factor