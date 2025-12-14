"""
База данных планет Солнечной системы с орбитальными параметрами.

Данные основаны на актуальных астрономических измерениях NASA/JPL.
Источники:
- NASA Planetary Fact Sheet: https://nssdc.gsfc.nasa.gov/planetary/factsheet/
- JPL Solar System Dynamics: https://ssd.jpl.nasa.gov/
- IAU 2015 Resolution B3 (астрономическая единица)

Точность данных:
- Массы планет: ±0.1% для внутренних планет, ±1% для внешних
- Радиусы: ±0.01% для всех планет
- Орбитальные радиусы: средние значения (большие полуоси)
- Скорости убегания: рассчитаны по формуле v = √(2GM/R)
"""
from typing import Dict, List, Tuple
from ..models.planet import Planet
import math


# Физические константы
G = 6.67430e-11  # Гравитационная постоянная, м³/(кг·с²)
AU = 1.495978707e11  # Астрономическая единица, м (точное значение IAU 2012)


def _calculate_escape_velocity(mass: float, radius: float) -> float:
    """
    Рассчитывает скорость убегания для планеты.
    
    Args:
        mass: Масса планеты в кг
        radius: Радиус планеты в м
        
    Returns:
        Скорость убегания в м/с
    """
    return math.sqrt(2 * G * mass / radius)


def _validate_astronomical_data(planet: Planet) -> bool:
    """
    Валидирует астрономические данные планеты на физическую реалистичность.
    
    Args:
        planet: Объект планеты для валидации
        
    Returns:
        True если данные корректны
        
    Raises:
        ValueError: Если данные не проходят валидацию
    """
    # Проверка плотности (должна быть разумной для планет)
    volume = (4/3) * math.pi * (planet.radius ** 3)
    density = planet.mass / volume
    
    if density < 500 or density > 15000:  # кг/м³
        raise ValueError(f"Нереалистичная плотность для {planet.name}: {density:.0f} кг/м³")
    
    # Проверка соответствия скорости убегания
    calculated_escape = _calculate_escape_velocity(planet.mass, planet.radius)
    relative_error = abs(planet.escape_velocity - calculated_escape) / calculated_escape
    
    if relative_error > 0.05:  # 5% допустимая погрешность
        raise ValueError(
            f"Несоответствие скорости убегания для {planet.name}: "
            f"указано {planet.escape_velocity:.0f} м/с, рассчитано {calculated_escape:.0f} м/с"
        )
    
    # Проверка орбитального радиуса (должен быть в пределах Солнечной системы)
    if planet.orbital_radius < 0.3 * AU or planet.orbital_radius > 50 * AU:
        raise ValueError(f"Орбитальный радиус {planet.name} вне пределов Солнечной системы")
    
    return True


# Планеты Солнечной системы с точными параметрами
# Данные обновлены по состоянию на 2024 год
PLANETS_DATA = {
    "mercury": Planet(
        name="Меркурий",
        mass=3.3011e23,  # kg ±0.0015e23
        radius=2.4397e6,  # m (средний радиус)
        orbital_radius=0.387098 * AU,  # 5.790905e10 m (большая полуось)
        escape_velocity=4250  # m/s
    ),
    "venus": Planet(
        name="Венера", 
        mass=4.8675e24,  # kg ±0.0006e24
        radius=6.0518e6,  # m (средний радиус)
        orbital_radius=0.723332 * AU,  # 1.082089e11 m (большая полуось)
        escape_velocity=10360  # m/s
    ),
    "earth": Planet(
        name="Земля",
        mass=5.9724e24,  # kg ±0.0006e24
        radius=6.3781e6,  # m (средний радиус)
        orbital_radius=1.000000 * AU,  # 1.495978707e11 m (по определению)
        escape_velocity=11186  # m/s
    ),
    "mars": Planet(
        name="Марс",
        mass=6.4171e23,  # kg ±0.0003e23
        radius=3.3972e6,  # m (средний радиус)
        orbital_radius=1.523679 * AU,  # 2.279391e11 m (большая полуось)
        escape_velocity=5027  # m/s
    ),
    "jupiter": Planet(
        name="Юпитер",
        mass=1.8982e27,  # kg ±0.0019e27
        radius=7.1492e7,  # m (экваториальный радиус)
        orbital_radius=5.204267 * AU,  # 7.785472e11 m (большая полуось)
        escape_velocity=59500  # m/s
    ),
    "saturn": Planet(
        name="Сатурн",
        mass=5.6834e26,  # kg ±0.0006e26
        radius=6.0268e7,  # m (экваториальный радиус)
        orbital_radius=9.582017 * AU,  # 1.433449e12 m (большая полуось)
        escape_velocity=35500  # m/s
    ),
    "uranus": Planet(
        name="Уран",
        mass=8.6810e25,  # kg ±0.0013e25
        radius=2.5559e7,  # m (экваториальный радиус)
        orbital_radius=19.229411 * AU,  # 2.876679e12 m (большая полуось)
        escape_velocity=21300  # m/s
    ),
    "neptune": Planet(
        name="Нептун",
        mass=1.02413e26,  # kg ±0.00003e26
        radius=2.4764e7,  # m (экваториальный радиус)
        orbital_radius=30.103658 * AU,  # 4.503443e12 m (большая полуось)
        escape_velocity=23500  # m/s
    )
}

# Дополнительные астрономические данные для справки
PLANET_METADATA = {
    "mercury": {
        "orbital_period_days": 87.97,
        "rotation_period_hours": 1407.6,
        "surface_gravity": 3.7,  # m/s²
        "atmosphere": "Практически отсутствует",
        "moons": 0
    },
    "venus": {
        "orbital_period_days": 224.70,
        "rotation_period_hours": -5832.5,  # ретроградное вращение
        "surface_gravity": 8.87,  # m/s²
        "atmosphere": "CO₂ (96.5%), N₂ (3.5%)",
        "moons": 0
    },
    "earth": {
        "orbital_period_days": 365.26,
        "rotation_period_hours": 23.93,
        "surface_gravity": 9.80665,  # m/s² (стандартное значение)
        "atmosphere": "N₂ (78%), O₂ (21%)",
        "moons": 1
    },
    "mars": {
        "orbital_period_days": 686.98,
        "rotation_period_hours": 24.62,
        "surface_gravity": 3.71,  # m/s²
        "atmosphere": "CO₂ (95.3%), N₂ (2.7%)",
        "moons": 2
    },
    "jupiter": {
        "orbital_period_days": 4332.59,
        "rotation_period_hours": 9.93,
        "surface_gravity": 24.79,  # m/s² (на уровне 1 бар)
        "atmosphere": "H₂ (89%), He (10%)",
        "moons": 95  # по состоянию на 2024
    },
    "saturn": {
        "orbital_period_days": 10759.22,
        "rotation_period_hours": 10.66,
        "surface_gravity": 10.44,  # m/s² (на уровне 1 бар)
        "atmosphere": "H₂ (96%), He (3%)",
        "moons": 146  # по состоянию на 2024
    },
    "uranus": {
        "orbital_period_days": 30688.5,
        "rotation_period_hours": -17.24,  # ретроградное вращение
        "surface_gravity": 8.69,  # m/s² (на уровне 1 бар)
        "atmosphere": "H₂ (82.5%), He (15.2%), CH₄ (2.3%)",
        "moons": 28
    },
    "neptune": {
        "orbital_period_days": 60182,
        "rotation_period_hours": 16.11,
        "surface_gravity": 11.15,  # m/s² (на уровне 1 бар)
        "atmosphere": "H₂ (80%), He (19%), CH₄ (1%)",
        "moons": 16
    }
}


# Валидация всех планет при загрузке модуля
for planet_key, planet in PLANETS_DATA.items():
    try:
        _validate_astronomical_data(planet)
    except ValueError as e:
        raise ValueError(f"Ошибка валидации данных планеты {planet_key}: {e}")


def get_planet_physical_data(planet_key: str) -> Tuple[float, float, float]:
    """
    Возвращает основные физические параметры планеты.
    
    Args:
        planet_key: Ключ планеты
        
    Returns:
        Кортеж (плотность в кг/м³, поверхностная гравитация в м/с², альбедо)
    """
    if planet_key not in PLANETS_DATA:
        raise KeyError(f"Планета {planet_key} не найдена")
    
    planet = PLANETS_DATA[planet_key]
    metadata = PLANET_METADATA[planet_key]
    
    # Рассчитываем плотность
    volume = (4/3) * math.pi * (planet.radius ** 3)
    density = planet.mass / volume
    
    # Поверхностная гравитация
    surface_gravity = metadata["surface_gravity"]
    
    return density, surface_gravity, 0.0  # альбедо пока не используется


def get_all_planets() -> Dict[str, Planet]:
    """
    Возвращает словарь всех доступных планет.
    
    Returns:
        Словарь с ключами-идентификаторами и значениями-объектами Planet
    """
    return PLANETS_DATA.copy()


def get_planet_by_key(key: str) -> Planet:
    """
    Возвращает планету по ключу.
    
    Args:
        key: Ключ планеты (например, "mars", "jupiter")
        
    Returns:
        Объект Planet
        
    Raises:
        KeyError: Если планета не найдена
    """
    if key not in PLANETS_DATA:
        raise KeyError(f"Планета с ключом '{key}' не найдена. Доступные: {list(PLANETS_DATA.keys())}")
    
    return PLANETS_DATA[key]


def get_planet_names() -> List[str]:
    """
    Возвращает список названий всех планет.
    
    Returns:
        Список названий планет
    """
    return [planet.name for planet in PLANETS_DATA.values()]


def get_destination_planets() -> Dict[str, Planet]:
    """
    Возвращает планеты, доступные как пункты назначения (исключая Землю).
    
    Returns:
        Словарь планет без Земли
    """
    destinations = PLANETS_DATA.copy()
    destinations.pop("earth", None)
    return destinations