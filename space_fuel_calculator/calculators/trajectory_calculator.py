"""
Калькулятор траекторий для межпланетных полетов.
"""
import math
from typing import Tuple
from ..models.planet import Planet
from ..utils.constants import GRAVITATIONAL_CONSTANT, SOLAR_MASS, ASTRONOMICAL_UNIT


class TrajectoryCalculator:
    """
    Калькулятор для расчета траекторий и дельта-V межпланетных полетов.
    
    Использует принципы орбитальной механики для вычисления энергетических
    требований для перелетов между планетами.
    """
    
    def __init__(self):
        """Инициализация калькулятора траекторий."""
        self.solar_mu = GRAVITATIONAL_CONSTANT * SOLAR_MASS  # Гравитационный параметр Солнца
    
    def calculate_escape_velocity(self, planet: Planet) -> float:
        """
        Рассчитать скорость убегания с планеты.
        
        Args:
            planet: Планета для расчета
            
        Returns:
            Скорость убегания в м/с
            
        Raises:
            ValueError: Если параметры планеты некорректны
        """
        if planet.mass <= 0 or planet.radius <= 0:
            raise ValueError(f"Некорректные параметры планеты: масса={planet.mass}, радиус={planet.radius}")
        
        # v_escape = sqrt(2 * G * M / R)
        mu = GRAVITATIONAL_CONSTANT * planet.mass
        escape_velocity = math.sqrt(2 * mu / planet.radius)
        
        return escape_velocity
    
    def calculate_hohmann_transfer(self, r1: float, r2: float) -> Tuple[float, float]:
        """
        Рассчитать дельта-V для траектории Гомана между двумя орбитами.
        
        Args:
            r1: Радиус начальной орбиты в метрах
            r2: Радиус конечной орбиты в метрах
            
        Returns:
            Кортеж (delta_v1, delta_v2) - дельта-V для начального и конечного маневров в м/с
            
        Raises:
            ValueError: Если радиусы орбит некорректны
        """
        if r1 <= 0 or r2 <= 0:
            raise ValueError(f"Радиусы орбит должны быть положительными: r1={r1}, r2={r2}")
        
        if abs(r1 - r2) < 1000:  # Менее 1 км разности
            return (0.0, 0.0)
        
        # Скорости на круговых орбитах
        v1 = math.sqrt(self.solar_mu / r1)
        v2 = math.sqrt(self.solar_mu / r2)
        
        # Полуось эллипса перехода
        a_transfer = (r1 + r2) / 2
        
        # Скорости на эллиптической траектории перехода
        v_transfer_1 = math.sqrt(self.solar_mu * (2/r1 - 1/a_transfer))
        v_transfer_2 = math.sqrt(self.solar_mu * (2/r2 - 1/a_transfer))
        
        # Дельта-V для маневров
        delta_v1 = abs(v_transfer_1 - v1)
        delta_v2 = abs(v2 - v_transfer_2)
        
        return (delta_v1, delta_v2)
    
    def calculate_delta_v(self, origin: Planet, destination: Planet) -> float:
        """
        Рассчитать общую дельта-V для перелета между планетами.
        
        Включает:
        - Уход с орбиты планеты отправления
        - Траекторию Гомана между орбитами планет
        - Захват на орбиту планеты назначения
        
        Args:
            origin: Планета отправления
            destination: Планета назначения
            
        Returns:
            Общая дельта-V в м/с
            
        Raises:
            ValueError: Если планеты идентичны или параметры некорректны
        """
        if origin.name == destination.name:
            return 0.0
        
        if origin.orbital_radius <= 0 or destination.orbital_radius <= 0:
            raise ValueError("Орбитальные радиусы планет должны быть положительными")
        
        # Дельта-V для ухода с орбиты планеты отправления
        # Используем упрощение: скорость убегания минус орбитальная скорость
        origin_orbital_velocity = math.sqrt(self.solar_mu / origin.orbital_radius)
        escape_delta_v = origin.escape_velocity - origin_orbital_velocity
        if escape_delta_v < 0:
            escape_delta_v = origin.escape_velocity * 0.1  # Минимальная дельта-V для ухода
        
        # Дельта-V для траектории Гомана между планетами
        hohmann_delta_v1, hohmann_delta_v2 = self.calculate_hohmann_transfer(
            origin.orbital_radius, destination.orbital_radius
        )
        
        # Дельта-V для захвата на орбиту планеты назначения
        destination_orbital_velocity = math.sqrt(self.solar_mu / destination.orbital_radius)
        capture_delta_v = destination.escape_velocity - destination_orbital_velocity
        if capture_delta_v < 0:
            capture_delta_v = destination.escape_velocity * 0.1  # Минимальная дельта-V для захвата
        
        # Общая дельта-V
        total_delta_v = escape_delta_v + hohmann_delta_v1 + hohmann_delta_v2 + capture_delta_v
        
        return total_delta_v
    
    def calculate_orbital_velocity(self, planet: Planet) -> float:
        """
        Рассчитать орбитальную скорость планеты вокруг Солнца.
        
        Args:
            planet: Планета для расчета
            
        Returns:
            Орбитальная скорость в м/с
        """
        if planet.orbital_radius <= 0:
            raise ValueError(f"Орбитальный радиус должен быть положительным: {planet.orbital_radius}")
        
        return math.sqrt(self.solar_mu / planet.orbital_radius)