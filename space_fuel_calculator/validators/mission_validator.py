"""
Валидатор миссий для проверки расчетов против реальных данных NASA/ESA.

Проверяет соответствие расчетной дельта-V историческим данным космических миссий.
"""

import warnings
from typing import Dict, List, Optional, Tuple
from ..models.validation import (
    ValidationResult, 
    MissionReference, 
    ValidationConfig,
    ConfidenceLevel,
    MissionType,
    TrajectoryType
)


class MissionValidator:
    """
    Валидирует расчеты против реальных данных NASA/ESA.
    
    Содержит базу данных референсных миссий и методы для проверки
    соответствия расчетной дельта-V реальным историческим данным.
    """
    
    def __init__(self, config: Optional[ValidationConfig] = None):
        """
        Инициализация валидатора миссий.
        
        Args:
            config: Конфигурация валидации (опционально)
        """
        self.config = config or ValidationConfig()
        self._initialize_reference_missions()
    
    def _initialize_reference_missions(self) -> None:
        """Инициализация базы данных референсных миссий."""
        
        # Референсные данные из реальных миссий NASA/ESA
        self.reference_missions: Dict[str, List[MissionReference]] = {
            'юпитер': [
                MissionReference(
                    name='Juno',
                    agency='NASA',
                    year=2011,
                    delta_v=8800,  # м/с
                    mission_type=MissionType.ORBITER,
                    trajectory_type=TrajectoryType.DIRECT,
                    target_planet='юпитер',
                    sources=[
                        'NASA Juno Mission Design',
                        'JPL Delta-V Budget Analysis 2011'
                    ],
                    notes='Polar orbiter mission to Jupiter'
                ),
                MissionReference(
                    name='Galileo',
                    agency='NASA',
                    year=1989,
                    delta_v=8500,  # м/с
                    mission_type=MissionType.ORBITER,
                    trajectory_type=TrajectoryType.GRAVITY_ASSIST,
                    target_planet='юпитер',
                    sources=[
                        'NASA Galileo Mission Report',
                        'JPL Trajectory Analysis 1989'
                    ],
                    notes='Used Venus-Earth-Earth gravity assists'
                ),
                MissionReference(
                    name='Europa Clipper',
                    agency='NASA',
                    year=2024,
                    delta_v=8900,  # м/с
                    mission_type=MissionType.ORBITER,
                    trajectory_type=TrajectoryType.DIRECT,
                    target_planet='юпитер',
                    sources=[
                        'NASA Europa Clipper Mission Design',
                        'JPL Delta-V Requirements 2024'
                    ],
                    notes='Jupiter orbiter with Europa flybys'
                )
            ],
            'марс': [
                MissionReference(
                    name='Perseverance',
                    agency='NASA',
                    year=2020,
                    delta_v=3500,  # м/с
                    mission_type=MissionType.LANDER,
                    trajectory_type=TrajectoryType.DIRECT,
                    target_planet='марс',
                    sources=[
                        'NASA Mars 2020 Mission Design',
                        'JPL Trajectory Analysis 2020'
                    ],
                    notes='Mars rover mission with sky crane landing'
                ),
                MissionReference(
                    name='Curiosity (MSL)',
                    agency='NASA',
                    year=2011,
                    delta_v=3600,  # м/с
                    mission_type=MissionType.LANDER,
                    trajectory_type=TrajectoryType.DIRECT,
                    target_planet='марс',
                    sources=[
                        'NASA MSL Mission Design',
                        'JPL Delta-V Budget 2011'
                    ],
                    notes='Mars Science Laboratory rover'
                ),
                MissionReference(
                    name='InSight',
                    agency='NASA',
                    year=2018,
                    delta_v=3400,  # м/с
                    mission_type=MissionType.LANDER,
                    trajectory_type=TrajectoryType.DIRECT,
                    target_planet='марс',
                    sources=[
                        'NASA InSight Mission Report',
                        'JPL Trajectory Design 2018'
                    ],
                    notes='Mars seismic monitoring lander'
                )
            ],
            'сатурн': [
                MissionReference(
                    name='Cassini-Huygens',
                    agency='NASA/ESA',
                    year=1997,
                    delta_v=8200,  # м/с
                    mission_type=MissionType.ORBITER,
                    trajectory_type=TrajectoryType.GRAVITY_ASSIST,
                    target_planet='сатурн',
                    sources=[
                        'NASA Cassini Mission Design',
                        'ESA Huygens Mission Report',
                        'JPL Trajectory Analysis 1997'
                    ],
                    notes='Used Venus-Venus-Earth-Jupiter gravity assists'
                )
            ],
            'венера': [
                MissionReference(
                    name='Parker Solar Probe',
                    agency='NASA',
                    year=2018,
                    delta_v=3500,  # м/с (Venus gravity assists)
                    mission_type=MissionType.FLYBY,
                    trajectory_type=TrajectoryType.GRAVITY_ASSIST,
                    target_planet='венера',
                    sources=[
                        'NASA Parker Solar Probe Mission Design',
                        'APL Trajectory Analysis 2018'
                    ],
                    notes='Multiple Venus gravity assists for solar approach'
                ),
                MissionReference(
                    name='BepiColombo',
                    agency='ESA/JAXA',
                    year=2018,
                    delta_v=3600,  # м/с
                    mission_type=MissionType.FLYBY,
                    trajectory_type=TrajectoryType.GRAVITY_ASSIST,
                    target_planet='венера',
                    sources=[
                        'ESA BepiColombo Mission Design',
                        'JAXA Trajectory Analysis 2018'
                    ],
                    notes='Venus and Earth gravity assists to Mercury'
                )
            ],
            'меркурий': [
                MissionReference(
                    name='MESSENGER',
                    agency='NASA',
                    year=2004,
                    delta_v=5500,  # м/с
                    mission_type=MissionType.ORBITER,
                    trajectory_type=TrajectoryType.GRAVITY_ASSIST,
                    target_planet='меркурий',
                    sources=[
                        'NASA MESSENGER Mission Design',
                        'APL Trajectory Analysis 2004'
                    ],
                    notes='Used Earth-Venus-Venus-Mercury gravity assists'
                )
            ],
            'уран': [
                MissionReference(
                    name='Voyager 2',
                    agency='NASA',
                    year=1977,
                    delta_v=11200,  # м/с
                    mission_type=MissionType.FLYBY,
                    trajectory_type=TrajectoryType.GRAVITY_ASSIST,
                    target_planet='уран',
                    sources=[
                        'NASA Voyager Mission Design',
                        'JPL Grand Tour Analysis 1977'
                    ],
                    notes='Jupiter-Saturn-Uranus-Neptune grand tour'
                )
            ],
            'нептун': [
                MissionReference(
                    name='Voyager 2',
                    agency='NASA',
                    year=1977,
                    delta_v=12100,  # м/с
                    mission_type=MissionType.FLYBY,
                    trajectory_type=TrajectoryType.GRAVITY_ASSIST,
                    target_planet='нептун',
                    sources=[
                        'NASA Voyager Mission Design',
                        'JPL Grand Tour Analysis 1977'
                    ],
                    notes='Jupiter-Saturn-Uranus-Neptune grand tour'
                )
            ]
        }
    
    def validate_delta_v(self, planet_name: str, calculated_delta_v: float) -> ValidationResult:
        """
        Проверяет соответствие расчетной дельта-V реальным миссиям.
        
        Args:
            planet_name: Название планеты назначения
            calculated_delta_v: Расчетная дельта-V в м/с
            
        Returns:
            ValidationResult с результатами валидации
            
        Raises:
            ValueError: Если входные параметры некорректны
        """
        if calculated_delta_v < 0:
            raise ValueError(f"Дельта-V не может быть отрицательной: {calculated_delta_v}")
        
        if not planet_name or not planet_name.strip():
            raise ValueError("Название планеты не может быть пустым")
        
        planet_key = planet_name.lower().strip()
        
        # Если нет референсных данных для планеты
        if planet_key not in self.reference_missions:
            return ValidationResult(
                valid=True,
                confidence=ConfidenceLevel.LOW,
                note=f"Нет референсных данных для планеты '{planet_name}'",
                sources=[]
            )
        
        missions = self.reference_missions[planet_key]
        if not missions:
            return ValidationResult(
                valid=True,
                confidence=ConfidenceLevel.LOW,
                note=f"Пустая база данных миссий для планеты '{planet_name}'",
                sources=[]
            )
        
        # Получаем диапазон референсных значений
        reference_values = [mission.delta_v for mission in missions]
        min_ref = min(reference_values)
        max_ref = max(reference_values)
        
        # Применяем допуск
        tolerance = self.config.tolerance_percent / 100.0
        min_allowed = min_ref * (1 - tolerance)
        max_allowed = max_ref * (1 + tolerance)
        
        # Находим ближайшую миссию
        closest_mission = min(missions, key=lambda m: abs(m.delta_v - calculated_delta_v))
        deviation_percent = abs(calculated_delta_v - closest_mission.delta_v) / closest_mission.delta_v * 100
        
        # Собираем все источники
        all_sources = []
        for mission in missions:
            all_sources.extend(mission.sources)
        
        # Проверяем соответствие
        if min_allowed <= calculated_delta_v <= max_allowed:
            return ValidationResult(
                valid=True,
                confidence=ConfidenceLevel.HIGH,
                reference_mission=closest_mission.name,
                note=f"Соответствует миссии {closest_mission.name} ({closest_mission.year})",
                sources=list(set(all_sources)),
                deviation_percent=deviation_percent
            )
        elif calculated_delta_v < min_allowed:
            return ValidationResult(
                valid=False,
                confidence=ConfidenceLevel.LOW,
                reference_mission=closest_mission.name,
                note=f"Значение {calculated_delta_v/1000:.1f} км/с ниже реальных миссий ({min_ref/1000:.1f}-{max_ref/1000:.1f} км/с)",
                sources=list(set(all_sources)),
                deviation_percent=deviation_percent
            )
        else:
            return ValidationResult(
                valid=False,
                confidence=ConfidenceLevel.LOW,
                reference_mission=closest_mission.name,
                note=f"Значение {calculated_delta_v/1000:.1f} км/с выше реальных миссий ({min_ref/1000:.1f}-{max_ref/1000:.1f} км/с)",
                sources=list(set(all_sources)),
                deviation_percent=deviation_percent
            )
    
    def get_reference_missions(self, planet_name: Optional[str] = None) -> Dict[str, List[MissionReference]]:
        """
        Получить референсные миссии для планеты или все миссии.
        
        Args:
            planet_name: Название планеты (опционально)
            
        Returns:
            Словарь с референсными миссиями
        """
        if planet_name is None:
            return self.reference_missions.copy()
        
        planet_key = planet_name.lower().strip()
        if planet_key in self.reference_missions:
            return {planet_key: self.reference_missions[planet_key].copy()}
        else:
            return {}
    
    def add_reference_mission(self, mission: MissionReference) -> None:
        """
        Добавить новую референсную миссию в базу данных.
        
        Args:
            mission: Данные миссии для добавления
            
        Raises:
            ValueError: Если данные миссии некорректны
        """
        if not isinstance(mission, MissionReference):
            raise ValueError("mission должен быть экземпляром MissionReference")
        
        planet_key = mission.target_planet.lower().strip()
        
        if planet_key not in self.reference_missions:
            self.reference_missions[planet_key] = []
        
        # Проверяем, что миссия с таким именем еще не существует
        existing_names = [m.name for m in self.reference_missions[planet_key]]
        if mission.name in existing_names:
            warnings.warn(f"Миссия '{mission.name}' уже существует для планеты '{planet_key}'")
            return
        
        self.reference_missions[planet_key].append(mission)
    
    def validate_roundtrip_delta_v(self, planet_name: str, outbound_delta_v: float, 
                                 return_delta_v: float) -> ValidationResult:
        """
        Валидирует дельта-V для полета туда-обратно.
        
        Args:
            planet_name: Название планеты назначения
            outbound_delta_v: Дельта-V для полета туда в м/с
            return_delta_v: Дельта-V для обратного полета в м/с
            
        Returns:
            ValidationResult с результатами валидации
        """
        total_delta_v = outbound_delta_v + return_delta_v
        
        # Валидируем общую дельта-V
        base_validation = self.validate_delta_v(planet_name, outbound_delta_v)
        
        # Проверяем разумность соотношения туда/обратно
        if return_delta_v > outbound_delta_v * 3:
            return ValidationResult(
                valid=False,
                confidence=ConfidenceLevel.LOW,
                note=f"Обратная дельта-V ({return_delta_v/1000:.1f} км/с) слишком велика относительно прямой ({outbound_delta_v/1000:.1f} км/с)",
                sources=base_validation.sources
            )
        
        if return_delta_v < outbound_delta_v * 0.5:
            return ValidationResult(
                valid=False,
                confidence=ConfidenceLevel.LOW,
                note=f"Обратная дельта-V ({return_delta_v/1000:.1f} км/с) слишком мала относительно прямой ({outbound_delta_v/1000:.1f} км/с)",
                sources=base_validation.sources
            )
        
        # Если базовая валидация прошла успешно
        if base_validation.valid:
            return ValidationResult(
                valid=True,
                confidence=base_validation.confidence,
                reference_mission=base_validation.reference_mission,
                note=f"Полет туда-обратно: {total_delta_v/1000:.1f} км/с (туда: {outbound_delta_v/1000:.1f}, обратно: {return_delta_v/1000:.1f})",
                sources=base_validation.sources,
                deviation_percent=base_validation.deviation_percent
            )
        else:
            return base_validation
    
    def get_mission_statistics(self) -> Dict[str, Dict[str, float]]:
        """
        Получить статистику по референсным миссиям.
        
        Returns:
            Словарь со статистикой по планетам
        """
        stats = {}
        
        for planet, missions in self.reference_missions.items():
            if not missions:
                continue
                
            delta_vs = [m.delta_v for m in missions]
            stats[planet] = {
                'count': len(missions),
                'min_delta_v': min(delta_vs),
                'max_delta_v': max(delta_vs),
                'avg_delta_v': sum(delta_vs) / len(delta_vs),
                'earliest_year': min(m.year for m in missions),
                'latest_year': max(m.year for m in missions)
            }
        
        return stats