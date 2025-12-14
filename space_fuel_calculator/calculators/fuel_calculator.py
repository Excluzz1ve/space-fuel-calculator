"""
Основной калькулятор топлива для космических полетов.
"""
import math
from dataclasses import dataclass
from typing import Optional, Dict, Any

from ..models.engine import Engine, ChemicalEngine, IonEngine, NuclearEngine
from ..models.planet import Planet
from ..utils.exceptions import InvalidInputError, PhysicsViolationError


# Стандартное ускорение свободного падения на Земле (м/с²)
STANDARD_GRAVITY = 9.80665


@dataclass
class FuelResult:
    """
    Результат расчета топлива.
    
    Attributes:
        outbound_fuel: Топливо для полета туда в кг
        return_fuel: Топливо для обратного полета в кг (если применимо)
        total_fuel: Общая масса топлива в кг
        delta_v_outbound: Дельта-V для полета туда в м/с
        delta_v_return: Дельта-V для обратного полета в м/с (если применимо)
        total_delta_v: Общая дельта-V в м/с
        engine_used: Использованный двигатель
        trajectory_type: Тип траектории
    """
    outbound_fuel: float  # kg
    return_fuel: Optional[float]  # kg
    total_fuel: float  # kg
    delta_v_outbound: float  # m/s
    delta_v_return: Optional[float]  # m/s
    total_delta_v: float  # m/s
    engine_used: Engine
    trajectory_type: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразование в словарь для сериализации."""
        return {
            'outbound_fuel': self.outbound_fuel,
            'return_fuel': self.return_fuel,
            'total_fuel': self.total_fuel,
            'delta_v_outbound': self.delta_v_outbound,
            'delta_v_return': self.delta_v_return,
            'total_delta_v': self.total_delta_v,
            'engine_used': self.engine_used.to_dict(),
            'trajectory_type': self.trajectory_type
        }


class FuelCalculator:
    """
    Основной калькулятор топлива для космических полетов.
    
    Использует уравнение Циолковского для расчета необходимой массы топлива
    на основе требуемой дельта-V, массы полезной нагрузки и характеристик двигателя.
    """
    
    def __init__(self):
        """Инициализация калькулятора топлива."""
        pass
    
    def calculate_fuel_mass(self, delta_v: float, payload_mass: float, engine: Engine) -> FuelResult:
        """
        Рассчитывает массу топлива по уравнению Циолковского.
        
        Уравнение Циолковского: m_fuel = m_payload × (exp(Δv/(Isp×g₀)) - 1)
        
        Args:
            delta_v: Требуемая дельта-V в м/с
            payload_mass: Масса полезной нагрузки в кг
            engine: Двигатель для расчета
            
        Returns:
            FuelResult с результатами расчета
            
        Raises:
            InvalidInputError: При некорректных входных параметрах
            PhysicsViolationError: При нарушении физических ограничений
        """
        # Валидация входных параметров
        self._validate_fuel_calculation_inputs(delta_v, payload_mass, engine)
        
        # Расчет эффективной скорости истечения
        exhaust_velocity = engine.specific_impulse * STANDARD_GRAVITY
        
        # Проверка на физическую реалистичность дельта-V
        if delta_v > 50000:  # 50 км/с - разумный верхний предел
            raise PhysicsViolationError(
                f"Требуемая дельта-V {delta_v:.0f} м/с превышает физически реалистичные пределы (>50 км/с)"
            )
        
        # Расчет отношения масс по уравнению Циолковского
        try:
            mass_ratio = math.exp(delta_v / exhaust_velocity)
        except OverflowError:
            raise PhysicsViolationError(
                f"Слишком большая дельта-V {delta_v:.0f} м/с для данного двигателя "
                f"(Isp={engine.specific_impulse:.0f}с) приводит к переполнению при расчете"
            )
        
        # Проверка на разумность отношения масс
        if mass_ratio > 1000:  # Практический предел для ракет
            raise PhysicsViolationError(
                f"Отношение масс {mass_ratio:.1f} превышает практические пределы ракетостроения (>1000)"
            )
        
        # Расчет массы топлива
        fuel_mass = payload_mass * (mass_ratio - 1)
        
        return FuelResult(
            outbound_fuel=fuel_mass,
            return_fuel=None,
            total_fuel=fuel_mass,
            delta_v_outbound=delta_v,
            delta_v_return=None,
            total_delta_v=delta_v,
            engine_used=engine,
            trajectory_type="single_burn"
        )
    
    def calculate_round_trip_fuel(self, destination: Planet, payload_mass: float, engine: Engine) -> FuelResult:
        """
        Рассчитывает топливо для полета туда и обратно с учетом гравитации планеты.
        
        Args:
            destination: Планета назначения
            payload_mass: Масса полезной нагрузки в кг
            engine: Двигатель для расчета
            
        Returns:
            FuelResult с результатами расчета туда и обратно
            
        Raises:
            InvalidInputError: При некорректных входных параметрах
            PhysicsViolationError: При нарушении физических ограничений
        """
        # Валидация входных параметров
        self._validate_round_trip_inputs(destination, payload_mass, engine)
        
        # Расчет дельта-V для полета от Земли до планеты назначения
        # Используем упрощенную модель: дельта-V = sqrt(GM/r_earth) + sqrt(GM/r_destination)
        # где GM - гравитационный параметр Солнца, r - орбитальный радиус
        
        # Константы (упрощенные значения)
        GM_SUN = 1.327e20  # м³/с² - гравитационный параметр Солнца
        EARTH_ORBITAL_RADIUS = 1.496e11  # м - среднее расстояние от Земли до Солнца
        
        # Дельта-V для выхода с орбиты Земли
        delta_v_earth_escape = math.sqrt(GM_SUN / EARTH_ORBITAL_RADIUS)
        
        # Дельта-V для входа на орбиту планеты назначения
        delta_v_destination_capture = math.sqrt(GM_SUN / destination.orbital_radius)
        
        # Общая дельта-V для прямого полета (упрощенная модель Гомана)
        delta_v_outbound = abs(delta_v_destination_capture - delta_v_earth_escape)
        
        # Добавляем дельта-V для преодоления гравитации планеты при взлете
        delta_v_planet_escape = destination.escape_velocity
        
        # Дельта-V для обратного полета (симметричная)
        delta_v_return = delta_v_outbound + delta_v_planet_escape
        
        # Общая дельта-V
        total_delta_v = delta_v_outbound + delta_v_return
        
        # Расчет топлива для прямого полета
        outbound_result = self.calculate_fuel_mass(delta_v_outbound, payload_mass, engine)
        outbound_fuel = outbound_result.total_fuel
        
        # Расчет топлива для обратного полета
        # Масса для обратного полета включает полезную нагрузку + топливо для обратного полета
        return_result = self.calculate_fuel_mass(delta_v_return, payload_mass, engine)
        return_fuel = return_result.total_fuel
        
        # Общая масса топлива
        total_fuel = outbound_fuel + return_fuel
        
        return FuelResult(
            outbound_fuel=outbound_fuel,
            return_fuel=return_fuel,
            total_fuel=total_fuel,
            delta_v_outbound=delta_v_outbound,
            delta_v_return=delta_v_return,
            total_delta_v=total_delta_v,
            engine_used=engine,
            trajectory_type="round_trip"
        )
    
    def _validate_fuel_calculation_inputs(self, delta_v: float, payload_mass: float, engine: Engine) -> None:
        """
        Валидирует входные параметры для расчета топлива.
        
        Args:
            delta_v: Требуемая дельта-V в м/с
            payload_mass: Масса полезной нагрузки в кг
            engine: Двигатель для расчета
            
        Raises:
            InvalidInputError: При некорректных входных параметрах
        """
        if not isinstance(delta_v, (int, float)):
            raise InvalidInputError(f"Дельта-V должна быть числом, получено: {type(delta_v)}")
        
        if not isinstance(payload_mass, (int, float)):
            raise InvalidInputError(f"Масса полезной нагрузки должна быть числом, получено: {type(payload_mass)}")
        
        if not hasattr(engine, 'specific_impulse') or not hasattr(engine, 'thrust'):
            raise InvalidInputError(f"Двигатель должен быть экземпляром Engine, получено: {type(engine)}")
        
        # Проверка на NaN и бесконечность
        if math.isnan(delta_v):
            raise InvalidInputError(f"Дельта-V не может быть NaN")
        
        if math.isinf(delta_v):
            raise InvalidInputError(f"Дельта-V не может быть бесконечностью")
        
        if math.isnan(payload_mass):
            raise InvalidInputError(f"Масса полезной нагрузки не может быть NaN")
        
        if math.isinf(payload_mass):
            raise InvalidInputError(f"Масса полезной нагрузки не может быть бесконечностью")
        
        if delta_v < 0:
            raise InvalidInputError(f"Дельта-V не может быть отрицательной, получено: {delta_v}")
        
        if payload_mass <= 0:
            raise InvalidInputError(f"Масса полезной нагрузки должна быть положительной, получено: {payload_mass}")
        
        if engine.specific_impulse <= 0:
            raise InvalidInputError(f"Удельный импульс двигателя должен быть положительным, получено: {engine.specific_impulse}")
    
    def _validate_round_trip_inputs(self, destination: Planet, payload_mass: float, engine: Engine) -> None:
        """
        Валидирует входные параметры для расчета полета туда и обратно.
        
        Args:
            destination: Планета назначения
            payload_mass: Масса полезной нагрузки в кг
            engine: Двигатель для расчета
            
        Raises:
            InvalidInputError: При некорректных входных параметрах
        """
        if not isinstance(destination, Planet):
            raise InvalidInputError(f"Планета назначения должна быть экземпляром Planet, получено: {type(destination)}")
        
        if not isinstance(payload_mass, (int, float)):
            raise InvalidInputError(f"Масса полезной нагрузки должна быть числом, получено: {type(payload_mass)}")
        
        if not hasattr(engine, 'specific_impulse') or not hasattr(engine, 'thrust'):
            raise InvalidInputError(f"Двигатель должен быть экземпляром Engine, получено: {type(engine)}")
        
        # Проверка на NaN и бесконечность
        if math.isnan(payload_mass):
            raise InvalidInputError(f"Масса полезной нагрузки не может быть NaN")
        
        if math.isinf(payload_mass):
            raise InvalidInputError(f"Масса полезной нагрузки не может быть бесконечностью")
        
        if payload_mass <= 0:
            raise InvalidInputError(f"Масса полезной нагрузки должна быть положительной, получено: {payload_mass}")
        
        if engine.specific_impulse <= 0:
            raise InvalidInputError(f"Удельный импульс двигателя должен быть положительным, получено: {engine.specific_impulse}")