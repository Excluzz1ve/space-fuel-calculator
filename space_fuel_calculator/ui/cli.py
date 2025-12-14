"""
CLI интерфейс для калькулятора топлива космических полетов.
"""
import sys
from typing import Optional, Tuple

from ..data.planets import get_destination_planets, get_planet_by_key
from ..data.engines import get_all_engines, get_engine_by_key, get_engine_categories
from ..models.planet import Planet
from ..models.engine import Engine, EngineType
from ..calculators.fuel_calculator import FuelCalculator, FuelResult
from ..calculators.trajectory_calculator import TrajectoryCalculator
from ..utils.exceptions import InvalidInputError, PhysicsViolationError
from .formatter import ResultFormatter


class MissionCLI:
    """
    Интерактивный CLI интерфейс для ввода параметров космической миссии.
    """
    
    def __init__(self):
        """Инициализация CLI интерфейса."""
        self.calculator = FuelCalculator()
        self.trajectory_calc = TrajectoryCalculator()
        self.planets = get_destination_planets()
        self.engines = get_all_engines()
        self.earth = get_planet_by_key("earth")
    
    def run_interactive_session(self) -> Optional[FuelResult]:
        """
        Запускает интерактивную сессию для ввода параметров миссии.
        
        Returns:
            FuelResult с результатами расчета или None при отмене
        """
        while True:  # Основной цикл для рестарта
            print("\n🚀 Калькулятор топлива для космических полетов")
            print("=" * 50)
            
            try:
                # Выбор планеты назначения
                destination = self._select_destination_planet()
                if destination is None:
                    return None
                
                # Выбор двигателя
                engine = self._select_engine()
                if engine is None:
                    continue  # Рестарт при отмене
                
                # Выбор типа миссии СНАЧАЛА (исправлена последовательность)
                round_trip = self._select_mission_type_first(destination, engine)
                if round_trip is None:
                    continue  # Рестарт при отмене
                
                # Ввод массы полезной нагрузки с учетом типа миссии
                payload_mass = self._input_payload_mass(destination, engine, round_trip)
                if payload_mass is None:
                    continue  # Рестарт при отмене
                
                # Предварительная проверка и предупреждения
                if not self._show_mission_warnings(destination, engine, payload_mass, round_trip):
                    continue  # Рестарт при отмене
                
                # Выполнение расчета
                print("\n🔄 Выполняется расчет...")
                
                if round_trip:
                    result = self.calculator.calculate_round_trip_fuel(destination, payload_mass, engine)
                else:
                    # Для односторонней миссии используем упрощенный расчет
                    # В реальной реализации здесь должен быть расчет дельта-V для конкретной планеты
                    delta_v = 12000  # Примерная дельта-V для межпланетного полета (м/с)
                    result = self.calculator.calculate_fuel_mass(delta_v, payload_mass, engine)
                
                # Показываем результат и спрашиваем о продолжении
                if result is not None:
                    print("\n" + "="*60)
                    ResultFormatter.display_result(result, show_metadata=True)
                    print("="*60)
                    
                    # Предлагаем дополнительные действия
                    print("\n💡 Что делать дальше?")
                    print("1. Новый расчет (рестарт)")
                    print("2. Завершить работу")
                    
                    while True:
                        try:
                            choice = input("\nВведите номер (1-2): ").strip()
                            if choice == '1':
                                break  # Выходим из внутреннего цикла для рестарта
                            elif choice == '2':
                                print("\n👋 Спасибо за использование калькулятора!")
                                return result
                            else:
                                print("❌ Введите 1 или 2.")
                        except KeyboardInterrupt:
                            print("\n👋 До свидания!")
                            return result
                    
                    continue  # Рестарт основного цикла
                
                return result
                
            except KeyboardInterrupt:
                print("\n\n❌ Операция отменена пользователем.")
                return None
            except (InvalidInputError, PhysicsViolationError) as e:
                print(f"\n❌ Ошибка расчета: {e}")
                print("\n💡 Возможные решения:")
                if "превышает физически реалистичные пределы" in str(e):
                    print("   • Выберите более близкую планету (Венера, Марс)")
                    print("   • Используйте более эффективный двигатель (ионный)")
                    print("   • Выберите полет в одну сторону вместо туда-обратно")
                    print("   • Уменьшите массу полезной нагрузки")
                elif "превышает практические пределы ракетостроения" in str(e):
                    print("   • Используйте двигатель с более высоким удельным импульсом")
                    print("   • Рассмотрите гравитационные маневры (будет реализовано)")
                    print("   • Уменьшите массу полезной нагрузки")
                
                # Предлагаем рестарт после ошибки
                print("\n🔄 Хотите попробовать снова?")
                print("1. Да, начать заново")
                print("2. Нет, завершить")
                
                while True:
                    try:
                        choice = input("\nВведите номер (1-2): ").strip()
                        if choice == '1':
                            break  # Рестарт
                        elif choice == '2':
                            print("\n👋 До свидания!")
                            return None
                        else:
                            print("❌ Введите 1 или 2.")
                    except KeyboardInterrupt:
                        return None
                
                continue  # Рестарт основного цикла
                
            except Exception as e:
                print(f"\n❌ Неожиданная ошибка: {e}")
                print("\n🔄 Попробуйте начать заново.")
                continue  # Рестарт при неожиданной ошибке
    
    def _select_destination_planet(self) -> Optional[Planet]:
        """
        Интерактивный выбор планеты назначения.
        
        Returns:
            Выбранная планета или None при отмене
        """
        print("\n📍 Выберите планету назначения:")
        print("-" * 30)
        
        planet_keys = list(self.planets.keys())
        for i, (key, planet) in enumerate(self.planets.items(), 1):
            # Добавляем индикаторы сложности миссий
            if planet.name in ["Венера", "Марс"]:
                difficulty = "🟢 ЛЕГКО"
            elif planet.name in ["Меркурий", "Юпитер"]:
                difficulty = "🟡 СРЕДНЕ"
            else:
                difficulty = "🔴 СЛОЖНО"
            print(f"{i}. {planet.name} ({difficulty})")
        
        print("\n💡 Подсказка:")
        print("   🟢 ЛЕГКО: Работают все типы миссий и двигателей")
        print("   🟡 СРЕДНЕ: Рекомендуется полет в одну сторону или ионные двигатели")
        print("   🔴 СЛОЖНО: Только полет в одну сторону + высокоэффективные двигатели")
        print("\n🔄 Введите 'q' для выхода")
        
        while True:
            try:
                choice = input(f"\nВведите номер планеты (1-{len(planet_keys)}) или 'q' для выхода: ").strip()
                
                if choice.lower() == 'q':
                    return None
                
                index = int(choice) - 1
                if 0 <= index < len(planet_keys):
                    selected_key = planet_keys[index]
                    selected_planet = self.planets[selected_key]
                    
                    print(f"\n✅ Выбрана планета: {selected_planet.name}")
                    self._display_planet_info(selected_planet)
                    
                    return selected_planet
                else:
                    print(f"❌ Неверный номер. Введите число от 1 до {len(planet_keys)}.")
                    
            except ValueError:
                print("❌ Введите корректный номер или 'q' для выхода.")
            except KeyboardInterrupt:
                return None
    
    def _select_engine(self) -> Optional[Engine]:
        """
        Интерактивный выбор двигателя.
        
        Returns:
            Выбранный двигатель или None при отмене
        """
        print("\n🔧 Выберите тип двигателя:")
        print("-" * 30)
        
        categories = get_engine_categories()
        
        # Сначала выбираем категорию с подсказками
        category_names = list(categories.keys())
        for i, category in enumerate(category_names, 1):
            if category == "Химические":
                hint = "(высокая тяга, для ближних планет)"
            elif category == "Ионные":
                hint = "(высокая эффективность, для дальних планет)"
            elif category == "Ядерные":
                hint = "(экспериментальные, максимальная эффективность)"
            else:
                hint = ""
            print(f"{i}. {category} {hint}")
        
        print("\n💡 Рекомендации по выбору:")
        print("   🚀 Химические: Венера, Марс (любой тип миссии)")
        print("   ⚡ Ионные: Юпитер+ (экономия топлива до 95%)")
        print("   ⚛️ Ядерные: Экстремальные миссии (экспериментальные)")
        
        while True:
            try:
                choice = input(f"\nВведите номер категории (1-{len(category_names)}) или 'q' для выхода: ").strip()
                
                if choice.lower() == 'q':
                    return None
                
                cat_index = int(choice) - 1
                if 0 <= cat_index < len(category_names):
                    selected_category = category_names[cat_index]
                    engine_keys = categories[selected_category]
                    
                    # Теперь выбираем конкретный двигатель
                    print(f"\n🔧 Двигатели категории '{selected_category}':")
                    print("-" * 40)
                    
                    for i, key in enumerate(engine_keys, 1):
                        engine = self.engines[key]
                        print(f"{i}. {engine.name}")
                    
                    while True:
                        try:
                            engine_choice = input(f"\nВведите номер двигателя (1-{len(engine_keys)}) или 'b' для возврата: ").strip()
                            
                            if engine_choice.lower() == 'b':
                                break
                            
                            engine_index = int(engine_choice) - 1
                            if 0 <= engine_index < len(engine_keys):
                                selected_key = engine_keys[engine_index]
                                selected_engine = self.engines[selected_key]
                                
                                print(f"\n✅ Выбран двигатель: {selected_engine.name}")
                                self._display_engine_info(selected_engine)
                                
                                return selected_engine
                            else:
                                print(f"❌ Неверный номер. Введите число от 1 до {len(engine_keys)}.")
                                
                        except ValueError:
                            print("❌ Введите корректный номер или 'b' для возврата.")
                        except KeyboardInterrupt:
                            return None
                else:
                    print(f"❌ Неверный номер. Введите число от 1 до {len(category_names)}.")
                    
            except ValueError:
                print("❌ Введите корректный номер или 'q' для выхода.")
            except KeyboardInterrupt:
                return None
    
    def _select_mission_type_first(self, destination: Planet, engine: Engine) -> Optional[bool]:
        """
        Выбор типа миссии СНАЧАЛА (до ввода массы).
        
        Args:
            destination: Планета назначения
            engine: Выбранный двигатель
            
        Returns:
            True для миссии туда-обратно, False для односторонней, None при отмене
        """
        print("\n🎯 Выберите тип миссии:")
        print("-" * 25)
        print("1. Полет в одну сторону")
        print("2. Полет туда и обратно")
        
        # Показываем общие рекомендации для данной комбинации
        print(f"\n💡 Рекомендации для {destination.name} + {engine.name}:")
        
        # Простая оценка сложности
        distant_planets = ["Юпитер", "Сатурн", "Уран", "Нептун"]
        if destination.name in distant_planets:
            if engine.engine_type.value == "chemical":
                print("   🔴 Для дальних планет с химическими двигателями рекомендуется полет в одну сторону")
            else:
                print("   🟡 Для дальних планет лучше использовать полет в одну сторону или малую массу")
        else:
            print("   🟢 Для ближних планет возможны оба типа миссий")
        
        while True:
            try:
                choice = input("\nВведите номер типа миссии (1-2) или 'q' для выхода: ").strip()
                
                if choice.lower() == 'q':
                    return None
                
                if choice == '1':
                    print("✅ Выбран полет в одну сторону")
                    return False
                elif choice == '2':
                    print("✅ Выбран полет туда и обратно")
                    return True
                else:
                    print("❌ Введите 1 или 2.")
                    
            except KeyboardInterrupt:
                return None

    def _input_payload_mass(self, destination: Planet, engine: Engine, round_trip: bool) -> Optional[float]:
        """
        Ввод массы полезной нагрузки с валидацией для конкретной планеты, двигателя и типа миссии.
        
        Args:
            destination: Планета назначения
            engine: Выбранный двигатель
            round_trip: True для полета туда-обратно
            
        Returns:
            Масса полезной нагрузки в кг или None при отмене
        """
        mission_type_str = "туда-обратно" if round_trip else "в одну сторону"
        print(f"\n📦 Введите массу полезной нагрузки для полета {mission_type_str}:")
        print("-" * 50)
        
        # Рассчитываем конкретные ограничения для выбранной комбинации
        limits = self._calculate_mass_limits(destination, engine)
        
        # Определяем максимум для выбранного типа миссии
        max_for_mission = limits['max_roundtrip'] if round_trip else limits['max_oneway']
        
        print(f"💡 Ограничения для {destination.name} + {engine.name}:")
        
        # Форматируем отображение ограничений с учетом невозможных миссий
        def format_limit(limit_value, mission_type):
            if limit_value == 0:
                return f"❌ НЕВОЗМОЖНО (дельта-V > 50 км/с)"
            else:
                return f"{limit_value:,.0f} кг"
        
        print(f"   • Рекомендуемый диапазон: {limits['recommended_min']:,.0f} - {limits['recommended_max']:,.0f} кг")
        print(f"   • Максимум для полета туда: {format_limit(limits['max_oneway'], 'туда')}")
        print(f"   • Максимум для полета туда-обратно: {format_limit(limits['max_roundtrip'], 'туда-обратно')}")
        
        # Показываем конкретно для выбранного типа миссии
        if max_for_mission == 0:
            print(f"🎯 Для вашего типа миссии ({mission_type_str}): ❌ НЕВОЗМОЖНО")
        else:
            print(f"🎯 Для вашего типа миссии ({mission_type_str}): максимум {max_for_mission:,.0f} кг")
        
        if limits['warnings']:
            print(f"   ⚠️ {limits['warnings']}")
        
        # Проверяем, возможна ли вообще выбранная миссия
        if max_for_mission == 0:
            print(f"\n🚫 КРИТИЧЕСКАЯ ОШИБКА:")
            print(f"   Выбранный тип миссии ({mission_type_str}) ФИЗИЧЕСКИ НЕВОЗМОЖЕН!")
            print(f"   Система не может рассчитать топливо для этой комбинации параметров.")
            print(f"\n💡 Рекомендации:")
            if round_trip:
                print(f"   • Выберите полет в одну сторону")
                print(f"   • Выберите более близкую планету (Венера, Марс)")
            else:
                print(f"   • Выберите более близкую планету")
                print(f"   • Используйте более эффективный двигатель")
            return None
        
        while True:
            try:
                mass_input = input(f"\nМасса в килограммах (максимум {max_for_mission:,.0f}) или 'q' для выхода: ").strip()
                
                if mass_input.lower() == 'q':
                    return None
                
                mass = float(mass_input)
                
                if mass <= 0:
                    print("❌ Масса должна быть положительным числом.")
                    continue
                
                if mass > 1000000:  # Абсолютный максимум
                    print("❌ Масса слишком велика (максимум 1,000,000 кг).")
                    continue
                
                # Проверяем конкретный лимит для выбранного типа миссии
                if round_trip and mass > limits['max_roundtrip']:
                    print(f"⚠️ ВНИМАНИЕ: Масса {mass:,.0f} кг превышает рекомендуемый максимум для полета туда-обратно ({limits['max_roundtrip']:,.0f} кг)")
                    print("   Это может привести к отклонению расчета из-за физических ограничений.")
                elif not round_trip and mass > limits['max_oneway']:
                    print(f"⚠️ ВНИМАНИЕ: Масса {mass:,.0f} кг превышает рекомендуемый максимум для полета в одну сторону ({limits['max_oneway']:,.0f} кг)")
                    print("   Это может привести к отклонению расчета из-за физических ограничений.")
                
                # Показываем дополнительные предупреждения
                warnings = self._get_mass_warnings(mass, destination, engine, limits)
                if warnings:
                    print(f"⚠️ {warnings}")
                
                print(f"✅ Масса полезной нагрузки: {mass:,.0f} кг ({mass/1000:.1f} тонн)")
                print(f"✅ Тип миссии: {mission_type_str}")
                return mass
                
            except ValueError:
                print("❌ Введите корректное число или 'q' для выхода.")
            except KeyboardInterrupt:
                return None
    
    def _select_mission_type(self, destination: Planet, engine: Engine, payload_mass: float) -> Optional[bool]:
        """
        Выбор типа миссии с учетом конкретных параметров.
        
        Args:
            destination: Планета назначения
            engine: Выбранный двигатель
            payload_mass: Масса полезной нагрузки
            
        Returns:
            True для миссии туда-обратно, False для односторонней, None при отмене
        """
        print("\n🎯 Выберите тип миссии:")
        print("-" * 25)
        print("1. Полет в одну сторону")
        print("2. Полет туда и обратно")
        
        # Рассчитываем конкретные ограничения для данной комбинации
        mission_analysis = self._analyze_mission_feasibility(destination, engine, payload_mass)
        
        print(f"\n📊 Анализ для {destination.name} + {engine.name} + {payload_mass:,.0f} кг:")
        print(f"   • Полет в одну сторону: {mission_analysis['oneway_status']}")
        print(f"   • Полет туда-обратно: {mission_analysis['roundtrip_status']}")
        
        if mission_analysis['recommendations']:
            print(f"   💡 {mission_analysis['recommendations']}")
        
        # Проверяем, есть ли хотя бы один возможный вариант
        oneway_possible = "ВОЗМОЖНО" in mission_analysis['oneway_status']
        roundtrip_possible = "ВОЗМОЖНО" in mission_analysis['roundtrip_status']
        
        if not oneway_possible and not roundtrip_possible:
            print(f"\n🚫 КРИТИЧЕСКОЕ ПРЕДУПРЕЖДЕНИЕ:")
            print(f"   Оба типа миссий показывают ВЫСОКИЙ РИСК!")
            print(f"   Расчет скорее всего будет отклонен системой.")
            print(f"\n💡 НАСТОЯТЕЛЬНО РЕКОМЕНДУЕТСЯ:")
            print(f"   • Выбрать более близкую планету (Венера, Марс)")
            print(f"   • Уменьшить массу полезной нагрузки")
            print(f"   • Использовать более эффективный двигатель")
            
            while True:
                try:
                    continue_choice = input(f"\n❓ Все равно продолжить? (y/n): ").strip().lower()
                    if continue_choice in ['n', 'no', 'нет', 'н']:
                        print("✅ Мудрое решение! Попробуйте другие параметры.")
                        return None
                    elif continue_choice in ['y', 'yes', 'да', 'д']:
                        print("⚠️ Продолжаем на ваш страх и риск...")
                        break
                    else:
                        print("❌ Введите 'y' для продолжения или 'n' для отмены.")
                except KeyboardInterrupt:
                    return None
        
        while True:
            try:
                choice = input("\nВведите номер типа миссии (1-2) или 'q' для выхода: ").strip()
                
                if choice.lower() == 'q':
                    return None
                
                if choice == '1':
                    if not oneway_possible:
                        print("⚠️ ВНИМАНИЕ: Полет в одну сторону показывает ВЫСОКИЙ РИСК!")
                        confirm = input("Все равно выбрать? (y/n): ").strip().lower()
                        if confirm not in ['y', 'yes', 'да', 'д']:
                            continue
                    print("✅ Выбран полет в одну сторону")
                    return False
                elif choice == '2':
                    if not roundtrip_possible:
                        print("⚠️ ВНИМАНИЕ: Полет туда-обратно показывает ВЫСОКИЙ РИСК!")
                        confirm = input("Все равно выбрать? (y/n): ").strip().lower()
                        if confirm not in ['y', 'yes', 'да', 'д']:
                            continue
                    print("✅ Выбран полет туда и обратно")
                    return True
                else:
                    print("❌ Введите 1 или 2.")
                    
            except KeyboardInterrupt:
                return None
    
    def _display_planet_info(self, planet: Planet) -> None:
        """
        Отображает информацию о планете.
        
        Args:
            planet: Планета для отображения
        """
        print(f"   📊 Характеристики планеты {planet.name}:")
        print(f"   • Масса: {planet.mass:.2e} кг")
        print(f"   • Радиус: {planet.radius/1000:.0f} км")
        print(f"   • Расстояние от Солнца: {planet.orbital_radius/1.496e11:.2f} а.е.")
        print(f"   • Скорость убегания: {planet.escape_velocity/1000:.1f} км/с")
    
    def _display_engine_info(self, engine: Engine) -> None:
        """
        Отображает характеристики двигателя.
        
        Args:
            engine: Двигатель для отображения
        """
        print(f"   📊 Характеристики двигателя {engine.name}:")
        print(f"   • Тип: {engine.engine_type.value}")
        print(f"   • Удельный импульс: {engine.specific_impulse:.0f} с")
        print(f"   • Тяга: {engine.thrust:,.0f} Н ({engine.thrust/1000:.0f} кН)")
        
        # Дополнительные характеристики в зависимости от типа
        if engine.engine_type == EngineType.CHEMICAL:
            from ..models.engine import ChemicalEngine
            if isinstance(engine, ChemicalEngine):
                print(f"   • Тип топлива: {engine.fuel_type}")
        elif engine.engine_type == EngineType.ION:
            from ..models.engine import IonEngine
            if isinstance(engine, IonEngine):
                print(f"   • Потребляемая мощность: {engine.power_consumption:,.0f} Вт")
        elif engine.engine_type == EngineType.NUCLEAR:
            from ..models.engine import NuclearEngine
            if isinstance(engine, NuclearEngine):
                print(f"   • Мощность реактора: {engine.reactor_power/1e6:.0f} МВт")
                print(f"   • Рабочее тело: {engine.propellant_type}")
    
    def _show_mission_warnings(self, destination: Planet, engine: Engine, payload_mass: float, round_trip: bool) -> bool:
        """
        Показывает предупреждения о потенциальных проблемах миссии.
        
        Args:
            destination: Планета назначения
            engine: Выбранный двигатель
            payload_mass: Масса полезной нагрузки
            round_trip: True для полета туда-обратно
            
        Returns:
            True если пользователь хочет продолжить, False если отменил
        """
        warnings = []
        
        # Проверка сложности планеты
        distant_planets = ["Юпитер", "Сатурн", "Уран", "Нептун"]
        if destination.name in distant_planets:
            if round_trip:
                warnings.append("🔴 ВЫСОКИЙ РИСК: Полет туда-обратно к дальним планетам может быть отклонен")
            if engine.engine_type.value == "chemical" and payload_mass > 1000:
                warnings.append("🟡 ВНИМАНИЕ: Большая масса + химический двигатель + дальняя планета = высокий расход топлива")
        
        # Проверка массы
        if payload_mass > 10000:  # 10 тонн
            warnings.append("🟡 ВНИМАНИЕ: Большая масса полезной нагрузки может привести к нереалистичным результатам")
        
        # Проверка комбинации двигатель-планета
        if destination.name in ["Сатурн", "Уран", "Нептун"] and engine.engine_type.value == "chemical":
            warnings.append("🟡 РЕКОМЕНДАЦИЯ: Для очень дальних планет лучше использовать ионные двигатели")
        
        # Показываем предупреждения
        if warnings:
            print("\n⚠️ ПРЕДУПРЕЖДЕНИЯ:")
            print("-" * 20)
            for warning in warnings:
                print(f"   {warning}")
            
            print("\n💡 ПРЕДЕЛЫ СИСТЕМЫ:")
            print("   • Максимальная дельта-V: 50 км/с")
            print("   • Максимальное отношение масс: 1000:1")
            print("   • При превышении пределов расчет будет отклонен")
            
            # Предлагаем продолжить или изменить параметры
            while True:
                try:
                    continue_choice = input("\n❓ Продолжить расчет? (y/n): ").strip().lower()
                    if continue_choice in ['n', 'no', 'нет', 'н']:
                        print("❌ Расчет отменен пользователем.")
                        return False
                    elif continue_choice in ['y', 'yes', 'да', 'д']:
                        break
                    else:
                        print("❌ Введите 'y' для продолжения или 'n' для отмены.")
                except KeyboardInterrupt:
                    return False
        
        return True
    
    def _calculate_mass_limits(self, destination: Planet, engine: Engine) -> dict:
        """
        Рассчитывает РЕАЛИСТИЧНЫЕ ограничения массы для данной комбинации планеты и двигателя.
        
        Args:
            destination: Планета назначения
            engine: Выбранный двигатель
            
        Returns:
            Словарь с ограничениями и рекомендациями
        """
        try:
            # Рассчитываем дельта-V для данной планеты используя исправленные расчеты
            delta_v = self.trajectory_calc.calculate_delta_v(self.earth, destination)
            outbound_dv, return_dv = self.trajectory_calc.calculate_roundtrip_delta_v(self.earth, destination)
            roundtrip_delta_v = outbound_dv + return_dv
            
            # КРИТИЧЕСКИ ВАЖНО: проверяем физические пределы СНАЧАЛА
            # Максимальная дельта-V системы: 50 км/с
            physically_possible_oneway = delta_v < 50000  # 50 км/с для полета в одну сторону
            physically_possible_roundtrip = roundtrip_delta_v < 45000  # 45 км/с для туда-обратно
            
            # Если даже полет в одну сторону невозможен
            if not physically_possible_oneway:
                return {
                    'recommended_min': 0,
                    'recommended_max': 0,
                    'max_oneway': 0,
                    'max_roundtrip': 0,
                    'warnings': f"ФИЗИЧЕСКИ НЕВОЗМОЖНО: требуемая дельта-V {delta_v/1000:.1f} км/с > 50 км/с"
                }
            
            if not physically_possible_roundtrip:
                # Полет в одну сторону возможен, туда-обратно - нет
                if delta_v < 10000:  # Ближние планеты
                    if engine.engine_type.value == "chemical":
                        recommended_min, recommended_max = 500, 5000
                        max_oneway = 10000
                    else:
                        recommended_min, recommended_max = 100, 2000
                        max_oneway = 5000
                elif delta_v < 20000:  # Средние планеты
                    if engine.engine_type.value == "chemical":
                        recommended_min, recommended_max = 200, 2000
                        max_oneway = 5000
                    else:
                        recommended_min, recommended_max = 50, 1000
                        max_oneway = 2000
                else:  # Дальние планеты
                    if engine.engine_type.value == "chemical":
                        recommended_min, recommended_max = 50, 500
                        max_oneway = 1000
                    else:
                        recommended_min, recommended_max = 10, 200
                        max_oneway = 500
                
                return {
                    'recommended_min': recommended_min,
                    'recommended_max': recommended_max,
                    'max_oneway': max_oneway,
                    'max_roundtrip': 0,  # ФИЗИЧЕСКИ НЕВОЗМОЖНО
                    'warnings': f"Полет туда-обратно НЕВОЗМОЖЕН: требуемая дельта-V {roundtrip_delta_v/1000:.1f} км/с > 45 км/с"
                }
            
            # Если оба типа физически возможны - рассчитываем нормальные ограничения
            if delta_v < 10000:  # Ближние планеты
                if engine.engine_type.value == "chemical":
                    recommended_min, recommended_max = 500, 5000
                    max_oneway, max_roundtrip = 10000, 3000
                else:  # ионные/ядерные
                    recommended_min, recommended_max = 100, 2000
                    max_oneway, max_roundtrip = 5000, 1000
            elif delta_v < 20000:  # Средние планеты
                if engine.engine_type.value == "chemical":
                    recommended_min, recommended_max = 200, 2000
                    max_oneway, max_roundtrip = 5000, 1000
                else:
                    recommended_min, recommended_max = 50, 1000
                    max_oneway, max_roundtrip = 2000, 500
            else:  # Дальние планеты (но физически возможные)
                if engine.engine_type.value == "chemical":
                    recommended_min, recommended_max = 50, 500
                    max_oneway, max_roundtrip = 1000, 200
                    warnings = "Химические двигатели неэффективны для дальних планет"
                else:
                    recommended_min, recommended_max = 10, 300
                    max_oneway, max_roundtrip = 800, 150
                    warnings = "Очень сложная миссия, требует точных расчетов"
            
            return {
                'recommended_min': recommended_min,
                'recommended_max': recommended_max,
                'max_oneway': max_oneway,
                'max_roundtrip': max_roundtrip,
                'warnings': warnings if 'warnings' in locals() else ""
            }
            
        except Exception:
            # Если не удалось рассчитать, используем консервативные ограничения
            return {
                'recommended_min': 100,
                'recommended_max': 1000,
                'max_oneway': 2000,
                'max_roundtrip': 500,
                'warnings': "Не удалось рассчитать точные ограничения - используются консервативные"
            }
    
    def _get_mass_warnings(self, mass: float, destination: Planet, engine: Engine, limits: dict) -> str:
        """
        Возвращает предупреждения для конкретной массы.
        
        Args:
            mass: Введенная масса
            destination: Планета назначения
            engine: Двигатель
            limits: Рассчитанные ограничения
            
        Returns:
            Строка с предупреждениями или пустая строка
        """
        warnings = []
        
        if mass > limits['max_roundtrip']:
            warnings.append(f"Масса превышает рекомендуемый максимум для полета туда-обратно ({limits['max_roundtrip']:,.0f} кг)")
        
        if mass > limits['max_oneway']:
            warnings.append(f"Масса превышает максимум даже для полета в одну сторону ({limits['max_oneway']:,.0f} кг)")
        
        if mass < limits['recommended_min']:
            warnings.append(f"Масса ниже рекомендуемого минимума ({limits['recommended_min']:,.0f} кг)")
        
        return "; ".join(warnings)
    
    def _analyze_mission_feasibility(self, destination: Planet, engine: Engine, payload_mass: float) -> dict:
        """
        Анализирует выполнимость миссии для конкретных параметров.
        
        Args:
            destination: Планета назначения
            engine: Двигатель
            payload_mass: Масса полезной нагрузки
            
        Returns:
            Словарь с анализом выполнимости
        """
        try:
            delta_v = self.trajectory_calc.calculate_delta_v(self.earth, destination)
            
            # Более строгие критерии для дальних планет
            # Учитываем, что для полета туда-обратно нужна удвоенная дельта-V
            roundtrip_delta_v = delta_v * 2.2  # Коэффициент для учета возвращения
            
            # Критерии выполнимости на основе физических пределов
            # Максимальная дельта-V: 50 км/с
            oneway_feasible = delta_v < 45000  # Оставляем запас
            roundtrip_feasible = roundtrip_delta_v < 45000  # Для туда-обратно
            
            # Корректировка для типа двигателя и массы
            if engine.engine_type.value == "chemical":
                # Химические двигатели менее эффективны для больших дельта-V
                oneway_feasible = oneway_feasible and delta_v < 25000 and payload_mass < 5000
                roundtrip_feasible = roundtrip_feasible and roundtrip_delta_v < 25000 and payload_mass < 1000
            elif engine.engine_type.value == "ion":
                # Ионные двигатели более эффективны, но ограничены по массе
                oneway_feasible = oneway_feasible and payload_mass < 2000
                roundtrip_feasible = roundtrip_feasible and payload_mass < 500
            elif engine.engine_type.value == "nuclear":
                # Ядерные двигатели самые эффективные
                oneway_feasible = oneway_feasible and payload_mass < 3000
                roundtrip_feasible = roundtrip_feasible and payload_mass < 800
            
            # Специальная проверка для экстремально дальних планет
            extreme_planets = ["Сатурн", "Уран", "Нептун"]
            if destination.name in extreme_planets:
                # Для этих планет туда-обратно практически невозможно
                roundtrip_feasible = False
                if payload_mass > 200:
                    oneway_feasible = False
            
            oneway_status = "✅ ВОЗМОЖНО" if oneway_feasible else "❌ ВЫСОКИЙ РИСК"
            roundtrip_status = "✅ ВОЗМОЖНО" if roundtrip_feasible else "❌ ВЫСОКИЙ РИСК"
            
            recommendations = ""
            if not roundtrip_feasible and oneway_feasible:
                recommendations = "Рекомендуется полет в одну сторону"
            elif not oneway_feasible:
                if destination.name in extreme_planets:
                    recommendations = "Выберите более близкую планету (Венера, Марс) или значительно уменьшите массу"
                else:
                    recommendations = "Рекомендуется уменьшить массу или выбрать более эффективный двигатель"
            
            # Добавляем информацию о дельта-V для понимания
            if delta_v > 40000:
                recommendations += f" (требуемая дельта-V: {delta_v/1000:.1f} км/с)"
            
            return {
                'oneway_status': oneway_status,
                'roundtrip_status': roundtrip_status,
                'recommendations': recommendations,
                'delta_v': delta_v,
                'roundtrip_delta_v': roundtrip_delta_v
            }
            
        except Exception:
            return {
                'oneway_status': "❓ НЕИЗВЕСТНО",
                'roundtrip_status': "❓ НЕИЗВЕСТНО",
                'recommendations': "Не удалось выполнить анализ",
                'delta_v': 0,
                'roundtrip_delta_v': 0
            }


def run_cli() -> Optional[FuelResult]:
    """
    Запускает CLI интерфейс для ввода параметров миссии.
    
    Returns:
        FuelResult с результатами расчета или None при отмене
    """
    cli = MissionCLI()
    result = cli.run_interactive_session()
    
    if result is not None:
        # Отображаем результаты с помощью форматтера
        print("\n" + "="*60)
        ResultFormatter.display_result(result, show_metadata=True)
        print("="*60)
        
        # Предлагаем дополнительные действия
        print("\n💡 Дополнительные возможности:")
        print("   • Сохранение результатов в файл (будет реализовано в следующих задачах)")
        print("   • Сравнение с другими двигателями")
        print("   • Анализ траекторий с гравитационными маневрами")
    
    return result