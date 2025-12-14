"""
Менеджер для управления миссиями: сохранение, загрузка и валидация.
"""
import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import csv
import io

from ..models.mission import Mission, FuelResult
from ..utils.exceptions import DataFormatError


class MissionManager:
    """
    Класс для управления конфигурациями миссий.
    
    Обеспечивает сохранение миссий в JSON, загрузку сохраненных миссий,
    валидацию структуры файлов и экспорт результатов в CSV.
    """
    
    def __init__(self, missions_dir: str = "missions"):
        """
        Инициализация менеджера миссий.
        
        Args:
            missions_dir: Директория для сохранения файлов миссий
        """
        self.missions_dir = Path(missions_dir)
        self.missions_dir.mkdir(exist_ok=True)
    
    def save_mission(self, mission: Mission) -> str:
        """
        Сохранение конфигурации миссии в JSON файл.
        
        Args:
            mission: Объект миссии для сохранения
            
        Returns:
            Путь к сохраненному файлу
            
        Raises:
            DataFormatError: При ошибке сериализации
        """
        try:
            filename = f"{mission.id}_{mission.name.replace(' ', '_')}.json"
            filepath = self.missions_dir / filename
            
            mission_data = mission.to_dict()
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(mission_data, f, ensure_ascii=False, indent=2)
            
            return str(filepath)
            
        except Exception as e:
            raise DataFormatError(f"Ошибка сохранения миссии {mission.id}: {e}")
    
    def load_mission(self, filepath: str) -> Mission:
        """
        Загрузка миссии из JSON файла.
        
        Args:
            filepath: Путь к файлу миссии
            
        Returns:
            Объект миссии
            
        Raises:
            DataFormatError: При ошибке загрузки или валидации
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Валидация структуры файла
            self._validate_mission_structure(data)
            
            return Mission.from_dict(data)
            
        except FileNotFoundError:
            raise DataFormatError(f"Файл миссии не найден: {filepath}")
        except json.JSONDecodeError as e:
            raise DataFormatError(f"Некорректный JSON в файле {filepath}: {e}")
        except Exception as e:
            raise DataFormatError(f"Ошибка загрузки миссии из {filepath}: {e}")
    
    def list_missions(self) -> List[Dict[str, Any]]:
        """
        Получение списка всех сохраненных миссий.
        
        Returns:
            Список словарей с информацией о миссиях
        """
        missions = []
        
        for filepath in self.missions_dir.glob("*.json"):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                missions.append({
                    'id': data.get('id'),
                    'name': data.get('name'),
                    'destination': data.get('destination', {}).get('name'),
                    'created_at': data.get('created_at'),
                    'filepath': str(filepath)
                })
            except Exception:
                # Пропускаем поврежденные файлы
                continue
        
        return sorted(missions, key=lambda x: x['created_at'], reverse=True)
    
    def delete_mission(self, mission_id: str) -> bool:
        """
        Удаление миссии по ID.
        
        Args:
            mission_id: Идентификатор миссии
            
        Returns:
            True если миссия была удалена, False если не найдена
        """
        for filepath in self.missions_dir.glob(f"{mission_id}_*.json"):
            try:
                filepath.unlink()
                return True
            except Exception:
                continue
        
        return False
    
    def export_to_csv(self, mission: Mission, include_details: bool = True) -> str:
        """
        Экспорт результатов миссии в CSV формат.
        
        Args:
            mission: Миссия для экспорта
            include_details: Включать ли детализированные расчеты
            
        Returns:
            CSV строка с данными миссии
            
        Raises:
            DataFormatError: При ошибке экспорта
        """
        try:
            output = io.StringIO()
            writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
            
            # Заголовок
            writer.writerow(['Параметр', 'Значение', 'Единицы'])
            
            # Основная информация о миссии
            writer.writerow(['ID миссии', mission.id, ''])
            writer.writerow(['Название', mission.name, ''])
            writer.writerow(['Планета назначения', mission.destination.name, ''])
            writer.writerow(['Масса полезной нагрузки', mission.payload_mass, 'кг'])
            writer.writerow(['Двигатель', mission.engine.name, ''])
            writer.writerow(['Удельный импульс', mission.engine.specific_impulse, 'с'])
            writer.writerow(['Тяга', mission.engine.thrust, 'Н'])
            writer.writerow(['Гравитационные маневры', 'Да' if mission.use_gravity_assists else 'Нет', ''])
            writer.writerow(['Дата создания', mission.created_at.strftime('%Y-%m-%d %H:%M:%S'), ''])
            
            # Результаты расчетов (если есть)
            if mission.fuel_requirements:
                writer.writerow(['', '', ''])  # Пустая строка
                writer.writerow(['РЕЗУЛЬТАТЫ РАСЧЕТОВ', '', ''])
                
                fuel = mission.fuel_requirements
                writer.writerow(['Топливо туда', fuel.outbound_fuel, 'кг'])
                writer.writerow(['Топливо туда', fuel.outbound_fuel / 1000, 'т'])
                
                if fuel.return_fuel is not None:
                    writer.writerow(['Топливо обратно', fuel.return_fuel, 'кг'])
                    writer.writerow(['Топливо обратно', fuel.return_fuel / 1000, 'т'])
                
                writer.writerow(['Общее топливо', fuel.total_fuel, 'кг'])
                writer.writerow(['Общее топливо', fuel.total_fuel / 1000, 'т'])
                
                writer.writerow(['Дельта-V туда', fuel.delta_v_outbound, 'м/с'])
                if fuel.delta_v_return is not None:
                    writer.writerow(['Дельта-V обратно', fuel.delta_v_return, 'м/с'])
                writer.writerow(['Общая дельта-V', fuel.total_delta_v, 'м/с'])
                writer.writerow(['Тип траектории', fuel.trajectory_type, ''])
                
                if include_details:
                    writer.writerow(['', '', ''])  # Пустая строка
                    writer.writerow(['ДЕТАЛИ ПЛАНЕТЫ', '', ''])
                    planet = mission.destination
                    writer.writerow(['Масса планеты', f"{planet.mass:.2e}", 'кг'])
                    writer.writerow(['Радиус планеты', planet.radius, 'м'])
                    writer.writerow(['Орбитальный радиус', f"{planet.orbital_radius:.2e}", 'м'])
                    writer.writerow(['Скорость убегания', planet.escape_velocity, 'м/с'])
            
            return output.getvalue()
            
        except Exception as e:
            raise DataFormatError(f"Ошибка экспорта миссии в CSV: {e}")
    
    def save_csv_export(self, mission: Mission, filepath: str, include_details: bool = True) -> None:
        """
        Сохранение экспорта миссии в CSV файл.
        
        Args:
            mission: Миссия для экспорта
            filepath: Путь для сохранения CSV файла
            include_details: Включать ли детализированные расчеты
        """
        csv_content = self.export_to_csv(mission, include_details)
        
        with open(filepath, 'w', encoding='utf-8', newline='') as f:
            f.write(csv_content)
    
    def _validate_mission_structure(self, data: Dict[str, Any]) -> None:
        """
        Валидация структуры данных миссии.
        
        Args:
            data: Словарь с данными миссии
            
        Raises:
            DataFormatError: При некорректной структуре
        """
        required_fields = [
            'id', 'name', 'destination', 'payload_mass', 
            'engine', 'use_gravity_assists', 'created_at'
        ]
        
        # Проверка обязательных полей
        for field in required_fields:
            if field not in data:
                raise DataFormatError(f"Отсутствует обязательное поле: {field}")
        
        # Проверка типов данных
        if not isinstance(data['id'], str) or not data['id']:
            raise DataFormatError("Поле 'id' должно быть непустой строкой")
        
        if not isinstance(data['name'], str) or not data['name']:
            raise DataFormatError("Поле 'name' должно быть непустой строкой")
        
        if not isinstance(data['payload_mass'], (int, float)) or data['payload_mass'] < 0:
            raise DataFormatError("Поле 'payload_mass' должно быть неотрицательным числом")
        
        if not isinstance(data['use_gravity_assists'], bool):
            raise DataFormatError("Поле 'use_gravity_assists' должно быть булевым значением")
        
        # Проверка структуры планеты
        destination = data['destination']
        if not isinstance(destination, dict):
            raise DataFormatError("Поле 'destination' должно быть объектом")
        
        planet_fields = ['name', 'mass', 'radius', 'orbital_radius', 'escape_velocity']
        for field in planet_fields:
            if field not in destination:
                raise DataFormatError(f"Отсутствует поле планеты: {field}")
        
        # Проверка структуры двигателя
        engine = data['engine']
        if not isinstance(engine, dict):
            raise DataFormatError("Поле 'engine' должно быть объектом")
        
        engine_fields = ['type', 'name', 'specific_impulse', 'thrust']
        for field in engine_fields:
            if field not in engine:
                raise DataFormatError(f"Отсутствует поле двигателя: {field}")
        
        # Проверка даты
        try:
            datetime.fromisoformat(data['created_at'])
        except ValueError:
            raise DataFormatError("Некорректный формат даты в поле 'created_at'")
        
        # Проверка результатов топлива (если есть)
        if data.get('fuel_requirements'):
            fuel_data = data['fuel_requirements']
            if not isinstance(fuel_data, dict):
                raise DataFormatError("Поле 'fuel_requirements' должно быть объектом")
            
            fuel_fields = [
                'outbound_fuel', 'total_fuel', 'delta_v_outbound', 
                'total_delta_v', 'engine_used', 'trajectory_type'
            ]
            for field in fuel_fields:
                if field not in fuel_data:
                    raise DataFormatError(f"Отсутствует поле результатов: {field}")