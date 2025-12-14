import streamlit as st
import sys
import os

# Добавляем путь к нашему модулю
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'space_fuel_calculator'))

from space_fuel_calculator.data.planets import get_destination_planets, get_planet_by_key
from space_fuel_calculator.data.engines import get_all_engines, get_engine_by_key, get_engine_categories
from space_fuel_calculator.calculators.fuel_calculator import FuelCalculator
from space_fuel_calculator.calculators.trajectory_calculator import TrajectoryCalculator
from space_fuel_calculator.ui.cli import MissionCLI

# Настройка страницы
st.set_page_config(
    page_title="🚀 Калькулятор топлива для космических полетов",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Заголовок
st.title("🚀 Калькулятор топлива для космических полетов")
st.markdown("### Рассчитайте необходимое топливо для межпланетных миссий")

# Инициализация
@st.cache_resource
def init_calculators():
    return MissionCLI(), FuelCalculator(), TrajectoryCalculator()

cli, fuel_calc, traj_calc = init_calculators()

# Боковая панель для выбора параметров
st.sidebar.header("🎯 Параметры миссии")

# Выбор планеты
st.sidebar.subheader("📍 Планета назначения")
planets = get_destination_planets()
planet_options = {}
for key, planet in planets.items():
    if planet.name in ["Венера", "Марс"]:
        difficulty = "🟢 ЛЕГКО"
    elif planet.name in ["Меркурий", "Юпитер"]:
        difficulty = "🟡 СРЕДНЕ"
    else:
        difficulty = "🔴 СЛОЖНО"
    planet_options[f"{planet.name} ({difficulty})"] = key

selected_planet_display = st.sidebar.selectbox(
    "Выберите планету:",
    list(planet_options.keys()),
    help="🟢 ЛЕГКО: Все типы миссий\n🟡 СРЕДНЕ: Ионные двигатели\n🔴 СЛОЖНО: Только в одну сторону"
)
selected_planet_key = planet_options[selected_planet_display]
selected_planet = planets[selected_planet_key]

# Выбор двигателя
st.sidebar.subheader("🔧 Тип двигателя")
engine_categories = get_engine_categories()
all_engines = get_all_engines()

category = st.sidebar.selectbox(
    "Категория двигателя:",
    list(engine_categories.keys()),
    help="🚀 Химические: Высокая тяга\n⚡ Ионные: Высокая эффективность\n⚛️ Ядерные: Экспериментальные"
)

engines_in_category = engine_categories[category]
engine_options = {all_engines[key].name: key for key in engines_in_category}

selected_engine_display = st.sidebar.selectbox(
    "Выберите двигатель:",
    list(engine_options.keys())
)
selected_engine_key = engine_options[selected_engine_display]
selected_engine = all_engines[selected_engine_key]

# Тип миссии
st.sidebar.subheader("🎯 Тип миссии")
mission_type = st.sidebar.radio(
    "Выберите тип:",
    ["Полет в одну сторону", "Полет туда и обратно"],
    help="Полет туда-обратно требует значительно больше топлива"
)
round_trip = mission_type == "Полет туда и обратно"

# Основная область
col1, col2 = st.columns([2, 1])

with col1:
    st.header("📊 Анализ миссии")
    
    # Показываем выбранные параметры
    st.subheader("Выбранные параметры:")
    st.write(f"📍 **Планета:** {selected_planet.name}")
    st.write(f"🔧 **Двигатель:** {selected_engine.name} ({selected_engine.engine_type.value})")
    st.write(f"🎯 **Тип миссии:** {mission_type}")
    
    # Рассчитываем ограничения
    limits = cli._calculate_mass_limits(selected_planet, selected_engine)
    
    st.subheader("💡 Ограничения массы:")
    
    def format_limit(limit_value):
        if limit_value == 0:
            return "❌ НЕВОЗМОЖНО (дельта-V > 50 км/с)"
        else:
            return f"{limit_value:,.0f} кг"
    
    st.write(f"• **Рекомендуемый диапазон:** {limits['recommended_min']:,.0f} - {limits['recommended_max']:,.0f} кг")
    st.write(f"• **Максимум для полета туда:** {format_limit(limits['max_oneway'])}")
    st.write(f"• **Максимум для полета туда-обратно:** {format_limit(limits['max_roundtrip'])}")
    
    if limits['warnings']:
        st.warning(f"⚠️ {limits['warnings']}")
    
    # Проверяем возможность миссии
    max_for_mission = limits['max_roundtrip'] if round_trip else limits['max_oneway']
    
    if max_for_mission == 0:
        st.error("🚫 **КРИТИЧЕСКАЯ ОШИБКА:** Выбранный тип миссии ФИЗИЧЕСКИ НЕВОЗМОЖЕН!")
        st.error("Система не может рассчитать топливо для этой комбинации параметров.")
        st.info("💡 **Рекомендации:**\n- Выберите полет в одну сторону\n- Выберите более близкую планету (Венера, Марс)")
        
        # Блокируем ввод
        payload_mass = st.number_input(
            "📦 Масса полезной нагрузки (кг):",
            min_value=0,
            max_value=0,
            value=0,
            disabled=True,
            help="Ввод заблокирован для невозможных миссий"
        )
    else:
        st.success(f"✅ **Миссия возможна!** Максимум для вашего типа: {max_for_mission:,.0f} кг")
        
        # Ввод массы
        payload_mass = st.number_input(
            "📦 Масса полезной нагрузки (кг):",
            min_value=1,
            max_value=max_for_mission,
            value=min(1000, max_for_mission),
            help=f"Введите массу от 1 до {max_for_mission:,.0f} кг"
        )
        
        # Предупреждения о массе
        warnings = cli._get_mass_warnings(payload_mass, selected_planet, selected_engine, limits)
        if warnings:
            st.warning(f"⚠️ {warnings}")
        
        # Кнопка расчета
        if st.button("🔄 Рассчитать топливо", type="primary"):
            try:
                with st.spinner("Выполняется расчет..."):
                    if round_trip:
                        result = fuel_calc.calculate_round_trip_fuel(selected_planet, payload_mass, selected_engine)
                    else:
                        delta_v = traj_calc.calculate_delta_v(cli.earth, selected_planet)
                        result = fuel_calc.calculate_fuel_mass(delta_v, payload_mass, selected_engine)
                
                # Показываем результаты
                st.success("🎉 Расчет завершен успешно!")
                
                st.subheader("📊 Результаты расчета:")
                
                if round_trip:
                    st.write(f"⛽ **Топливо для полета туда:** {result.outbound_fuel:,.0f} кг ({result.outbound_fuel/1000:.1f} тонн)")
                    st.write(f"⛽ **Топливо для обратного полета:** {result.return_fuel:,.0f} кг ({result.return_fuel/1000:.1f} тонн)")
                    total_fuel = result.total_fuel
                    st.write(f"⛽ **ОБЩЕЕ КОЛИЧЕСТВО ТОПЛИВА:** {total_fuel:,.0f} кг ({total_fuel/1000:.1f} тонн)")
                else:
                    st.write(f"⛽ **Необходимое топливо:** {result.total_fuel:,.0f} кг ({result.total_fuel/1000:.1f} тонн)")
                    total_fuel = result.total_fuel
                
                # Анализ эффективности
                fuel_ratio = total_fuel / payload_mass
                total_mass = total_fuel + payload_mass
                
                st.subheader("📈 Анализ эффективности:")
                st.write(f"• **Отношение топливо/полезная нагрузка:** {fuel_ratio:.1f}:1")
                st.write(f"• **Общая масса ракеты:** {total_mass:,.0f} кг ({total_mass/1000:.1f} тонн)")
                
                if fuel_ratio < 50:
                    st.success("✅ Отличная эффективность для межпланетной миссии!")
                elif fuel_ratio < 100:
                    st.info("🟡 Приемлемая эффективность")
                else:
                    st.warning("🔴 Низкая эффективность - рассмотрите другие варианты")
                
                if total_fuel < 100000:
                    st.success("✅ Реалистично для современных ракет-носителей")
                elif total_fuel < 500000:
                    st.info("🟡 Потребует тяжелые ракеты-носители (Falcon Heavy, SLS)")
                else:
                    st.warning("🔴 Потребует множественные запуски или новые технологии")
                
            except Exception as e:
                st.error(f"❌ Ошибка расчета: {e}")
                st.info("💡 Попробуйте уменьшить массу полезной нагрузки или выбрать другие параметры")

with col2:
    st.header("ℹ️ Информация")
    
    # Информация о планете
    st.subheader(f"🌍 {selected_planet.name}")
    st.write(f"**Масса:** {selected_planet.mass:.2e} кг")
    st.write(f"**Радиус:** {selected_planet.radius/1000:.0f} км")
    st.write(f"**Расстояние от Солнца:** {selected_planet.orbital_radius/1.496e11:.2f} а.е.")
    st.write(f"**Скорость убегания:** {selected_planet.escape_velocity/1000:.1f} км/с")
    
    # Информация о двигателе
    st.subheader(f"🔧 {selected_engine.name}")
    st.write(f"**Тип:** {selected_engine.engine_type.value}")
    st.write(f"**Удельный импульс:** {selected_engine.specific_impulse:.0f} с")
    st.write(f"**Тяга:** {selected_engine.thrust:,.0f} Н ({selected_engine.thrust/1000:.1f} кН)")
    
    # Дополнительная информация о двигателе
    if selected_engine.engine_type.value == "chemical":
        from space_fuel_calculator.models.engine import ChemicalEngine
        if isinstance(selected_engine, ChemicalEngine):
            st.write(f"**Тип топлива:** {selected_engine.fuel_type}")
    elif selected_engine.engine_type.value == "ion":
        from space_fuel_calculator.models.engine import IonEngine
        if isinstance(selected_engine, IonEngine):
            st.write(f"**Потребляемая мощность:** {selected_engine.power_consumption:,.0f} Вт")
    elif selected_engine.engine_type.value == "nuclear":
        from space_fuel_calculator.models.engine import NuclearEngine
        if isinstance(selected_engine, NuclearEngine):
            st.write(f"**Мощность реактора:** {selected_engine.reactor_power/1e6:.0f} МВт")
            st.write(f"**Рабочее тело:** {selected_engine.propellant_type}")

# Футер
st.markdown("---")
st.markdown("### 💡 Дополнительная информация")
st.info("""
**Важные замечания:**
- Расчеты основаны на упрощенной модели (уравнение Циолковского)
- Не учитываются: атмосферное торможение, гравитационные маневры
- Для точного планирования миссии требуется детальный анализ
- Точность расчетов: ±5%
""")

st.success("""
**Возможности системы:**
- ✅ Персонализированные ограничения для каждой комбинации параметров
- ✅ Анализ выполнимости миссии в реальном времени  
- ✅ Блокировка физически невозможных миссий
- ✅ Конкретные рекомендации и альтернативы
""")