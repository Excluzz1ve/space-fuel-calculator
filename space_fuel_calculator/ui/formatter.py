"""
Форматирование и отображение результатов расчетов топлива.
"""
from typing import Optional
from datetime import datetime

from ..calculators.fuel_calculator import FuelResult
from ..models.engine import EngineType
from ..models.planet import Planet
from .trajectory_visualizer import TrajectoryVisualizer
from .trajectory_visualizer import TrajectoryVisualizer


class ResultFormatter:
    """
    Класс для форматирования и отображения результатов расчетов.
    """
    
    @staticmethod
    def format_fuel_result(result: FuelResult, show_metadata: bool = True) -> str:
        """
        Форматирует результат расчета топлива для отображения.
        
        Args:
            result: Результат расчета топлива
            show_metadata: Показывать ли метаданные и источники данных
            
        Returns:
            Отформатированная строка с результатами
        """
        lines = []
        
        # Заголовок
        lines.append("🚀 РЕЗУЛЬТАТЫ РАСЧЕТА ТОПЛИВА")
        lines.append("=" * 50)
        
        # Информация о двигателе
        lines.append(f"\n🔧 Использованный двигатель: {result.engine_used.name}")
        lines.append(f"   • Тип: {result.engine_used.engine_type.value}")
        lines.append(f"   • Удельный импульс: {result.engine_used.specific_impulse:.0f} с")
        
        # Тип траектории
        trajectory_name = "Полет туда и обратно" if result.trajectory_type == "round_trip" else "Полет в одну сторону"
        lines.append(f"\n🎯 Тип миссии: {trajectory_name}")
        
        # Требуемая дельта-V
        lines.append(f"\n📊 Требуемая дельта-V:")
        if result.return_fuel is not None:
            lines.append(f"   • Полет туда: {result.delta_v_outbound:,.0f} м/с ({result.delta_v_outbound/1000:.1f} км/с)")
            if result.delta_v_return is not None:
                lines.append(f"   • Обратный полет: {result.delta_v_return:,.0f} м/с ({result.delta_v_return/1000:.1f} км/с)")
        lines.append(f"   • Общая дельта-V: {result.total_delta_v:,.0f} м/с ({result.total_delta_v/1000:.1f} км/с)")
        
        # Результаты по топливу
        lines.append(f"\n⛽ НЕОБХОДИМОЕ ТОПЛИВО:")
        
        if result.return_fuel is not None:
            # Полет туда и обратно
            lines.append(f"   • Топливо для полета туда:")
            lines.append(f"     - {result.outbound_fuel:,.0f} кг")
            lines.append(f"     - {result.outbound_fuel/1000:.1f} тонн")
            
            lines.append(f"   • Топливо для обратного полета:")
            lines.append(f"     - {result.return_fuel:,.0f} кг")
            lines.append(f"     - {result.return_fuel/1000:.1f} тонн")
        
        lines.append(f"   • ОБЩЕЕ КОЛИЧЕСТВО ТОПЛИВА:")
        lines.append(f"     - {result.total_fuel:,.0f} кг")
        lines.append(f"     - {result.total_fuel/1000:.1f} тонн")
        
        # Дополнительная информация для ионных двигателей
        if result.engine_used.engine_type == EngineType.ION:
            from ..models.engine import IonEngine
            if isinstance(result.engine_used, IonEngine):
                # Примерный расчет времени полета для ионного двигателя
                # Время = дельта-V / ускорение, где ускорение = тяга / (масса полезной нагрузки + топливо)
                estimated_mass = result.total_fuel + 1000  # Примерная масса полезной нагрузки
                acceleration = result.engine_used.thrust / estimated_mass
                flight_time_seconds = result.total_delta_v / acceleration if acceleration > 0 else 0
                flight_time_days = flight_time_seconds / (24 * 3600)
                
                lines.append(f"\n⚡ Особенности ионного двигателя:")
                lines.append(f"   • Потребляемая мощность: {result.engine_used.power_consumption:,.0f} Вт")
                lines.append(f"   • Примерное время полета: {flight_time_days:.0f} дней")
                lines.append(f"   • Энергопотребление за полет: {result.engine_used.power_consumption * flight_time_seconds / 1e9:.1f} ГВт⋅ч")
        
        # Метаданные и источники данных
        if show_metadata:
            lines.append(f"\n📋 МЕТАДАННЫЕ:")
            lines.append(f"   • Время расчета: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            lines.append(f"   • Точность расчетов: ±5% (упрощенная модель)")
            lines.append(f"   • Источники данных:")
            lines.append(f"     - Орбитальные параметры: NASA JPL")
            lines.append(f"     - Характеристики двигателей: открытые источники")
            lines.append(f"     - Расчетная модель: уравнение Циолковского")
            
            lines.append(f"\n⚠️  ВАЖНЫЕ ЗАМЕЧАНИЯ:")
            lines.append(f"   • Расчеты основаны на упрощенной модели")
            lines.append(f"   • Не учитываются: атмосферное торможение, гравитационные маневры")
            lines.append(f"   • Для точного планирования миссии требуется детальный анализ")
        
        return "\n".join(lines)
    
    @staticmethod
    def format_mass_in_units(mass_kg: float) -> str:
        """
        Форматирует массу в килограммах и тоннах.
        
        Args:
            mass_kg: Масса в килограммах
            
        Returns:
            Отформатированная строка с массой в обеих единицах
        """
        return f"{mass_kg:,.0f} кг ({mass_kg/1000:.1f} тонн)"
    
    @staticmethod
    def format_delta_v(delta_v_ms: float) -> str:
        """
        Форматирует дельта-V в м/с и км/с.
        
        Args:
            delta_v_ms: Дельта-V в м/с
            
        Returns:
            Отформатированная строка с дельта-V в обеих единицах
        """
        return f"{delta_v_ms:,.0f} м/с ({delta_v_ms/1000:.1f} км/с)"
    
    @staticmethod
    def display_result(result: FuelResult, show_metadata: bool = True) -> None:
        """
        Отображает результат расчета в консоли.
        
        Args:
            result: Результат расчета топлива
            show_metadata: Показывать ли метаданные и источники данных
        """
        formatted_result = ResultFormatter.format_fuel_result(result, show_metadata)
        print(f"\n{formatted_result}")
    
    @staticmethod
    def format_engine_characteristics(engine) -> str:
        """
        Форматирует характеристики двигателя для отображения.
        
        Args:
            engine: Двигатель для форматирования
            
        Returns:
            Отформатированная строка с характеристиками
        """
        lines = []
        lines.append(f"🔧 {engine.name}")
        lines.append(f"   • Тип: {engine.engine_type.value}")
        lines.append(f"   • Удельный импульс: {engine.specific_impulse:.0f} с")
        # Форматируем тягу с учетом малых значений для ионных двигателей
        if engine.thrust < 1:
            lines.append(f"   • Тяга: {engine.thrust:.1f} Н ({engine.thrust/1000:.3f} кН)")
        else:
            lines.append(f"   • Тяга: {engine.thrust:,.0f} Н ({engine.thrust/1000:.0f} кН)")
        
        # Дополнительные характеристики в зависимости от типа
        if engine.engine_type == EngineType.CHEMICAL:
            from ..models.engine import ChemicalEngine
            if isinstance(engine, ChemicalEngine):
                lines.append(f"   • Тип топлива: {engine.fuel_type}")
        elif engine.engine_type == EngineType.ION:
            from ..models.engine import IonEngine
            if isinstance(engine, IonEngine):
                lines.append(f"   • Потребляемая мощность: {engine.power_consumption:,.0f} Вт")
        elif engine.engine_type == EngineType.NUCLEAR:
            from ..models.engine import NuclearEngine
            if isinstance(engine, NuclearEngine):
                lines.append(f"   • Мощность реактора: {engine.reactor_power/1e6:.0f} МВт")
                lines.append(f"   • Рабочее тело: {engine.propellant_type}")
        
        return "\n".join(lines)
    
    @staticmethod
    def format_trajectory_with_gravity_assists(origin_planet, destination_planet, 
                                             base_delta_v: float, use_assists: bool = True) -> str:
        """
        Форматирует визуализацию траектории с гравитационными маневрами.
        
        Args:
            origin_planet: Планета отправления
            destination_planet: Планета назначения
            base_delta_v: Базовая дельта-V для прямого полета в м/с
            use_assists: Использовать ли гравитационные маневры
            
        Returns:
            Отформатированная строка с визуализацией траектории
        """
        visualizer = TrajectoryVisualizer()
        return visualizer.visualize_mission_trajectory(
            origin_planet, destination_planet, base_delta_v, use_assists
        )
    
    @staticmethod
    def display_trajectory_visualization(origin_planet, destination_planet, 
                                       base_delta_v: float, use_assists: bool = True) -> None:
        """
        Отображает визуализацию траектории в консоли.
        
        Args:
            origin_planet: Планета отправления
            destination_planet: Планета назначения
            base_delta_v: Базовая дельта-V для прямого полета в м/с
            use_assists: Использовать ли гравитационные маневры
        """
        trajectory_viz = ResultFormatter.format_trajectory_with_gravity_assists(
            origin_planet, destination_planet, base_delta_v, use_assists
        )
        print(f"\n{trajectory_viz}")
    
    @staticmethod
    def get_trajectory_summary(origin_planet, destination_planet, base_delta_v: float) -> str:
        """
        Получить краткую сводку по оптимальной траектории.
        
        Args:
            origin_planet: Планета отправления
            destination_planet: Планета назначения
            base_delta_v: Базовая дельта-V для прямого полета в м/с
            
        Returns:
            Краткое описание оптимальной траектории
        """
        visualizer = TrajectoryVisualizer()
        trajectory_desc, final_delta_v, savings = visualizer.get_trajectory_summary(
            origin_planet, destination_planet, base_delta_v
        )
        
        if savings > 0:
            efficiency = (savings / base_delta_v) * 100
            return (f"{trajectory_desc} - экономия {savings:.0f} м/с ({efficiency:.1f}%)")
        else:
            return trajectory_desc
    @staticmethod
    def format_trajectory_with_gravity_assists(origin: Planet, destination: Planet, 
                                             base_delta_v: float, use_assists: bool = True) -> str:
        """
        Форматирует визуализацию траектории с гравитационными маневрами.
        
        Args:
            origin: Планета отправления
            destination: Планета назначения
            base_delta_v: Базовая дельта-V для прямого полета (м/с)
            use_assists: Использовать ли гравитационные маневры
            
        Returns:
            Отформатированная строка с визуализацией траектории
        """
        return TrajectoryVisualizer.format_trajectory_with_gravity_assists(
            origin, destination, base_delta_v, use_assists
        )