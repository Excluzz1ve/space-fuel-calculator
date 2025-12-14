"""
Property-based тесты для MissionManager.

**Feature: space-fuel-calculator, Property 16: Round-trip сериализации миссии**
**Validates: Requirements 5.2, 5.3**
"""
import pytest
import tempfile
import shutil
from pathlib import Path
from hypothesis import given, strategies as st
from datetime import datetime, timezone
import json

from space_fuel_calculator.managers import MissionManager
from space_fuel_calculator.models import Mission, Planet, ChemicalEngine, FuelResult
from space_fuel_calculator.utils.exceptions import DataFormatError

# Импортируем стратегии из существующих тестов
from .test_models_serialization import mission_strategy, planet_strategy, engine_strategy


class TestMissionManager:
    """Тесты для MissionManager."""
    
    def setup_method(self):
        """Настройка для каждого теста."""
        self.temp_dir = tempfile.mkdtemp()
        self.manager = MissionManager(self.temp_dir)
    
    def teardown_method(self):
        """Очистка после каждого теста."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @given(mission_strategy())
    def test_mission_manager_round_trip_serialization(self, mission):
        """
        **Feature: space-fuel-calculator, Property 16: Round-trip сериализации миссии**
        **Validates: Requirements 5.2, 5.3**
        
        Для любой конфигурации миссии, сохранение через MissionManager с последующей 
        загрузкой должно восстановить эквивалентную конфигурацию.
        """
        # Сохраняем миссию
        filepath = self.manager.save_mission(mission)
        
        # Проверяем, что файл создан
        assert Path(filepath).exists()
        
        # Загружаем миссию обратно
        restored_mission = self.manager.load_mission(filepath)
        
        # Проверяем эквивалентность
        assert restored_mission == mission
        assert restored_mission.id == mission.id
        assert restored_mission.name == mission.name
        assert restored_mission.destination == mission.destination
        assert restored_mission.payload_mass == mission.payload_mass
        assert restored_mission.engine == mission.engine
        assert restored_mission.use_gravity_assists == mission.use_gravity_assists
        assert restored_mission.created_at == mission.created_at
        assert restored_mission.fuel_requirements == mission.fuel_requirements
    
    @given(mission_strategy())
    def test_mission_manager_validation(self, mission):
        """
        **Feature: space-fuel-calculator, Property 18: Валидация структуры данных**
        **Validates: Requirements 5.5**
        
        Для любого файла данных миссии, парсинг должен валидировать структуру 
        против определенной схемы и отклонять некорректные файлы.
        """
        # Сохраняем валидную миссию
        filepath = self.manager.save_mission(mission)
        
        # Загружаем и проверяем, что валидация проходит
        restored_mission = self.manager.load_mission(filepath)
        assert restored_mission is not None
        
        # Портим файл и проверяем, что валидация отклоняет его
        with open(filepath, 'w') as f:
            json.dump({"invalid": "data"}, f)
        
        with pytest.raises(DataFormatError):
            self.manager.load_mission(filepath)
    
    def test_mission_manager_list_missions(self):
        """Тест получения списка миссий."""
        # Создаем несколько тестовых миссий
        missions = []
        for i in range(3):
            mission = Mission(
                id=f"test_{i}",
                name=f"Test Mission {i}",
                destination=Planet("Mars", 6.39e23, 3.39e6, 2.28e11, 5030),
                payload_mass=1000.0,
                engine=ChemicalEngine("Test Engine", 300, 1000000, "RP-1/LOX"),
                use_gravity_assists=False,
                created_at=datetime.now(timezone.utc)
            )
            missions.append(mission)
            self.manager.save_mission(mission)
        
        # Получаем список
        mission_list = self.manager.list_missions()
        
        # Проверяем, что все миссии в списке
        assert len(mission_list) == 3
        mission_ids = [m['id'] for m in mission_list]
        for mission in missions:
            assert mission.id in mission_ids
    
    def test_mission_manager_delete_mission(self):
        """Тест удаления миссии."""
        # Создаем тестовую миссию
        mission = Mission(
            id="test_delete",
            name="Test Delete Mission",
            destination=Planet("Mars", 6.39e23, 3.39e6, 2.28e11, 5030),
            payload_mass=1000.0,
            engine=ChemicalEngine("Test Engine", 300, 1000000, "RP-1/LOX"),
            use_gravity_assists=False,
            created_at=datetime.now(timezone.utc)
        )
        
        # Сохраняем миссию
        filepath = self.manager.save_mission(mission)
        assert Path(filepath).exists()
        
        # Удаляем миссию
        result = self.manager.delete_mission(mission.id)
        assert result is True
        assert not Path(filepath).exists()
        
        # Попытка удалить несуществующую миссию
        result = self.manager.delete_mission("nonexistent")
        assert result is False
    
    @given(mission_strategy())
    def test_csv_export_contains_required_data(self, mission):
        """
        **Feature: space-fuel-calculator, Property 17: Корректность CSV экспорта**
        **Validates: Requirements 5.4**
        
        Для любого результата расчета, экспортированный CSV файл должен содержать 
        все ключевые параметры миссии и результаты в правильном формате.
        """
        # Экспортируем в CSV
        csv_content = self.manager.export_to_csv(mission)
        
        # Проверяем, что CSV содержит основные данные миссии
        assert mission.id in csv_content
        assert mission.name in csv_content
        assert mission.destination.name in csv_content
        assert str(mission.payload_mass) in csv_content
        assert mission.engine.name in csv_content
        assert str(mission.engine.specific_impulse) in csv_content
        
        # Проверяем наличие заголовков
        assert "Параметр" in csv_content
        assert "Значение" in csv_content
        assert "Единицы" in csv_content
        
        # Если есть результаты расчетов, проверяем их наличие
        if mission.fuel_requirements:
            fuel = mission.fuel_requirements
            assert str(fuel.total_fuel) in csv_content
            assert str(fuel.total_delta_v) in csv_content
            assert fuel.trajectory_type in csv_content
    
    def test_csv_export_file_save(self):
        """Тест сохранения CSV экспорта в файл."""
        # Создаем тестовую миссию
        mission = Mission(
            id="test_csv",
            name="Test CSV Mission",
            destination=Planet("Mars", 6.39e23, 3.39e6, 2.28e11, 5030),
            payload_mass=1000.0,
            engine=ChemicalEngine("Test Engine", 300, 1000000, "RP-1/LOX"),
            use_gravity_assists=False,
            created_at=datetime.now(timezone.utc)
        )
        
        # Сохраняем CSV в файл
        csv_filepath = Path(self.temp_dir) / "test_export.csv"
        self.manager.save_csv_export(mission, str(csv_filepath))
        
        # Проверяем, что файл создан и содержит данные
        assert csv_filepath.exists()
        
        with open(csv_filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            assert mission.id in content
            assert mission.name in content
    
    def test_invalid_json_file_handling(self):
        """Тест обработки некорректных JSON файлов."""
        # Создаем файл с некорректным JSON
        invalid_file = Path(self.temp_dir) / "invalid.json"
        with open(invalid_file, 'w') as f:
            f.write("{ invalid json }")
        
        # Проверяем, что загрузка вызывает исключение
        with pytest.raises(DataFormatError):
            self.manager.load_mission(str(invalid_file))
    
    def test_nonexistent_file_handling(self):
        """Тест обработки несуществующих файлов."""
        nonexistent_file = Path(self.temp_dir) / "nonexistent.json"
        
        # Проверяем, что загрузка вызывает исключение
        with pytest.raises(DataFormatError):
            self.manager.load_mission(str(nonexistent_file))