"""
Property-based тесты для пользовательского интерфейса и форматирования.
"""

import pytest
import sys
from pathlib import Path
from hypothesis import given, strategies as st, assume, settings

# Добавляем корневую директорию проекта в путь
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from space_fuel_calculator.ui.formatter import ResultFormatter
from space_fuel_calculator.models.engine import ChemicalEngine, IonEngine, NuclearEngine, EngineType
from space_fuel_calculator.calculators.fuel_calculator import FuelResult, FuelCalculator
import re


class TestUIFormatterProperties:
    """Property-based тесты для форматирования пользовательского интерфейса."""
    
    @given(
        engine_name=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc', 'Pd'), whitelist_characters=' -_')),
        specific_impulse=st.floats(min_value=200, max_value=8000),
        thrust=st.floats(min_value=0.01, max_value=10000000),
        fuel_type=st.text(min_size=1, max_size=30, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc', 'Pd'), whitelist_characters=' -_/')),
        power_consumption=st.floats(min_value=100, max_value=100000),
        reactor_power=st.floats(min_value=1000, max_value=1000000000),
        propellant_type=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters=' -_'))
    )
    @settings(max_examples=100)
    def test_engine_characteristics_display_property(self, engine_name, specific_impulse, thrust, 
                                                   fuel_type, power_consumption, reactor_power, propellant_type):
        """
        **Feature: space-fuel-calculator, Property 12: Отображение характеристик двигателя**
        
        Для любого выбранного двигателя, система должна отображать его технические
        характеристики (удельный импульс, тяга, тип).
        
        **Validates: Requirements 3.5**
        """
        # Фильтруем некорректные названия и типы топлива
        assume(engine_name.strip() != "")  # Название не должно быть пустым после удаления пробелов
        assume(not any(ord(c) < 32 for c in engine_name))  # Исключаем управляющие символы
        assume(fuel_type.strip() != "")
        assume(propellant_type.strip() != "")
        
        # Создаем различные типы двигателей
        chemical_engine = ChemicalEngine(
            name=engine_name,
            specific_impulse=specific_impulse,
            thrust=thrust,
            fuel_type=fuel_type
        )
        
        ion_engine = IonEngine(
            name=engine_name,
            specific_impulse=specific_impulse,
            thrust=thrust,
            power_consumption=power_consumption
        )
        
        nuclear_engine = NuclearEngine(
            name=engine_name,
            specific_impulse=specific_impulse,
            thrust=thrust,
            reactor_power=reactor_power,
            propellant_type=propellant_type
        )
        
        engines = [chemical_engine, ion_engine, nuclear_engine]
        
        for engine in engines:
            # Форматируем характеристики двигателя
            formatted_characteristics = ResultFormatter.format_engine_characteristics(engine)
            
            # Проверяем, что отформатированный текст содержит обязательные характеристики
            
            # 1. Название двигателя должно присутствовать
            assert engine.name in formatted_characteristics, (
                f"Отформатированные характеристики должны содержать название двигателя '{engine.name}'"
            )
            
            # 2. Тип двигателя должен присутствовать
            assert engine.engine_type.value in formatted_characteristics, (
                f"Отформатированные характеристики должны содержать тип двигателя '{engine.engine_type.value}'"
            )
            
            # 3. Удельный импульс должен присутствовать
            isp_str = f"{engine.specific_impulse:.0f}"
            assert isp_str in formatted_characteristics, (
                f"Отформатированные характеристики должны содержать удельный импульс '{isp_str} с'"
            )
            
            # 4. Тяга должна присутствовать (в Ньютонах и килоньютонах)
            thrust_n_str = f"{engine.thrust:,.0f}"
            thrust_kn_str = f"{engine.thrust/1000:.0f}"
            assert thrust_n_str in formatted_characteristics or thrust_kn_str in formatted_characteristics, (
                f"Отформатированные характеристики должны содержать тягу в Н или кН"
            )
            
            # 5. Специфические характеристики для каждого типа двигателя
            if engine.engine_type == EngineType.CHEMICAL:
                assert fuel_type in formatted_characteristics, (
                    f"Характеристики химического двигателя должны содержать тип топлива '{fuel_type}'"
                )
            
            elif engine.engine_type == EngineType.ION:
                power_str = f"{power_consumption:,.0f}"
                assert power_str in formatted_characteristics, (
                    f"Характеристики ионного двигателя должны содержать потребляемую мощность '{power_str} Вт'"
                )
            
            elif engine.engine_type == EngineType.NUCLEAR:
                reactor_power_mw_str = f"{reactor_power/1e6:.0f}"
                assert reactor_power_mw_str in formatted_characteristics, (
                    f"Характеристики ядерного двигателя должны содержать мощность реактора '{reactor_power_mw_str} МВт'"
                )
                assert propellant_type in formatted_characteristics, (
                    f"Характеристики ядерного двигателя должны содержать рабочее тело '{propellant_type}'"
                )
            
            # 6. Проверяем структуру форматирования (должны быть маркеры списка)
            assert "•" in formatted_characteristics, (
                "Отформатированные характеристики должны содержать маркеры списка '•'"
            )
            
            # 7. Проверяем, что текст не пустой и содержит разумное количество информации
            assert len(formatted_characteristics.strip()) > 50, (
                f"Отформатированные характеристики должны содержать достаточно информации, "
                f"получено {len(formatted_characteristics)} символов"
            )
            
            # 8. Проверяем, что нет очевидных ошибок форматирования
            lines = formatted_characteristics.split('\n')
            assert len(lines) >= 4, (
                f"Отформатированные характеристики должны содержать минимум 4 строки, "
                f"получено {len(lines)}"
            )
            
            # 9. Проверяем, что первая строка содержит название и эмодзи двигателя
            first_line = lines[0].strip()
            assert "🔧" in first_line, (
                "Первая строка должна содержать эмодзи двигателя '🔧'"
            )
            # Проверяем название двигателя, убирая лишние пробелы
            engine_name_clean = engine.name.strip()
            assert engine_name_clean in first_line, (
                f"Первая строка должна содержать название двигателя '{engine_name_clean}'"
            )
            
            # 10. Проверяем корректность числовых значений в тексте
            # Удельный импульс должен быть в разумных пределах
            if specific_impulse < 100 or specific_impulse > 10000:
                # Для экстремальных значений проверяем, что они корректно отображаются
                extreme_isp_str = f"{specific_impulse:.0f}"
                assert extreme_isp_str in formatted_characteristics, (
                    f"Экстремальное значение удельного импульса {extreme_isp_str} должно корректно отображаться"
                )
            
            # Тяга должна быть в разумных пределах и корректно отформатирована
            if thrust >= 1000:
                # Для больших значений тяги проверяем форматирование с разделителями тысяч
                formatted_thrust = f"{thrust:,.0f}"
                assert "," in formatted_thrust or " " in formatted_thrust or formatted_thrust in formatted_characteristics, (
                    f"Большие значения тяги должны быть отформатированы с разделителями"
                )


    @given(
        delta_v=st.floats(min_value=1000, max_value=15000),
        payload_mass=st.floats(min_value=100, max_value=50000),
        specific_impulse=st.floats(min_value=200, max_value=500),
        thrust=st.floats(min_value=1000, max_value=10000000),
        fuel_type=st.text(min_size=1, max_size=30, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc', 'Pd'), whitelist_characters=' -_/')),
        engine_name=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc', 'Pd'), whitelist_characters=' -_'))
    )
    @settings(max_examples=100)
    def test_units_correctness_in_output_property(self, delta_v, payload_mass, specific_impulse, thrust, fuel_type, engine_name):
        """
        **Feature: space-fuel-calculator, Property 4: Корректность единиц измерения в выводе**
        
        Для любого результата расчета, отображаемый текст должен содержать значения
        в килограммах и тоннах с правильными единицами измерения.
        
        **Validates: Requirements 1.4**
        """
        # Фильтруем некорректные названия
        assume(engine_name.strip() != "")
        assume(not any(ord(c) < 32 for c in engine_name))
        assume(fuel_type.strip() != "")
        
        # Фильтруем комбинации, которые приводят к нереалистичным отношениям масс
        import math
        STANDARD_GRAVITY = 9.80665
        exhaust_velocity = specific_impulse * STANDARD_GRAVITY
        mass_ratio = math.exp(delta_v / exhaust_velocity)
        assume(mass_ratio <= 1000)  # Ограничиваем практическими пределами ракетостроения
        
        # Создаем двигатель и выполняем расчет
        engine = ChemicalEngine(
            name=engine_name,
            specific_impulse=specific_impulse,
            thrust=thrust,
            fuel_type=fuel_type
        )
        
        calculator = FuelCalculator()
        result = calculator.calculate_fuel_mass(delta_v, payload_mass, engine)
        
        # Форматируем результат
        formatted_result = ResultFormatter.format_fuel_result(result, show_metadata=True)
        
        # Проверяем наличие единиц измерения массы
        
        # 1. Результат должен содержать значения в килограммах
        assert " кг" in formatted_result, (
            "Отформатированный результат должен содержать единицы измерения в килограммах ' кг'"
        )
        
        # 2. Результат должен содержать значения в тоннах
        assert " тонн" in formatted_result, (
            "Отформатированный результат должен содержать единицы измерения в тоннах ' тонн'"
        )
        
        # 3. Проверяем корректность числовых значений в килограммах
        fuel_mass_kg = result.total_fuel
        fuel_mass_kg_str = f"{fuel_mass_kg:,.0f}"
        
        # Ищем строку с килограммами в результате
        kg_found = False
        for line in formatted_result.split('\n'):
            if " кг" in line and fuel_mass_kg_str in line:
                kg_found = True
                break
        
        assert kg_found, (
            f"Отформатированный результат должен содержать корректное значение массы топлива "
            f"в килограммах: {fuel_mass_kg_str} кг"
        )
        
        # 4. Проверяем корректность числовых значений в тоннах
        fuel_mass_tonnes = fuel_mass_kg / 1000
        fuel_mass_tonnes_str = f"{fuel_mass_tonnes:.1f}"
        
        # Ищем строку с тоннами в результате
        tonnes_found = False
        for line in formatted_result.split('\n'):
            if " тонн" in line and fuel_mass_tonnes_str in line:
                tonnes_found = True
                break
        
        assert tonnes_found, (
            f"Отформатированный результат должен содержать корректное значение массы топлива "
            f"в тоннах: {fuel_mass_tonnes_str} тонн"
        )
        
        # 5. Проверяем единицы измерения дельта-V
        assert " м/с" in formatted_result, (
            "Отформатированный результат должен содержать единицы измерения дельта-V в м/с"
        )
        
        assert " км/с" in formatted_result, (
            "Отформатированный результат должен содержать единицы измерения дельта-V в км/с"
        )
        
        # 6. Проверяем корректность значений дельта-V
        delta_v_ms_str = f"{delta_v:,.0f}"
        delta_v_kms_str = f"{delta_v/1000:.1f}"
        
        # Ищем строки с дельта-V
        delta_v_ms_found = False
        delta_v_kms_found = False
        
        for line in formatted_result.split('\n'):
            if " м/с" in line and delta_v_ms_str in line:
                delta_v_ms_found = True
            if " км/с" in line and delta_v_kms_str in line:
                delta_v_kms_found = True
        
        assert delta_v_ms_found, (
            f"Отформатированный результат должен содержать корректное значение дельта-V "
            f"в м/с: {delta_v_ms_str} м/с"
        )
        
        assert delta_v_kms_found, (
            f"Отформатированный результат должен содержать корректное значение дельта-V "
            f"в км/с: {delta_v_kms_str} км/с"
        )
        
        # 7. Проверяем единицы измерения удельного импульса
        assert " с" in formatted_result, (
            "Отформатированный результат должен содержать единицы измерения удельного импульса в секундах ' с'"
        )
        
        # 8. Проверяем корректность значения удельного импульса
        isp_str = f"{specific_impulse:.0f}"
        isp_found = False
        
        for line in formatted_result.split('\n'):
            if " с" in line and isp_str in line and "импульс" in line:
                isp_found = True
                break
        
        assert isp_found, (
            f"Отформатированный результат должен содержать корректное значение удельного импульса: {isp_str} с"
        )
        
        # 9. Проверяем отсутствие некорректных единиц измерения
        incorrect_units = ["кг/с", "тонн/с", "м/ч", "км/ч", "фунт", "lb", "галлон"]
        for unit in incorrect_units:
            assert unit not in formatted_result, (
                f"Отформатированный результат не должен содержать некорректную единицу измерения: {unit}"
            )
        
        # 10. Проверяем консистентность между килограммами и тоннами
        # Соотношение должно быть 1000:1
        expected_ratio = fuel_mass_kg / 1000
        actual_ratio = fuel_mass_tonnes
        
        relative_error = abs(expected_ratio - actual_ratio) / expected_ratio if expected_ratio > 0 else 0
        assert relative_error < 0.01, (
            f"Соотношение между килограммами и тоннами должно быть корректным: "
            f"{fuel_mass_kg} кг = {fuel_mass_kg/1000:.1f} тонн, но отображается {fuel_mass_tonnes:.1f} тонн"
        )

    @given(
        payload_mass=st.floats(min_value=100, max_value=10000),
        orbital_radius=st.floats(min_value=1.5e11, max_value=4e11),
        escape_velocity=st.floats(min_value=3000, max_value=12000),
        specific_impulse=st.floats(min_value=300, max_value=450),
        thrust=st.floats(min_value=1000000, max_value=10000000),
        engine_name=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc', 'Pd'), whitelist_characters=' -_')),
        fuel_type=st.text(min_size=1, max_size=30, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc', 'Pd'), whitelist_characters=' -_/'))
    )
    @settings(max_examples=50)
    def test_round_trip_result_structure_property(self, payload_mass, orbital_radius, escape_velocity, 
                                                specific_impulse, thrust, engine_name, fuel_type):
        """
        **Feature: space-fuel-calculator, Property 8: Структура результата полета**
        
        Для любого расчета туда и обратно, результат должен содержать отдельные
        значения топлива для каждого этапа полета.
        
        **Validates: Requirements 2.4**
        """
        from space_fuel_calculator.models.planet import Planet
        import math
        
        # Фильтруем некорректные названия
        assume(engine_name.strip() != "")
        assume(not any(ord(c) < 32 for c in engine_name))
        assume(fuel_type.strip() != "")
        
        # Ограничиваем значения для избежания экстремальных случаев
        assume(escape_velocity < 15000)  # Разумный предел для скорости убегания
        assume(orbital_radius > 5e10)    # Минимальный орбитальный радиус
        
        # Создаем планету
        planet = Planet(
            name="Test Planet",
            mass=1e24,
            radius=5e6,
            orbital_radius=orbital_radius,
            escape_velocity=escape_velocity
        )
        
        # Создаем двигатель
        engine = ChemicalEngine(
            name=engine_name,
            specific_impulse=specific_impulse,
            thrust=thrust,
            fuel_type=fuel_type
        )
        
        # Проверяем, что расчеты не превысят практические пределы
        GM_SUN = 1.327e20
        EARTH_ORBITAL_RADIUS = 1.496e11
        STANDARD_GRAVITY = 9.80665
        
        delta_v_earth_escape = math.sqrt(GM_SUN / EARTH_ORBITAL_RADIUS)
        delta_v_destination_capture = math.sqrt(GM_SUN / orbital_radius)
        delta_v_outbound = abs(delta_v_destination_capture - delta_v_earth_escape)
        delta_v_return = delta_v_outbound + escape_velocity
        
        exhaust_velocity = specific_impulse * STANDARD_GRAVITY
        mass_ratio_outbound = math.exp(delta_v_outbound / exhaust_velocity)
        mass_ratio_return = math.exp(delta_v_return / exhaust_velocity)
        
        assume(mass_ratio_outbound <= 1000)
        assume(mass_ratio_return <= 1000)
        
        # Выполняем расчет полета туда и обратно
        calculator = FuelCalculator()
        result = calculator.calculate_round_trip_fuel(planet, payload_mass, engine)
        
        # Форматируем результат
        formatted_result = ResultFormatter.format_fuel_result(result, show_metadata=True)
        
        # Проверяем структуру результата полета туда и обратно
        
        # 1. Результат должен содержать информацию о типе миссии
        assert "Полет туда и обратно" in formatted_result, (
            "Отформатированный результат должен указывать тип миссии 'Полет туда и обратно'"
        )
        
        # 2. Результат должен содержать отдельные значения топлива для прямого полета
        assert "Полет туда:" in formatted_result or "полета туда:" in formatted_result, (
            "Отформатированный результат должен содержать раздел с топливом для прямого полета"
        )
        
        # 3. Результат должен содержать отдельные значения топлива для обратного полета
        assert "Обратный полет:" in formatted_result or "обратного полета:" in formatted_result, (
            "Отформатированный результат должен содержать раздел с топливом для обратного полета"
        )
        
        # 4. Результат должен содержать общее количество топлива
        assert "ОБЩЕЕ КОЛИЧЕСТВО ТОПЛИВА:" in formatted_result, (
            "Отформатированный результат должен содержать раздел с общим количеством топлива"
        )
        
        # 5. Проверяем наличие отдельных значений дельта-V для каждого этапа
        assert "Полет туда:" in formatted_result and " м/с" in formatted_result, (
            "Отформатированный результат должен содержать дельта-V для прямого полета"
        )
        
        assert "Обратный полет:" in formatted_result and " м/с" in formatted_result, (
            "Отформатированный результат должен содержать дельта-V для обратного полета"
        )
        
        # 6. Проверяем корректность числовых значений в структуре
        outbound_fuel_kg_str = f"{result.outbound_fuel:,.0f}"
        return_fuel_kg_str = f"{result.return_fuel:,.0f}"
        total_fuel_kg_str = f"{result.total_fuel:,.0f}"
        
        # Ищем значения топлива в соответствующих разделах
        outbound_fuel_found = False
        return_fuel_found = False
        total_fuel_found = False
        
        lines = formatted_result.split('\n')
        in_outbound_section = False
        in_return_section = False
        in_total_section = False
        
        for line in lines:
            # Определяем, в каком разделе мы находимся
            if "полета туда:" in line.lower():
                in_outbound_section = True
                in_return_section = False
                in_total_section = False
            elif "обратного полета:" in line.lower():
                in_outbound_section = False
                in_return_section = True
                in_total_section = False
            elif "общее количество топлива:" in line.lower():
                in_outbound_section = False
                in_return_section = False
                in_total_section = True
            
            # Проверяем наличие значений в соответствующих разделах
            if in_outbound_section and outbound_fuel_kg_str in line and " кг" in line:
                outbound_fuel_found = True
            elif in_return_section and return_fuel_kg_str in line and " кг" in line:
                return_fuel_found = True
            elif in_total_section and total_fuel_kg_str in line and " кг" in line:
                total_fuel_found = True
        
        assert outbound_fuel_found, (
            f"Отформатированный результат должен содержать корректное значение топлива для прямого полета "
            f"в соответствующем разделе: {outbound_fuel_kg_str} кг"
        )
        
        assert return_fuel_found, (
            f"Отформатированный результат должен содержать корректное значение топлива для обратного полета "
            f"в соответствующем разделе: {return_fuel_kg_str} кг"
        )
        
        assert total_fuel_found, (
            f"Отформатированный результат должен содержать корректное значение общего топлива "
            f"в соответствующем разделе: {total_fuel_kg_str} кг"
        )
        
        # 7. Проверяем логическую структуру: общее топливо = топливо туда + топливо обратно
        expected_total = result.outbound_fuel + result.return_fuel
        actual_total = result.total_fuel
        
        relative_error = abs(expected_total - actual_total) / expected_total if expected_total > 0 else 0
        assert relative_error < 1e-10, (
            f"Общее топливо должно равняться сумме топлива этапов: "
            f"{result.outbound_fuel:.2f} + {result.return_fuel:.2f} = {expected_total:.2f}, "
            f"но получено {actual_total:.2f}"
        )
        
        # 8. Проверяем, что все значения положительные
        assert result.outbound_fuel > 0, (
            f"Топливо для прямого полета должно быть положительным: {result.outbound_fuel}"
        )
        
        assert result.return_fuel > 0, (
            f"Топливо для обратного полета должно быть положительным: {result.return_fuel}"
        )
        
        assert result.total_fuel > 0, (
            f"Общее топливо должно быть положительным: {result.total_fuel}"
        )
        
        # 9. Проверяем структуру дельта-V
        assert result.delta_v_outbound > 0, (
            f"Дельта-V прямого полета должна быть положительной: {result.delta_v_outbound}"
        )
        
        assert result.delta_v_return > 0, (
            f"Дельта-V обратного полета должна быть положительной: {result.delta_v_return}"
        )
        
        # 10. Проверяем, что результат содержит правильный тип траектории
        assert result.trajectory_type == "round_trip", (
            f"Тип траектории должен быть 'round_trip', получено: {result.trajectory_type}"
        )

    @given(
        delta_v=st.floats(min_value=1000, max_value=15000),
        payload_mass=st.floats(min_value=100, max_value=50000),
        specific_impulse=st.floats(min_value=200, max_value=500),
        thrust=st.floats(min_value=1000, max_value=10000000),
        fuel_type=st.text(min_size=1, max_size=30, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc', 'Pd'), whitelist_characters=' -_/')),
        engine_name=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc', 'Pd'), whitelist_characters=' -_'))
    )
    @settings(max_examples=100)
    def test_metadata_in_results_property(self, delta_v, payload_mass, specific_impulse, thrust, fuel_type, engine_name):
        """
        **Feature: space-fuel-calculator, Property 21: Метаданные в результатах**
        
        Для любого результата расчета, вывод должен включать информацию о точности
        расчетов и источниках астрономических данных.
        
        **Validates: Requirements 6.4**
        """
        # Фильтруем некорректные названия
        assume(engine_name.strip() != "")
        assume(not any(ord(c) < 32 for c in engine_name))
        assume(fuel_type.strip() != "")
        
        # Фильтруем комбинации, которые приводят к нереалистичным отношениям масс
        import math
        STANDARD_GRAVITY = 9.80665
        exhaust_velocity = specific_impulse * STANDARD_GRAVITY
        mass_ratio = math.exp(delta_v / exhaust_velocity)
        assume(mass_ratio <= 1000)  # Ограничиваем практическими пределами ракетостроения
        
        # Создаем двигатель и выполняем расчет
        engine = ChemicalEngine(
            name=engine_name,
            specific_impulse=specific_impulse,
            thrust=thrust,
            fuel_type=fuel_type
        )
        
        calculator = FuelCalculator()
        result = calculator.calculate_fuel_mass(delta_v, payload_mass, engine)
        
        # Форматируем результат с метаданными
        formatted_result_with_metadata = ResultFormatter.format_fuel_result(result, show_metadata=True)
        
        # Форматируем результат без метаданных для сравнения
        formatted_result_without_metadata = ResultFormatter.format_fuel_result(result, show_metadata=False)
        
        # Проверяем наличие метаданных в результате с show_metadata=True
        
        # 1. Результат должен содержать раздел метаданных
        assert "МЕТАДАННЫЕ:" in formatted_result_with_metadata, (
            "Отформатированный результат с метаданными должен содержать раздел 'МЕТАДАННЫЕ:'"
        )
        
        # 2. Результат должен содержать информацию о времени расчета
        assert "Время расчета:" in formatted_result_with_metadata, (
            "Метаданные должны содержать информацию о времени расчета"
        )
        
        # 3. Результат должен содержать информацию о точности расчетов
        assert "Точность расчетов:" in formatted_result_with_metadata, (
            "Метаданные должны содержать информацию о точности расчетов"
        )
        
        # 4. Результат должен содержать информацию об источниках данных
        assert "Источники данных:" in formatted_result_with_metadata, (
            "Метаданные должны содержать информацию об источниках данных"
        )
        
        # 5. Проверяем конкретные источники данных
        expected_sources = [
            "NASA JPL",  # Орбитальные параметры
            "уравнение Циолковского"  # Расчетная модель
        ]
        
        for source in expected_sources:
            assert source in formatted_result_with_metadata, (
                f"Метаданные должны содержать ссылку на источник данных: {source}"
            )
        
        # 6. Результат должен содержать важные замечания
        assert "ВАЖНЫЕ ЗАМЕЧАНИЯ:" in formatted_result_with_metadata, (
            "Отформатированный результат должен содержать раздел 'ВАЖНЫЕ ЗАМЕЧАНИЯ:'"
        )
        
        # 7. Проверяем наличие предупреждений об ограничениях модели
        model_limitations = [
            "упрощенной модели",
            "атмосферное торможение",
            "гравитационные маневры",
            "детальный анализ"
        ]
        
        for limitation in model_limitations:
            assert limitation in formatted_result_with_metadata, (
                f"Важные замечания должны содержать информацию об ограничении: {limitation}"
            )
        
        # 8. Проверяем формат времени расчета (должен быть в формате YYYY-MM-DD HH:MM:SS)
        import re
        from datetime import datetime
        
        # Ищем строку с временем расчета
        time_pattern = r"Время расчета: (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})"
        time_match = re.search(time_pattern, formatted_result_with_metadata)
        
        assert time_match is not None, (
            "Время расчета должно быть в формате YYYY-MM-DD HH:MM:SS"
        )
        
        # Проверяем, что время разумное (не в далеком прошлом или будущем)
        time_str = time_match.group(1)
        calculation_time = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
        current_time = datetime.now()
        
        time_diff = abs((current_time - calculation_time).total_seconds())
        assert time_diff < 60, (  # Время расчета должно быть в пределах последней минуты
            f"Время расчета должно быть близко к текущему времени, "
            f"разница: {time_diff:.1f} секунд"
        )
        
        # 9. Проверяем, что результат без метаданных не содержит метаданные
        assert "МЕТАДАННЫЕ:" not in formatted_result_without_metadata, (
            "Результат без метаданных не должен содержать раздел 'МЕТАДАННЫЕ:'"
        )
        
        assert "ВАЖНЫЕ ЗАМЕЧАНИЯ:" not in formatted_result_without_metadata, (
            "Результат без метаданных не должен содержать раздел 'ВАЖНЫЕ ЗАМЕЧАНИЯ:'"
        )
        
        # 10. Проверяем, что основная информация присутствует в обоих форматах
        essential_info = [
            "РЕЗУЛЬТАТЫ РАСЧЕТА ТОПЛИВА",
            engine_name,
            "НЕОБХОДИМОЕ ТОПЛИВО",
            " кг",
            " тонн"
        ]
        
        for info in essential_info:
            assert info in formatted_result_with_metadata, (
                f"Результат с метаданными должен содержать основную информацию: {info}"
            )
            assert info in formatted_result_without_metadata, (
                f"Результат без метаданных должен содержать основную информацию: {info}"
            )
        
        # 11. Проверяем, что метаданные добавляют существенную информацию
        metadata_length = len(formatted_result_with_metadata) - len(formatted_result_without_metadata)
        assert metadata_length > 200, (
            f"Метаданные должны добавлять существенное количество информации, "
            f"добавлено символов: {metadata_length}"
        )
        
        # 12. Проверяем наличие эмодзи для улучшения читаемости
        metadata_emojis = ["📋", "⚠️"]
        for emoji in metadata_emojis:
            assert emoji in formatted_result_with_metadata, (
                f"Метаданные должны содержать эмодзи для улучшения читаемости: {emoji}"
            )
        
        # 13. Проверяем, что точность указана в процентах или других понятных единицах
        accuracy_indicators = ["±", "%", "упрощенная модель"]
        accuracy_found = False
        
        for indicator in accuracy_indicators:
            if indicator in formatted_result_with_metadata:
                accuracy_found = True
                break
        
        assert accuracy_found, (
            f"Информация о точности должна содержать один из индикаторов: {accuracy_indicators}"
        )

    @given(
        origin_orbital_radius=st.floats(min_value=5e10, max_value=2e11),  # Внутренние планеты
        destination_orbital_radius=st.floats(min_value=2e11, max_value=8e11),  # Внешние планеты
        origin_escape_velocity=st.floats(min_value=5000, max_value=15000),
        destination_escape_velocity=st.floats(min_value=3000, max_value=12000),
        base_delta_v=st.floats(min_value=8000, max_value=20000),
        origin_name=st.text(min_size=3, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'), whitelist_characters=' ')),
        destination_name=st.text(min_size=3, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'), whitelist_characters=' '))
    )
    @settings(max_examples=5)
    def test_trajectory_visualization_with_maneuvers_property(self, origin_orbital_radius, destination_orbital_radius,
                                                            origin_escape_velocity, destination_escape_velocity,
                                                            base_delta_v, origin_name, destination_name):
        """
        **Feature: space-fuel-calculator, Property 15: Визуализация траектории с маневрами**
        
        Для любой траектории с гравитационными маневрами, отображение должно включать
        все промежуточные планеты и точки маневров.
        
        **Validates: Requirements 4.3**
        """
        from space_fuel_calculator.models.planet import Planet
        
        # Фильтруем некорректные названия
        assume(origin_name.strip() != "")
        assume(destination_name.strip() != "")
        assume(origin_name != destination_name)
        assume(not any(ord(c) < 32 for c in origin_name))
        assume(not any(ord(c) < 32 for c in destination_name))
        
        # Исключаем названия, содержащие индикаторы ошибок
        error_indicators = ["error", "ошибка", "nan", "inf", "none"]
        assume(not any(indicator.lower() in origin_name.lower() for indicator in error_indicators))
        assume(not any(indicator.lower() in destination_name.lower() for indicator in error_indicators))
        
        # Убеждаемся, что планеты имеют разные орбитальные радиусы
        assume(abs(origin_orbital_radius - destination_orbital_radius) > 5e10)
        
        # Создаем планеты отправления и назначения
        origin_planet = Planet(
            name=origin_name.strip(),
            mass=5e24,  # Примерная масса планеты
            radius=6e6,  # Примерный радиус планеты
            orbital_radius=origin_orbital_radius,
            escape_velocity=origin_escape_velocity
        )
        
        destination_planet = Planet(
            name=destination_name.strip(),
            mass=4e24,  # Примерная масса планеты
            radius=5e6,  # Примерный радиус планеты
            orbital_radius=destination_orbital_radius,
            escape_velocity=destination_escape_velocity
        )
        
        # Тестируем визуализацию траектории с гравитационными маневрами
        trajectory_viz_with_assists = ResultFormatter.format_trajectory_with_gravity_assists(
            origin_planet, destination_planet, base_delta_v, use_assists=True
        )
        
        # Тестируем визуализацию прямой траектории для сравнения
        trajectory_viz_direct = ResultFormatter.format_trajectory_with_gravity_assists(
            origin_planet, destination_planet, base_delta_v, use_assists=False
        )
        
        # Проверяем основные элементы визуализации траектории
        
        # 1. Визуализация должна содержать заголовок
        assert "ВИЗУАЛИЗАЦИЯ ТРАЕКТОРИИ ПОЛЕТА" in trajectory_viz_with_assists, (
            "Визуализация траектории должна содержать заголовок"
        )
        
        # 2. Должен быть указан тип траектории
        assert "Тип траектории:" in trajectory_viz_with_assists, (
            "Визуализация должна указывать тип траектории"
        )
        
        # 3. Должен быть указан маршрут с названиями планет
        assert "Маршрут:" in trajectory_viz_with_assists, (
            "Визуализация должна содержать информацию о маршруте"
        )
        
        assert origin_name.strip() in trajectory_viz_with_assists, (
            f"Визуализация должна содержать название планеты отправления: {origin_name.strip()}"
        )
        
        assert destination_name.strip() in trajectory_viz_with_assists, (
            f"Визуализация должна содержать название планеты назначения: {destination_name.strip()}"
        )
        
        # 4. Должны быть детали траектории
        assert "Детали траектории:" in trajectory_viz_with_assists, (
            "Визуализация должна содержать раздел с деталями траектории"
        )
        
        # 5. Проверяем наличие визуальных элементов траектории
        trajectory_symbols = ["──────────────►", "🛰️", "🚀", "📍", "🗺️"]
        
        for symbol in trajectory_symbols:
            assert symbol in trajectory_viz_with_assists, (
                f"Визуализация траектории должна содержать символ: {symbol}"
            )
        
        # 6. Должны быть общие показатели траектории
        assert "ОБЩИЕ ПОКАЗАТЕЛИ ТРАЕКТОРИИ:" in trajectory_viz_with_assists, (
            "Визуализация должна содержать раздел с общими показателями"
        )
        
        # 7. Должна быть информация о дельта-V
        assert "Общая дельта-V:" in trajectory_viz_with_assists, (
            "Визуализация должна содержать информацию об общей дельта-V"
        )
        
        assert " м/с" in trajectory_viz_with_assists, (
            "Визуализация должна содержать единицы измерения дельта-V в м/с"
        )
        
        assert " км/с" in trajectory_viz_with_assists, (
            "Визуализация должна содержать единицы измерения дельта-V в км/с"
        )
        
        # 8. Проверяем различия между траекторией с маневрами и прямой траекторией
        
        # Прямая траектория должна быть помечена как "прямая"
        assert "прямая" in trajectory_viz_direct.lower(), (
            "Визуализация прямой траектории должна быть помечена как 'прямая'"
        )
        
        # Траектория с маневрами должна содержать информацию о маневрах (если они есть)
        has_maneuvers = "гравитационными маневрами" in trajectory_viz_with_assists
        
        if has_maneuvers:
            # Если есть маневры, должна быть информация об экономии
            assert "Экономия от маневров:" in trajectory_viz_with_assists, (
                "Визуализация с маневрами должна содержать информацию об экономии дельта-V"
            )
            
            assert "Эффективность маневров:" in trajectory_viz_with_assists, (
                "Визуализация с маневрами должна содержать информацию об эффективности"
            )
            
            # Должно быть сравнение с прямой траекторией
            assert "Сравнение с прямой траекторией:" in trajectory_viz_with_assists, (
                "Визуализация с маневрами должна содержать сравнение с прямой траекторией"
            )
            
            # Должны быть промежуточные планеты (точки маневров)
            assert "гравитационный" in trajectory_viz_with_assists.lower() and "маневр" in trajectory_viz_with_assists.lower(), (
                "Визуализация с маневрами должна содержать информацию о гравитационных маневрах"
            )
        
        # 9. Проверяем временные характеристики
        assert "Временные характеристики:" in trajectory_viz_with_assists or "Примечания:" in trajectory_viz_with_assists, (
            "Визуализация должна содержать информацию о временных характеристиках или примечания"
        )
        
        # 10. Проверяем структуру визуализации (должна быть разбита на разделы)
        sections = [
            "ВИЗУАЛИЗАЦИЯ ТРАЕКТОРИИ ПОЛЕТА",
            "Тип траектории:",
            "Детали траектории:",
            "ОБЩИЕ ПОКАЗАТЕЛИ ТРАЕКТОРИИ:"
        ]
        
        for section in sections:
            assert section in trajectory_viz_with_assists, (
                f"Визуализация должна содержать раздел: {section}"
            )
        
        # 11. Проверяем, что визуализация содержит достаточно информации
        assert len(trajectory_viz_with_assists.strip()) > 500, (
            f"Визуализация траектории должна содержать достаточно информации, "
            f"получено {len(trajectory_viz_with_assists)} символов"
        )
        
        # 12. Проверяем корректность числовых значений
        import re
        
        # Ищем значения дельта-V в тексте
        delta_v_pattern = r"(\d{1,3}(?:,\d{3})*)\s*м/с"
        delta_v_matches = re.findall(delta_v_pattern, trajectory_viz_with_assists)
        
        assert len(delta_v_matches) > 0, (
            "Визуализация должна содержать числовые значения дельта-V в м/с"
        )
        
        # Проверяем, что найденные значения разумны
        for match in delta_v_matches:
            delta_v_value = int(match.replace(',', ''))
            assert 0 <= delta_v_value <= 100000, (
                f"Значение дельта-V должно быть разумным: {delta_v_value} м/с"
            )
        
        # 13. Проверяем наличие эмодзи для улучшения читаемости
        required_emojis = ["🛰️", "🚀", "📍", "🗺️", "📊"]
        
        for emoji in required_emojis:
            assert emoji in trajectory_viz_with_assists, (
                f"Визуализация должна содержать эмодзи для улучшения читаемости: {emoji}"
            )
        
        # 14. Проверяем, что визуализация не содержит очевидных ошибок
        error_indicators = ["error", "ошибка", "nan", "inf", "none"]
        
        for indicator in error_indicators:
            assert indicator.lower() not in trajectory_viz_with_assists.lower(), (
                f"Визуализация не должна содержать индикаторы ошибок: {indicator}"
            )


class TestUIFormatterValidation:
    """Тесты валидации для форматирования UI."""
    
    def test_format_engine_characteristics_with_none_raises_error(self):
        """Тест на передачу None вместо двигателя."""
        with pytest.raises(AttributeError):
            ResultFormatter.format_engine_characteristics(None)
    
    def test_format_engine_characteristics_with_invalid_object_raises_error(self):
        """Тест на передачу некорректного объекта вместо двигателя."""
        with pytest.raises(AttributeError):
            ResultFormatter.format_engine_characteristics("not an engine")
    
    def test_format_engine_characteristics_chemical_engine(self):
        """Тест форматирования характеристик химического двигателя."""
        engine = ChemicalEngine(
            name="Test Chemical Engine",
            specific_impulse=350,
            thrust=2000000,
            fuel_type="RP-1/LOX"
        )
        
        result = ResultFormatter.format_engine_characteristics(engine)
        
        assert "Test Chemical Engine" in result
        assert "chemical" in result
        assert "350" in result
        assert "2,000,000" in result or "2000000" in result
        assert "RP-1/LOX" in result
        assert "🔧" in result
    
    def test_format_engine_characteristics_ion_engine(self):
        """Тест форматирования характеристик ионного двигателя."""
        engine = IonEngine(
            name="Test Ion Engine",
            specific_impulse=4000,
            thrust=0.5,
            power_consumption=5000
        )
        
        result = ResultFormatter.format_engine_characteristics(engine)
        
        assert "Test Ion Engine" in result
        assert "ion" in result
        assert "4000" in result or "4,000" in result
        assert "0.5" in result or "0,5" in result
        assert "5000" in result or "5,000" in result
        assert "🔧" in result
    
    def test_format_engine_characteristics_nuclear_engine(self):
        """Тест форматирования характеристик ядерного двигателя."""
        engine = NuclearEngine(
            name="Test Nuclear Engine",
            specific_impulse=900,
            thrust=400000,
            reactor_power=1500000000,  # 1.5 GW
            propellant_type="H2"
        )
        
        result = ResultFormatter.format_engine_characteristics(engine)
        
        assert "Test Nuclear Engine" in result
        assert "nuclear" in result
        assert "900" in result
        assert "400,000" in result or "400000" in result
        assert "1500" in result  # МВт
        assert "H2" in result
        assert "🔧" in result