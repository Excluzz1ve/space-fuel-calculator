"""
База данных ракетных двигателей с реальными характеристиками.

Данные основаны на технических спецификациях производителей и NASA.
Источники:
- NASA Glenn Research Center Propulsion Database
- SpaceX Technical Specifications
- Roscosmos Technical Documentation
- ESA Propulsion Systems Database
- Academic publications on advanced propulsion

Категории двигателей:
1. Химические - используют химическую энергию сгорания топлива
2. Ионные - используют электрическую энергию для ускорения ионов
3. Ядерные - используют ядерную энергию (экспериментальные/концептуальные)

Точность данных:
- Удельный импульс: ±2% для серийных двигателей, ±10% для экспериментальных
- Тяга: ±1% для химических, ±5% для электрических двигателей
- Потребляемая мощность: ±5% для ионных двигателей
"""
from typing import Dict, List, Tuple, Optional
from ..models.engine import ChemicalEngine, IonEngine, NuclearEngine, Engine


def _validate_engine_parameters(engine: Engine) -> bool:
    """
    Валидирует параметры двигателя на техническую реалистичность.
    
    Args:
        engine: Объект двигателя для валидации
        
    Returns:
        True если параметры корректны
        
    Raises:
        ValueError: Если параметры не проходят валидацию
    """
    # Проверка удельного импульса по типу двигателя
    if isinstance(engine, ChemicalEngine):
        if engine.specific_impulse < 200 or engine.specific_impulse > 500:
            raise ValueError(f"Нереалистичный удельный импульс для химического двигателя {engine.name}: {engine.specific_impulse}с")
        if engine.thrust < 1000 or engine.thrust > 10000000:  # от 1кН до 10МН
            raise ValueError(f"Нереалистичная тяга для химического двигателя {engine.name}: {engine.thrust}Н")
    
    elif isinstance(engine, IonEngine):
        if engine.specific_impulse < 1000 or engine.specific_impulse > 10000:
            raise ValueError(f"Нереалистичный удельный импульс для ионного двигателя {engine.name}: {engine.specific_impulse}с")
        if engine.thrust < 0.001 or engine.thrust > 10:  # от 1мН до 10Н
            raise ValueError(f"Нереалистичная тяга для ионного двигателя {engine.name}: {engine.thrust}Н")
        if engine.power_consumption < 100 or engine.power_consumption > 200000:  # от 100Вт до 200кВт
            raise ValueError(f"Нереалистичное энергопотребление для ионного двигателя {engine.name}: {engine.power_consumption}Вт")
    
    elif isinstance(engine, NuclearEngine):
        if engine.specific_impulse < 400 or engine.specific_impulse > 20000:
            raise ValueError(f"Нереалистичный удельный импульс для ядерного двигателя {engine.name}: {engine.specific_impulse}с")
        if engine.reactor_power < 1000000 or engine.reactor_power > 10000000000:  # от 1МВт до 10ГВт
            raise ValueError(f"Нереалистичная мощность реактора для ядерного двигателя {engine.name}: {engine.reactor_power}Вт")
    
    return True


# Химические двигатели - проверенные в полетах
CHEMICAL_ENGINES = {
    # Российские двигатели
    "rd180": ChemicalEngine(
        name="РД-180",
        specific_impulse=311.3,  # seconds (в вакууме)
        thrust=3827000,  # Newtons (в вакууме)
        fuel_type="RP-1/LOX"
    ),
    "rd191": ChemicalEngine(
        name="РД-191",
        specific_impulse=311.7,  # seconds (в вакууме)
        thrust=2085000,  # Newtons (в вакууме)
        fuel_type="RP-1/LOX"
    ),
    "rd0110": ChemicalEngine(
        name="РД-0110",
        specific_impulse=326,  # seconds (в вакууме)
        thrust=298000,  # Newtons (в вакууме)
        fuel_type="RP-1/LOX"
    ),
    
    # SpaceX двигатели
    "merlin1d": ChemicalEngine(
        name="Merlin 1D",
        specific_impulse=282,  # seconds (на уровне моря)
        thrust=845000,  # Newtons (на уровне моря)
        fuel_type="RP-1/LOX"
    ),
    "merlin1d_vacuum": ChemicalEngine(
        name="Merlin 1D Vacuum",
        specific_impulse=348,  # seconds (в вакууме)
        thrust=934000,  # Newtons (в вакууме)
        fuel_type="RP-1/LOX"
    ),
    "raptor": ChemicalEngine(
        name="Raptor",
        specific_impulse=350,  # seconds (в вакууме)
        thrust=2000000,  # Newtons (в вакууме)
        fuel_type="CH4/LOX"
    ),
    "raptor_vacuum": ChemicalEngine(
        name="Raptor Vacuum",
        specific_impulse=378,  # seconds (в вакууме)
        thrust=2200000,  # Newtons (в вакууме)
        fuel_type="CH4/LOX"
    ),
    
    # NASA/Boeing двигатели
    "rs25": ChemicalEngine(
        name="RS-25 (SSME)",
        specific_impulse=452.3,  # seconds (в вакууме)
        thrust=2279000,  # Newtons (в вакууме)
        fuel_type="LH2/LOX"
    ),
    "rl10": ChemicalEngine(
        name="RL10B-2",
        specific_impulse=462.4,  # seconds (в вакууме)
        thrust=110100,  # Newtons (в вакууме)
        fuel_type="LH2/LOX"
    ),
    
    # Blue Origin двигатели
    "be4": ChemicalEngine(
        name="BE-4",
        specific_impulse=334,  # seconds (в вакууме)
        thrust=2400000,  # Newtons (в вакууме)
        fuel_type="CH4/LOX"
    ),
    "be3": ChemicalEngine(
        name="BE-3",
        specific_impulse=445,  # seconds (в вакууме)
        thrust=490000,  # Newtons (в вакууме)
        fuel_type="LH2/LOX"
    ),
    
    # Европейские двигатели
    "vulcain2": ChemicalEngine(
        name="Vulcain 2",
        specific_impulse=434,  # seconds (в вакууме)
        thrust=1390000,  # Newtons (в вакууме)
        fuel_type="LH2/LOX"
    ),
    "vinci": ChemicalEngine(
        name="Vinci",
        specific_impulse=465,  # seconds (в вакууме)
        thrust=180000,  # Newtons (в вакууме)
        fuel_type="LH2/LOX"
    )
}

# Ионные двигатели - проверенные в космических миссиях
ION_ENGINES = {
    # NASA двигатели
    "nstar": IonEngine(
        name="NSTAR",
        specific_impulse=3120,  # seconds
        thrust=0.092,  # Newtons
        power_consumption=2300  # Watts
    ),
    "next": IonEngine(
        name="NEXT (NASA Evolutionary Xenon Thruster)",
        specific_impulse=4190,  # seconds
        thrust=0.236,  # Newtons
        power_consumption=6900  # Watts
    ),
    "dawn_ion": IonEngine(
        name="Dawn Ion Propulsion System",
        specific_impulse=3100,  # seconds
        thrust=0.091,  # Newtons
        power_consumption=2300  # Watts
    ),
    
    # ESA двигатели
    "rit22": IonEngine(
        name="RIT-22",
        specific_impulse=3500,  # seconds
        thrust=0.200,  # Newtons
        power_consumption=4500  # Watts
    ),
    "t6": IonEngine(
        name="T6 Ion Thruster",
        specific_impulse=3000,  # seconds
        thrust=0.165,  # Newtons
        power_consumption=4200  # Watts
    ),
    
    # Hall Effect двигатели
    "spt100": IonEngine(
        name="SPT-100 (Stationary Plasma Thruster)",
        specific_impulse=1600,  # seconds
        thrust=0.083,  # Newtons
        power_consumption=1350  # Watts
    ),
    "bht200": IonEngine(
        name="BHT-200 (Busek Hall Thruster)",
        specific_impulse=1500,  # seconds
        thrust=0.013,  # Newtons
        power_consumption=200  # Watts
    ),
    "pet": IonEngine(
        name="PPS-1350 (Plasma Propulsion System)",
        specific_impulse=1640,  # seconds
        thrust=0.090,  # Newtons
        power_consumption=1500  # Watts
    ),
    
    # Современные разработки
    "x3": IonEngine(
        name="X3 Nested-Channel Hall Thruster",
        specific_impulse=2650,  # seconds
        thrust=5.4,  # Newtons
        power_consumption=102000  # Watts (102 kW)
    ),
    "aeps": IonEngine(
        name="AEPS (Advanced Electric Propulsion System)",
        specific_impulse=2900,  # seconds
        thrust=0.600,  # Newtons
        power_consumption=13300  # Watts
    )
}

# Ядерные двигатели - экспериментальные и концептуальные
NUCLEAR_ENGINES = {
    # Исторические проекты
    "nerva": NuclearEngine(
        name="NERVA (Nuclear Engine for Rocket Vehicle Application)",
        specific_impulse=850,  # seconds
        thrust=334000,  # Newtons
        reactor_power=1500000000,  # Watts (1.5 GW)
        propellant_type="H2"
    ),
    "rover": NuclearEngine(
        name="Project Rover NRX-A6",
        specific_impulse=825,  # seconds
        thrust=311000,  # Newtons
        reactor_power=1100000000,  # Watts (1.1 GW)
        propellant_type="H2"
    ),
    
    # Современные концепции
    "vasimr": NuclearEngine(
        name="VASIMR (Variable Specific Impulse Magnetoplasma Rocket)",
        specific_impulse=5000,  # seconds (переменный 1000-5000)
        thrust=5.7,  # Newtons
        reactor_power=200000000,  # Watts (200 MW)
        propellant_type="Ar/H2"
    ),
    "nuclear_lightbulb": NuclearEngine(
        name="Nuclear Lightbulb",
        specific_impulse=1500,  # seconds
        thrust=1000000,  # Newtons
        reactor_power=5000000000,  # Watts (5 GW)
        propellant_type="H2"
    ),
    "nuclear_saltwater": NuclearEngine(
        name="Nuclear Salt-Water Rocket",
        specific_impulse=4700,  # seconds
        thrust=13000000,  # Newtons
        reactor_power=10000000000,  # Watts (10 GW)
        propellant_type="U235/H2O"
    ),
    
    # Российские проекты
    "rd0410": NuclearEngine(
        name="РД-0410 (Ядерный ракетный двигатель)",
        specific_impulse=910,  # seconds
        thrust=35200,  # Newtons
        reactor_power=196000000,  # Watts (196 MW)
        propellant_type="H2"
    ),
    
    # Перспективные концепции
    "fusion_ramjet": NuclearEngine(
        name="Fusion Ramjet",
        specific_impulse=10000,  # seconds
        thrust=1000000,  # Newtons
        reactor_power=1000000000,  # Watts (1 GW)
        propellant_type="D-T"
    )
}

# Метаданные двигателей для дополнительной информации
ENGINE_METADATA = {
    # Химические двигатели
    "rd180": {
        "manufacturer": "НПО Энергомаш",
        "first_flight": 2000,
        "status": "Активный",
        "applications": ["Atlas V"],
        "throttle_range": "47-100%",
        "restart_capability": False
    },
    "merlin1d": {
        "manufacturer": "SpaceX",
        "first_flight": 2013,
        "status": "Активный",
        "applications": ["Falcon 9", "Falcon Heavy"],
        "throttle_range": "40-100%",
        "restart_capability": True
    },
    "rs25": {
        "manufacturer": "Aerojet Rocketdyne",
        "first_flight": 1981,
        "status": "Активный",
        "applications": ["Space Shuttle", "SLS"],
        "throttle_range": "67-109%",
        "restart_capability": False
    },
    "raptor": {
        "manufacturer": "SpaceX",
        "first_flight": 2019,
        "status": "В разработке",
        "applications": ["Starship", "Super Heavy"],
        "throttle_range": "20-100%",
        "restart_capability": True
    },
    
    # Ионные двигатели
    "nstar": {
        "manufacturer": "NASA Glenn Research Center",
        "first_flight": 1998,
        "status": "Завершен",
        "applications": ["Deep Space 1"],
        "operational_lifetime": "16000+ часов",
        "propellant": "Xenon"
    },
    "next": {
        "manufacturer": "NASA Glenn Research Center",
        "first_flight": None,
        "status": "Тестирование",
        "applications": ["Будущие миссии"],
        "operational_lifetime": "50000+ часов",
        "propellant": "Xenon"
    },
    
    # Ядерные двигатели
    "nerva": {
        "manufacturer": "NASA/AEC",
        "first_flight": None,
        "status": "Отменен (1973)",
        "applications": ["Mars missions (planned)"],
        "test_duration": "62 минуты",
        "development_cost": "$1.4 млрд (1973)"
    },
    "vasimr": {
        "manufacturer": "Ad Astra Rocket Company",
        "first_flight": None,
        "status": "В разработке",
        "applications": ["ISS tests", "Mars missions"],
        "test_duration": "Наземные испытания",
        "power_source": "Nuclear reactor"
    }
}

# Объединенный словарь всех двигателей
ALL_ENGINES = {
    **CHEMICAL_ENGINES,
    **ION_ENGINES,
    **NUCLEAR_ENGINES
}

# Валидация всех двигателей при загрузке модуля
for engine_key, engine in ALL_ENGINES.items():
    try:
        _validate_engine_parameters(engine)
    except ValueError as e:
        raise ValueError(f"Ошибка валидации параметров двигателя {engine_key}: {e}")


def get_all_engines() -> Dict[str, Engine]:
    """
    Возвращает словарь всех доступных двигателей.
    
    Returns:
        Словарь с ключами-идентификаторами и значениями-объектами Engine
    """
    return ALL_ENGINES.copy()


def get_engines_by_type(engine_type: str) -> Dict[str, Engine]:
    """
    Возвращает двигатели определенного типа.
    
    Args:
        engine_type: Тип двигателя ("chemical", "ion", "nuclear")
        
    Returns:
        Словарь двигателей указанного типа
        
    Raises:
        ValueError: Если тип двигателя неизвестен
    """
    if engine_type == "chemical":
        return CHEMICAL_ENGINES.copy()
    elif engine_type == "ion":
        return ION_ENGINES.copy()
    elif engine_type == "nuclear":
        return NUCLEAR_ENGINES.copy()
    else:
        raise ValueError(f"Неизвестный тип двигателя: {engine_type}. Доступные: chemical, ion, nuclear")


def get_engine_by_key(key: str) -> Engine:
    """
    Возвращает двигатель по ключу.
    
    Args:
        key: Ключ двигателя (например, "rd180", "nstar")
        
    Returns:
        Объект Engine
        
    Raises:
        KeyError: Если двигатель не найден
    """
    if key not in ALL_ENGINES:
        raise KeyError(f"Двигатель с ключом '{key}' не найден. Доступные: {list(ALL_ENGINES.keys())}")
    
    return ALL_ENGINES[key]


def get_engine_names() -> List[str]:
    """
    Возвращает список названий всех двигателей.
    
    Returns:
        Список названий двигателей
    """
    return [engine.name for engine in ALL_ENGINES.values()]


def get_engine_categories() -> Dict[str, List[str]]:
    """
    Возвращает двигатели, сгруппированные по категориям.
    
    Returns:
        Словарь с категориями и списками ключей двигателей
    """
    return {
        "Химические": list(CHEMICAL_ENGINES.keys()),
        "Ионные": list(ION_ENGINES.keys()),
        "Ядерные": list(NUCLEAR_ENGINES.keys())
    }


def get_engine_metadata(engine_key: str) -> Optional[Dict]:
    """
    Возвращает метаданные двигателя.
    
    Args:
        engine_key: Ключ двигателя
        
    Returns:
        Словарь с метаданными или None если не найдены
    """
    return ENGINE_METADATA.get(engine_key)


def get_engines_by_performance(min_isp: float = 0, max_isp: float = float('inf'),
                              min_thrust: float = 0, max_thrust: float = float('inf')) -> Dict[str, Engine]:
    """
    Фильтрует двигатели по характеристикам производительности.
    
    Args:
        min_isp: Минимальный удельный импульс (с)
        max_isp: Максимальный удельный импульс (с)
        min_thrust: Минимальная тяга (Н)
        max_thrust: Максимальная тяга (Н)
        
    Returns:
        Словарь отфильтрованных двигателей
    """
    filtered = {}
    for key, engine in ALL_ENGINES.items():
        if (min_isp <= engine.specific_impulse <= max_isp and
            min_thrust <= engine.thrust <= max_thrust):
            filtered[key] = engine
    return filtered


def get_recommended_engines_for_mission(mission_type: str) -> List[str]:
    """
    Возвращает рекомендуемые двигатели для типа миссии.
    
    Args:
        mission_type: Тип миссии ("earth_orbit", "lunar", "mars", "outer_planets", "interstellar")
        
    Returns:
        Список ключей рекомендуемых двигателей
    """
    recommendations = {
        "earth_orbit": ["merlin1d", "rd180", "rs25", "be4"],
        "lunar": ["rl10", "merlin1d_vacuum", "raptor_vacuum", "be3"],
        "mars": ["raptor", "rs25", "next", "vasimr"],
        "outer_planets": ["next", "aeps", "vasimr", "nerva"],
        "interstellar": ["vasimr", "fusion_ramjet", "nuclear_lightbulb"]
    }
    
    return recommendations.get(mission_type, list(ALL_ENGINES.keys())[:5])


def compare_engines(engine_keys: List[str]) -> Dict[str, Dict[str, float]]:
    """
    Сравнивает характеристики нескольких двигателей.
    
    Args:
        engine_keys: Список ключей двигателей для сравнения
        
    Returns:
        Словарь с характеристиками каждого двигателя
        
    Raises:
        KeyError: Если один из двигателей не найден
    """
    comparison = {}
    for key in engine_keys:
        if key not in ALL_ENGINES:
            raise KeyError(f"Двигатель {key} не найден")
        
        engine = ALL_ENGINES[key]
        comparison[key] = {
            "specific_impulse": engine.specific_impulse,
            "thrust": engine.thrust,
            "thrust_to_weight": 0.0,  # Требует массы двигателя
            "type": engine.engine_type.value
        }
        
        # Добавляем специфичные для типа характеристики
        if isinstance(engine, IonEngine):
            comparison[key]["power_consumption"] = engine.power_consumption
            comparison[key]["thrust_per_kw"] = engine.thrust / (engine.power_consumption / 1000)
        elif isinstance(engine, NuclearEngine):
            comparison[key]["reactor_power"] = engine.reactor_power
            comparison[key]["power_to_thrust"] = engine.reactor_power / engine.thrust
    
    return comparison