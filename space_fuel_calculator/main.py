"""
Главный модуль калькулятора топлива для космических полетов.

Точка входа в приложение с обработкой аргументов командной строки.
Интегрирует все компоненты системы: расчеты, управление миссиями, UI.
"""

import sys
import argparse
from typing import Optional
from pathlib import Path

from .ui.cli import run_cli
from .ui.formatter import ResultFormatter
from .managers.mission_manager import MissionManager
from .calculators.fuel_calculator import FuelCalculator
from .data.planets import get_destination_planets
from .data.engines import get_all_engines
from .utils.exceptions import InvalidInputError, PhysicsViolationError, DataFormatError
from . import __version__


def create_parser() -> argparse.ArgumentParser:
    """Создает парсер аргументов командной строки."""
    parser = argparse.ArgumentParser(
        description="Калькулятор топлива для космических полетов",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  space-fuel-calc                           # Интерактивный режим
  space-fuel-calc --list-missions           # Показать сохраненные миссии
  space-fuel-calc --load mission_id.json   # Загрузить миссию из файла
  space-fuel-calc --validate-data          # Проверить целостность данных
  space-fuel-calc --help                   # Показать справку
        """
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}"
    )
    
    parser.add_argument(
        "--interactive",
        action="store_true",
        default=False,
        help="Запустить в интерактивном режиме"
    )
    
    parser.add_argument(
        "--list-missions",
        action="store_true",
        help="Показать список сохраненных миссий"
    )
    
    parser.add_argument(
        "--load",
        metavar="FILEPATH",
        help="Загрузить миссию из JSON файла"
    )
    
    parser.add_argument(
        "--export-csv",
        metavar="FILEPATH",
        help="Экспортировать последнюю миссию в CSV файл"
    )
    
    parser.add_argument(
        "--validate-data",
        action="store_true",
        help="Проверить целостность данных планет и двигателей"
    )
    
    parser.add_argument(
        "--missions-dir",
        metavar="DIR",
        default="missions",
        help="Директория для сохранения миссий (по умолчанию: missions)"
    )
    
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Подробный вывод информации"
    )
    
    return parser


def validate_system_data(verbose: bool = False) -> bool:
    """
    Проверяет целостность данных планет и двигателей.
    
    Args:
        verbose: Подробный вывод информации
        
    Returns:
        True если все данные корректны, False иначе
    """
    try:
        if verbose:
            print("🔍 Проверка данных планет...")
        
        planets = get_destination_planets()
        if not planets:
            print("❌ Не найдены данные планет")
            return False
        
        # Проверка корректности данных планет
        for key, planet in planets.items():
            if planet.mass <= 0 or planet.radius <= 0 or planet.orbital_radius <= 0:
                print(f"❌ Некорректные данные планеты {planet.name}")
                return False
        
        if verbose:
            print(f"✅ Загружено {len(planets)} планет")
        
        if verbose:
            print("🔍 Проверка данных двигателей...")
        
        engines = get_all_engines()
        if not engines:
            print("❌ Не найдены данные двигателей")
            return False
        
        # Проверка корректности данных двигателей
        for key, engine in engines.items():
            if engine.specific_impulse <= 0 or engine.thrust <= 0:
                print(f"❌ Некорректные данные двигателя {engine.name}")
                return False
        
        if verbose:
            print(f"✅ Загружено {len(engines)} двигателей")
        
        if verbose:
            print("🔍 Проверка калькулятора...")
        
        # Тестовый расчет
        calculator = FuelCalculator()
        test_result = calculator.calculate_fuel_mass(1000.0, 1000.0, list(engines.values())[0])
        
        if test_result.total_fuel <= 0:
            print("❌ Ошибка в расчетах калькулятора")
            return False
        
        if verbose:
            print("✅ Калькулятор работает корректно")
        
        print("✅ Все системные данные корректны")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при проверке данных: {e}")
        return False


def list_saved_missions(mission_manager: MissionManager, verbose: bool = False) -> None:
    """
    Выводит список сохраненных миссий.
    
    Args:
        mission_manager: Менеджер миссий
        verbose: Подробный вывод информации
    """
    try:
        missions = mission_manager.list_missions()
        
        if not missions:
            print("📂 Сохраненные миссии не найдены")
            return
        
        print(f"📂 Найдено {len(missions)} сохраненных миссий:")
        print("-" * 80)
        
        for mission in missions:
            print(f"🚀 {mission['name']} (ID: {mission['id']})")
            print(f"   📍 Назначение: {mission['destination']}")
            print(f"   📅 Создано: {mission['created_at']}")
            if verbose:
                print(f"   📁 Файл: {mission['filepath']}")
            print()
            
    except Exception as e:
        print(f"❌ Ошибка при получении списка миссий: {e}")


def load_and_display_mission(filepath: str, mission_manager: MissionManager) -> bool:
    """
    Загружает и отображает миссию из файла.
    
    Args:
        filepath: Путь к файлу миссии
        mission_manager: Менеджер миссий
        
    Returns:
        True если миссия успешно загружена, False иначе
    """
    try:
        print(f"📂 Загрузка миссии из {filepath}...")
        
        mission = mission_manager.load_mission(filepath)
        
        print(f"✅ Миссия '{mission.name}' успешно загружена")
        print("=" * 60)
        
        # Отображение информации о миссии
        print(f"🚀 Миссия: {mission.name}")
        print(f"📍 Назначение: {mission.destination.name}")
        print(f"📦 Полезная нагрузка: {mission.payload_mass:,.0f} кг")
        print(f"🔧 Двигатель: {mission.engine.name}")
        print(f"🌌 Гравитационные маневры: {'Да' if mission.use_gravity_assists else 'Нет'}")
        print(f"📅 Создано: {mission.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        
        if mission.fuel_requirements:
            print("\n📊 Результаты расчетов:")
            ResultFormatter.display_result(mission.fuel_requirements, show_metadata=True)
        
        print("=" * 60)
        return True
        
    except DataFormatError as e:
        print(f"❌ Ошибка формата файла: {e}")
        return False
    except Exception as e:
        print(f"❌ Ошибка загрузки миссии: {e}")
        return False


def main(argv: Optional[list] = None) -> int:
    """
    Главная функция приложения.
    
    Args:
        argv: Аргументы командной строки (по умолчанию sys.argv)
        
    Returns:
        Код возврата (0 - успех, 1 - ошибка)
    """
    if argv is None:
        argv = sys.argv[1:]
    
    parser = create_parser()
    args = parser.parse_args(argv)
    
    try:
        # Инициализация менеджера миссий
        mission_manager = MissionManager(args.missions_dir)
        
        # Обработка различных режимов работы
        if args.validate_data:
            success = validate_system_data(args.verbose)
            return 0 if success else 1
        
        elif args.list_missions:
            list_saved_missions(mission_manager, args.verbose)
            return 0
        
        elif args.load:
            success = load_and_display_mission(args.load, mission_manager)
            return 0 if success else 1
        
        elif args.export_csv:
            print("❌ Экспорт в CSV требует предварительной загрузки миссии")
            print("   Используйте: --load <файл_миссии> --export-csv <выходной_файл>")
            return 1
        
        elif args.interactive or len(argv) == 0:
            # Интерактивный режим (по умолчанию)
            print("🚀 Запуск интерактивного режима...")
            
            # Проверка системных данных перед запуском
            if not validate_system_data(args.verbose):
                print("❌ Обнаружены проблемы с системными данными")
                return 1
            
            result = run_cli()
            
            if result is not None:
                print("\n✅ Расчет завершен успешно!")
                
                # Предложение сохранить результат
                try:
                    save_choice = input("\n💾 Сохранить результаты миссии? (y/n): ").strip().lower()
                    if save_choice in ['y', 'yes', 'да', 'д']:
                        # Здесь будет реализовано сохранение в следующих задачах
                        print("💡 Функция сохранения будет доступна после завершения всех задач")
                except KeyboardInterrupt:
                    pass
                
                return 0
            else:
                print("\n❌ Расчет отменен.")
                return 1
        
        else:
            # Показать справку если не указаны аргументы
            parser.print_help()
            return 0
        
    except KeyboardInterrupt:
        print("\nПрограмма прервана пользователем.")
        return 1
    except (InvalidInputError, PhysicsViolationError, DataFormatError) as e:
        print(f"❌ Ошибка: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        if args.verbose:
            import traceback
            traceback.print_exc()
        print(f"❌ Неожиданная ошибка: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())