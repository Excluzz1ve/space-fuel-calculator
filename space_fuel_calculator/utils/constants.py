"""
Физические константы для расчетов космических полетов.
"""

# Физические константы
GRAVITATIONAL_CONSTANT = 6.67430e-11  # м³/(кг·с²)
STANDARD_GRAVITY = 9.80665  # м/с²
SPEED_OF_LIGHT = 299792458  # м/с

# Астрономические константы
ASTRONOMICAL_UNIT = 1.495978707e11  # м (среднее расстояние от Земли до Солнца)
SOLAR_MASS = 1.98847e30  # кг

# Константы Земли
EARTH_MASS = 5.97237e24  # кг
EARTH_RADIUS = 6.371e6  # м
EARTH_ESCAPE_VELOCITY = 11180  # м/с

# Пределы валидации
MIN_PAYLOAD_MASS = 1.0  # кг
MAX_PAYLOAD_MASS = 1e6  # кг (1000 тонн)
MAX_DELTA_V = 50000  # м/с (50 км/с)
MIN_SPECIFIC_IMPULSE = 100  # с
MAX_SPECIFIC_IMPULSE = 10000  # с

# Единицы измерения
KG_TO_TONNES = 1000
M_S_TO_KM_S = 1000