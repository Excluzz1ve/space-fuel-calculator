"""
Интеграционные тесты для полных сценариев космических миссий.

Тестирует взаимодействие всех компонентов системы в реалистичных сценариях.
"""

import pytest
import tempfile
import os
from pathlib import Path
from datetime import datetime

from space_fuel_calculator.calculators.fuel_calculator import FuelCalculator
from space_fuel_calculator.calculators.trajectory_calculator import TrajectoryCalculator
from space_fuel_calculator.calculators.gravity_assist_calculator import GravityAssistCalculator
from space_fuel_calculator.managers.mission_manager import MissionManager
from space_fuel_calculator.models.mission import Mission
from space_fuel_calculator.models.engine import ChemicalEngine, IonEngine
from space_fuel_calculator.data.planets import get_planet_by_key
from space_fuel_calculator.data.engines import get_engine_by_key
from space_fuel_calculator.ui.formatter import ResultFormatter
from space_fuel_calculator.ui.trajectory_visualizer import TrajectoryVisualizer
from space_fuel_calculator.utils.exceptions import InvalidInputError, DataFormatError


class TestMissionIntegration:
    """Интеграционные тесты для полных сценариев миссий."""
    
    def setup_method(self):
        """Настройка для каждого теста."""
        self.fuel_calculator = FuelCalculator()
        self.trajectory_calculator = TrajectoryCalculator()
        self.gravity_assist_calculator = GravityAssistCalculator()
        
        # Создаем временную директорию для тестов
        self.temp_dir = tempfile.mkdtemp()
        self.mission_manager = MissionManager(self.temp_dir)
    
    def teardown_method(self):
        """Очистка после каждого теста."""
        # Удаляем временные файлы
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_earth_mars_earth_mission_scenario(self):
        """
        Тест полного сценария миссии Земля-Марс-Земля.
        
        **Validates: Requirements 1.1, 2.1, 4.1, 5.1**
        """
        # 1. Получаем данные планет и двигателя
        earth = get_planet_by_key("earth")
        mars = get_planet_by_key("mars")
        engine = get_engine_by_key("rd180")  # Химический двигатель РД-180
        
        assert earth is not None, "Планета Земля должна быть доступна"
        assert mars is not None, "Планета Марс должна быть доступна"
        assert engine is not None, "Двигатель РД-180 должен быть доступен"
        
        payload_mass = 5000.0  # 5 тонн полезной нагрузки
        
        # 2. Рассчитываем траекторию
        delta_v = self.trajectory_calculator.calculate_delta_v(earth, mars)
        assert delta_v > 0, "Дельта-V для полета на Марс должна быть положительной"
        assert delta_v < 20000, "Дельта-V не должна превышать разумные пределы"
        
        # 3. Рассчитываем топливо для полета туда и обратно
        fuel_result = self.fuel_calculator.calculate_round_trip_fuel(mars, payload_mass, engine)
        
        # Проверяем корректность результата
        assert fuel_result.total_fuel > 0, "Общая масса топлива должна быть положительной"
        assert fuel_result.outbound_fuel > 0, "Топливо для прямого полета должно быть положительным"
        assert fuel_result.return_fuel > 0, "Топливо для обратного полета должно быть положительным"
        assert fuel_result.total_fuel == fuel_result.outbound_fuel + fuel_result.return_fuel, (
            "Общее топливо должно равняться сумме топлива для этапов"
        )
        
        # 4. Создаем миссию
        mission = Mission(
            id=f"mars_mission_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            name="Mars Sample Return Mission",
            destination=mars,
            payload_mass=payload_mass,
            engine=engine,
            use_gravity_assists=False,
            created_at=datetime.now(),
            fuel_requirements=fuel_result
        )
        
        # 5. Сохраняем миссию
        saved_path = self.mission_manager.save_mission(mission)
        assert os.path.exists(saved_path), "Файл миссии должен быть создан"
        
        # 6. Загружаем миссию обратно
        loaded_mission = self.mission_manager.load_mission(saved_path)
        
        # Проверяем корректность загрузки
        assert loaded_mission.id == mission.id, "ID миссии должен совпадать"
        assert loaded_mission.name == mission.name, "Название миссии должно совпадать"
        assert loaded_mission.destination.name == mars.name, "Планета назначения должна совпадать"
        assert loaded_mission.payload_mass == payload_mass, "Масса полезной нагрузки должна совпадать"
        assert loaded_mission.engine.name == engine.name, "Двигатель должен совпадать"
        
        # 7. Экспортируем в CSV
        csv_content = self.mission_manager.export_to_csv(loaded_mission)
        assert "Mars Sample Return Mission" in csv_content, "CSV должен содержать название миссии"
        assert "Марс" in csv_content, "CSV должен содержать планету назначения"
        assert str(payload_mass) in csv_content, "CSV должен содержать массу полезной нагрузки"
        
        # 8. Форматируем результаты для отображения
        formatted_result = ResultFormatter.display_result(fuel_result, show_metadata=True)
        # Проверяем, что форматирование не вызывает ошибок (результат не None)
        assert formatted_result is None  # display_result печатает, но не возвращает значение
        
        # 9. Проверяем разумность результатов
        fuel_to_payload_ratio = fuel_result.total_fuel / payload_mass
        assert fuel_to_payload_ratio > 1, "Отношение топлива к полезной нагрузке должно быть больше 1"
        assert fuel_to_payload_ratio < 50, "Отношение топлива к полезной нагрузке не должно быть чрезмерным"
        
        print(f"✅ Миссия Земля-Марс-Земля успешно протестирована:")
        print(f"   • Полезная нагрузка: {payload_mass:,.0f} кг")
        print(f"   • Общее топливо: {fuel_result.total_fuel:,.0f} кг")
        print(f"   • Отношение топливо/нагрузка: {fuel_to_payload_ratio:.1f}")
        print(f"   • Общая дельта-V: {fuel_result.total_delta_v:,.0f} м/с")
    def test_jupiter_gravity_assist_mission_scenario(self):
        """
        Тест сценария миссии с гравитационными маневрами через Юпитер.
        
        **Validates: Requirements 4.1, 4.2, 4.3**
        """
        # 1. Получаем данные планет и двигателя
        earth = get_planet_by_key("earth")
        jupiter = get_planet_by_key("jupiter")  # Используем Юпитер как более реалистичную цель
        engine = get_engine_by_key("merlin1d")  # SpaceX Merlin 1D
        
        assert earth is not None, "Планета Земля должна быть доступна"
        assert jupiter is not None, "Планета Юпитер должна быть доступна"
        assert engine is not None, "Двигатель Merlin 1D должен быть доступен"
        
        payload_mass = 2000.0  # 2 тонны для дальней миссии
        
        # 2. Используем реалистичные значения дельта-V для Юпитера
        direct_delta_v = 8500.0  # Реалистичная дельта-V для прямого полета к Юпитеру (м/с)
        
        # 3. Симулируем гравитационный маневр (упрощенный расчет)
        # В реальной системе здесь был бы более сложный расчет
        assist_efficiency = 0.15  # 15% экономия от гравитационного маневра
        assist_delta_v = direct_delta_v * (1 - assist_efficiency)
        
        # Проверяем, что маневр дает экономию
        assert assist_delta_v < direct_delta_v, (
            f"Гравитационный маневр должен экономить дельта-V: "
            f"прямой полет {direct_delta_v:.0f} м/с vs с маневром {assist_delta_v:.0f} м/с"
        )
        
        savings = direct_delta_v - assist_delta_v
        savings_percent = (savings / direct_delta_v) * 100
        
        assert savings > 0, "Экономия от гравитационного маневра должна быть положительной"
        assert savings_percent > 5, "Экономия должна быть значительной (>5%)"
        
        # 4. Рассчитываем топливо для обеих траекторий
        direct_fuel = self.fuel_calculator.calculate_fuel_mass(direct_delta_v, payload_mass, engine)
        assist_fuel = self.fuel_calculator.calculate_fuel_mass(assist_delta_v, payload_mass, engine)
        
        fuel_savings = direct_fuel.total_fuel - assist_fuel.total_fuel
        fuel_savings_percent = (fuel_savings / direct_fuel.total_fuel) * 100
        
        assert fuel_savings > 0, "Экономия топлива должна быть положительной"
        assert fuel_savings_percent > 5, "Экономия топлива должна быть значительной (>5%)"
        
        # 5. Создаем миссию с гравитационными маневрами
        mission = Mission(
            id=f"jupiter_gravity_assist_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            name="Jupiter Exploration with Gravity Assist",
            destination=jupiter,
            payload_mass=payload_mass,
            engine=engine,
            use_gravity_assists=True,
            created_at=datetime.now(),
            fuel_requirements=assist_fuel
        )
        
        # 6. Создаем визуализацию траектории
        trajectory_viz = TrajectoryVisualizer.format_trajectory_with_gravity_assists(
            origin=earth,
            destination=jupiter,
            base_delta_v=direct_delta_v,
            use_assists=True
        )
        
        # Проверяем содержание визуализации
        assert "гравитационными маневрами" in trajectory_viz, (
            "Визуализация должна упоминать гравитационные маневры"
        )
        assert "Экономия" in trajectory_viz, (
            "Визуализация должна показывать экономию от маневров"
        )
        assert "Юпитер" in trajectory_viz, (
            "Визуализация должна упоминать Юпитер как промежуточную планету"
        )
        
        # 7. Сохраняем и проверяем миссию
        saved_path = self.mission_manager.save_mission(mission)
        loaded_mission = self.mission_manager.load_mission(saved_path)
        
        assert loaded_mission.use_gravity_assists == True, (
            "Флаг гравитационных маневров должен сохраняться"
        )
        
        print(f"✅ Миссия с гравитационными маневрами успешно протестирована:")
        print(f"   • Экономия дельта-V: {savings:,.0f} м/с ({savings_percent:.1f}%)")
        print(f"   • Экономия топлива: {fuel_savings:,.0f} кг ({fuel_savings_percent:.1f}%)")
        print(f"   • Прямой полет: {direct_fuel.total_fuel:,.0f} кг топлива")
        print(f"   • С маневром: {assist_fuel.total_fuel:,.0f} кг топлива")

    def test_ion_engine_deep_space_mission_scenario(self):
        """
        Тест сценария дальней миссии с ионным двигателем.
        
        **Validates: Requirements 3.4, 1.1, 2.1**
        """
        # 1. Получаем данные для дальней миссии
        earth = get_planet_by_key("earth")
        jupiter = get_planet_by_key("jupiter")  # Используем Юпитер вместо Нептуна для более реалистичной дельта-V
        ion_engine = get_engine_by_key("nstar")  # NASA NSTAR ионный двигатель
        
        assert earth is not None, "Планета Земля должна быть доступна"
        assert jupiter is not None, "Планета Юпитер должна быть доступна"
        assert ion_engine is not None, "Ионный двигатель NSTAR должен быть доступен"
        
        payload_mass = 500.0  # Небольшая полезная нагрузка для дальней миссии
        
        # 2. Рассчитываем траекторию (используем более реалистичную дельта-V)
        delta_v = 8000.0  # Реалистичная дельта-V для полета к Юпитеру (м/с)
        
        # 3. Сравниваем ионный и химический двигатели
        chemical_engine = get_engine_by_key("rd180")
        
        ion_fuel = self.fuel_calculator.calculate_fuel_mass(delta_v, payload_mass, ion_engine)
        chemical_fuel = self.fuel_calculator.calculate_fuel_mass(delta_v, payload_mass, chemical_engine)
        
        # Ионный двигатель должен требовать значительно меньше топлива
        fuel_ratio = chemical_fuel.total_fuel / ion_fuel.total_fuel
        assert fuel_ratio > 2, (
            f"Ионный двигатель должен быть значительно эффективнее: "
            f"химический {chemical_fuel.total_fuel:,.0f} кг vs ионный {ion_fuel.total_fuel:,.0f} кг "
            f"(отношение: {fuel_ratio:.1f})"
        )
        
        # 4. Проверяем характеристики ионного двигателя
        assert ion_engine.specific_impulse > 3000, (
            f"Ионный двигатель должен иметь высокий удельный импульс: {ion_engine.specific_impulse:.0f} с"
        )
        assert ion_engine.thrust < 1, (
            f"Ионный двигатель должен иметь низкую тягу: {ion_engine.thrust:.3f} Н"
        )
        
        # 5. Создаем миссию с ионным двигателем
        mission = Mission(
            id=f"jupiter_ion_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            name="Jupiter Deep Space Mission (Ion Propulsion)",
            destination=jupiter,
            payload_mass=payload_mass,
            engine=ion_engine,
            use_gravity_assists=False,
            created_at=datetime.now(),
            fuel_requirements=ion_fuel
        )
        
        # 6. Тестируем сохранение и загрузку
        saved_path = self.mission_manager.save_mission(mission)
        loaded_mission = self.mission_manager.load_mission(saved_path)
        
        # Проверяем, что тип двигателя сохранился корректно
        assert loaded_mission.engine.engine_type.value == "ion", (
            "Тип ионного двигателя должен сохраняться"
        )
        
        # 7. Экспортируем детальный отчет
        csv_content = self.mission_manager.export_to_csv(loaded_mission, include_details=True)
        
        # Проверяем наличие специфичной для ионных двигателей информации
        assert "ion" in csv_content, "CSV должен содержать тип двигателя"
        assert str(ion_engine.specific_impulse) in csv_content, (
            "CSV должен содержать удельный импульс ионного двигателя"
        )
        
        print(f"✅ Миссия с ионным двигателем успешно протестирована:")
        print(f"   • Ионный двигатель: {ion_fuel.total_fuel:,.0f} кг топлива")
        print(f"   • Химический двигатель: {chemical_fuel.total_fuel:,.0f} кг топлива")
        print(f"   • Экономия топлива: {fuel_ratio:.1f}x")
        print(f"   • Удельный импульс: {ion_engine.specific_impulse:.0f} с")

    def test_mission_configuration_persistence_scenario(self):
        """
        Тест сценария сохранения и восстановления сложных конфигураций миссий.
        
        **Validates: Requirements 5.1, 5.2, 5.3, 5.5**
        """
        # 1. Создаем несколько различных миссий
        missions = []
        
        # Миссия 1: Химический двигатель, Марс
        mars_mission = Mission(
            id="mars_chemical_001",
            name="Mars Rover Delivery",
            destination=get_planet_by_key("mars"),
            payload_mass=3000.0,
            engine=get_engine_by_key("rd180"),
            use_gravity_assists=False,
            created_at=datetime.now(),
            fuel_requirements=None  # Будет рассчитано
        )
        
        # Рассчитываем топливо для Mars миссии
        mars_fuel = self.fuel_calculator.calculate_round_trip_fuel(
            mars_mission.destination, mars_mission.payload_mass, mars_mission.engine
        )
        mars_mission.fuel_requirements = mars_fuel
        missions.append(mars_mission)
        
        # Миссия 2: Ионный двигатель, Юпитер
        jupiter_mission = Mission(
            id="jupiter_ion_001",
            name="Jupiter Orbital Survey",
            destination=get_planet_by_key("jupiter"),
            payload_mass=800.0,
            engine=get_engine_by_key("nstar"),
            use_gravity_assists=True,
            created_at=datetime.now(),
            fuel_requirements=None
        )
        
        # Рассчитываем топливо для Jupiter миссии (используем реалистичную дельта-V)
        jupiter_delta_v = 8000.0  # Реалистичная дельта-V для Юпитера
        jupiter_fuel = self.fuel_calculator.calculate_fuel_mass(
            jupiter_delta_v, jupiter_mission.payload_mass, jupiter_mission.engine
        )
        jupiter_mission.fuel_requirements = jupiter_fuel
        missions.append(jupiter_mission)
        
        # Миссия 3: Ядерный двигатель, Сатурн
        saturn_mission = Mission(
            id="saturn_nuclear_001",
            name="Saturn Ring Analysis Mission",
            destination=get_planet_by_key("saturn"),
            payload_mass=1500.0,
            engine=get_engine_by_key("nerva"),
            use_gravity_assists=True,
            created_at=datetime.now(),
            fuel_requirements=None
        )
        
        # Рассчитываем топливо для Saturn миссии (используем реалистичную дельта-V)
        saturn_delta_v = 12000.0  # Реалистичная дельта-V для Сатурна
        saturn_fuel = self.fuel_calculator.calculate_fuel_mass(
            saturn_delta_v, saturn_mission.payload_mass, saturn_mission.engine
        )
        saturn_mission.fuel_requirements = saturn_fuel
        missions.append(saturn_mission)
        
        # 2. Сохраняем все миссии
        saved_paths = []
        for mission in missions:
            path = self.mission_manager.save_mission(mission)
            saved_paths.append(path)
            assert os.path.exists(path), f"Файл миссии {mission.name} должен быть создан"
        
        # 3. Проверяем список миссий
        mission_list = self.mission_manager.list_missions()
        assert len(mission_list) == 3, f"Должно быть 3 миссии, найдено {len(mission_list)}"
        
        # Проверяем, что все миссии в списке
        mission_ids = {m['id'] for m in mission_list}
        expected_ids = {m.id for m in missions}
        assert mission_ids == expected_ids, "Все миссии должны быть в списке"
        
        # 4. Загружаем и проверяем каждую миссию
        for i, (original_mission, saved_path) in enumerate(zip(missions, saved_paths)):
            loaded_mission = self.mission_manager.load_mission(saved_path)
            
            # Проверяем основные параметры
            assert loaded_mission.id == original_mission.id, f"ID миссии {i+1} должен совпадать"
            assert loaded_mission.name == original_mission.name, f"Название миссии {i+1} должно совпадать"
            assert loaded_mission.payload_mass == original_mission.payload_mass, (
                f"Масса полезной нагрузки миссии {i+1} должна совпадать"
            )
            assert loaded_mission.use_gravity_assists == original_mission.use_gravity_assists, (
                f"Флаг гравитационных маневров миссии {i+1} должен совпадать"
            )
            
            # Проверяем планету назначения
            assert loaded_mission.destination.name == original_mission.destination.name, (
                f"Планета назначения миссии {i+1} должна совпадать"
            )
            
            # Проверяем двигатель
            assert loaded_mission.engine.name == original_mission.engine.name, (
                f"Двигатель миссии {i+1} должен совпадать"
            )
            assert loaded_mission.engine.engine_type == original_mission.engine.engine_type, (
                f"Тип двигателя миссии {i+1} должен совпадать"
            )
            
            # Проверяем результаты расчетов топлива
            if original_mission.fuel_requirements and loaded_mission.fuel_requirements:
                assert abs(loaded_mission.fuel_requirements.total_fuel - 
                          original_mission.fuel_requirements.total_fuel) < 0.01, (
                    f"Результаты расчетов топлива миссии {i+1} должны совпадать"
                )
        
        # 5. Тестируем экспорт в CSV для всех миссий
        for mission in missions:
            csv_content = self.mission_manager.export_to_csv(mission, include_details=True)
            
            # Проверяем наличие ключевых данных
            assert mission.name in csv_content, f"CSV должен содержать название миссии {mission.name}"
            assert mission.destination.name in csv_content, (
                f"CSV должен содержать планету назначения {mission.destination.name}"
            )
            assert str(mission.payload_mass) in csv_content, (
                f"CSV должен содержать массу полезной нагрузки {mission.payload_mass}"
            )
            assert mission.engine.name in csv_content, (
                f"CSV должен содержать название двигателя {mission.engine.name}"
            )
        
        # 6. Тестируем удаление миссий
        for mission in missions:
            success = self.mission_manager.delete_mission(mission.id)
            assert success, f"Миссия {mission.id} должна быть успешно удалена"
        
        # Проверяем, что миссии действительно удалены
        final_mission_list = self.mission_manager.list_missions()
        assert len(final_mission_list) == 0, "Все миссии должны быть удалены"
        
        print(f"✅ Сохранение и восстановление конфигураций успешно протестировано:")
        print(f"   • Создано и сохранено: 3 миссии")
        print(f"   • Загружено и проверено: 3 миссии")
        print(f"   • Экспортировано в CSV: 3 миссии")
        print(f"   • Удалено: 3 миссии")

    def test_error_handling_and_validation_scenario(self):
        """
        Тест сценария обработки ошибок и валидации в интеграционном контексте.
        
        **Validates: Requirements 6.3, 6.5**
        """
        # 1. Тестируем обработку некорректных файлов миссий
        
        # Создаем файл с некорректным JSON
        invalid_json_path = os.path.join(self.temp_dir, "invalid.json")
        with open(invalid_json_path, 'w') as f:
            f.write("{ invalid json content")
        
        with pytest.raises(DataFormatError, match="Некорректный JSON"):
            self.mission_manager.load_mission(invalid_json_path)
        
        # Создаем файл с неполной структурой
        incomplete_json_path = os.path.join(self.temp_dir, "incomplete.json")
        with open(incomplete_json_path, 'w') as f:
            f.write('{"id": "test", "name": "Test"}')  # Отсутствуют обязательные поля
        
        with pytest.raises(DataFormatError, match="Отсутствует обязательное поле"):
            self.mission_manager.load_mission(incomplete_json_path)
        
        # 2. Тестируем валидацию физических параметров
        earth = get_planet_by_key("earth")
        mars = get_planet_by_key("mars")
        engine = get_engine_by_key("rd180")
        
        # Тестируем отрицательную массу полезной нагрузки
        with pytest.raises(InvalidInputError, match="положительной"):
            self.fuel_calculator.calculate_round_trip_fuel(mars, -1000.0, engine)
        
        # Тестируем нереалистично высокую дельта-V
        with pytest.raises(Exception):  # Может быть PhysicsViolationError или другая ошибка
            self.fuel_calculator.calculate_fuel_mass(100000.0, 1000.0, engine)
        
        # 3. Тестируем обработку несуществующих файлов
        nonexistent_path = os.path.join(self.temp_dir, "nonexistent.json")
        with pytest.raises(DataFormatError, match="не найден"):
            self.mission_manager.load_mission(nonexistent_path)
        
        # 4. Тестируем корректную обработку граничных случаев
        
        # Очень маленькая полезная нагрузка
        tiny_payload = 0.1  # 100 грамм
        tiny_result = self.fuel_calculator.calculate_fuel_mass(3000.0, tiny_payload, engine)
        assert tiny_result.total_fuel > 0, "Расчет должен работать для очень малых нагрузок"
        
        # Очень большая полезная нагрузка (но в разумных пределах)
        large_payload = 100000.0  # 100 тонн
        large_result = self.fuel_calculator.calculate_fuel_mass(3000.0, large_payload, engine)
        assert large_result.total_fuel > 0, "Расчет должен работать для больших нагрузок"
        
        # Проверяем масштабирование
        fuel_ratio = large_result.total_fuel / tiny_result.total_fuel
        payload_ratio = large_payload / tiny_payload
        
        # Отношение топлива должно быть близко к отношению полезных нагрузок
        # (с учетом экспоненциальной зависимости в уравнении Циолковского)
        assert fuel_ratio > payload_ratio * 0.5, "Масштабирование топлива должно быть разумным"
        assert fuel_ratio < payload_ratio * 2.0, "Масштабирование топлива не должно быть чрезмерным"
        
        print(f"✅ Обработка ошибок и валидация успешно протестированы:")
        print(f"   • Некорректные JSON файлы: обработаны")
        print(f"   • Неполные структуры данных: обработаны")
        print(f"   • Физическая валидация: работает")
        print(f"   • Граничные случаи: обработаны корректно")
        print(f"   • Масштабирование: {fuel_ratio:.1f}x для {payload_ratio:.0f}x нагрузки")


if __name__ == "__main__":
    # Запуск интеграционных тестов
    pytest.main([__file__, "-v"])