"""
Автоматический калькулятор цен для электромонтажных работ
Адаптировано из electro_calc проекта
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class ServiceCategory(str, Enum):
    """Категории услуг"""
    ELECTRICAL = "electrical"  # Электромонтажные работы
    PLUMBING = "plumbing"      # Сантехника
    APPLIANCE = "appliance"    # Бытовая техника
    GENERAL = "general"        # Общие работы
    HVAC = "hvac"             # Кондиционеры, вентиляция
    EMERGENCY = "emergency"    # Срочный вызов


class Urgency(str, Enum):
    """Срочность заказа"""
    NORMAL = "normal"          # Обычный (1-2 дня)
    URGENT = "urgent"          # Срочный (сегодня)
    EMERGENCY = "emergency"    # Экстренный (в течение часа)


class TimeOfDay(str, Enum):
    """Время суток"""
    MORNING = "morning"        # 08:00 - 12:00
    DAY = "day"               # 12:00 - 18:00
    EVENING = "evening"       # 18:00 - 22:00
    NIGHT = "night"           # 22:00 - 08:00


class District(str, Enum):
    """Районы Калининграда"""
    CENTER = "center"          # Центр
    LENINGRADSKY = "leningradsky"  # Ленинградский
    MOSKOVSKУ = "moskovsky"    # Московский
    OKTYABRSKY = "oktyabrsky"  # Октябрьский
    BALTIKA = "baltika"        # Балтика
    SVETLOGORSK = "svetlogorsk"  # Светлогорск (пригород)


@dataclass
class PriceFactors:
    """Факторы влияющие на цену"""
    category: ServiceCategory
    urgency: Urgency = Urgency.NORMAL
    time_of_day: TimeOfDay = TimeOfDay.DAY
    district: District = District.CENTER
    
    # Характеристики работы
    description: str = ""
    estimated_hours: float = 1.0
    complexity: int = 1  # 1-5 (простая-сложная)
    
    # Дополнительные факторы
    materials_needed: bool = False
    high_voltage: bool = False  # 380V вместо 220V
    height_work: bool = False   # Работа на высоте
    outdoors: bool = False      # Уличные работы
    
    # Количество точек
    outlets: int = 0
    switches: int = 0
    chandeliers: int = 0
    
    # Расстояние
    distance_km: float = 0.0


# Базовые цены по категориям (₽)
BASE_PRICES = {
    ServiceCategory.ELECTRICAL: {
        "base": 1500,
        "outlet_install": 350,
        "outlet_wiring": 850,
        "switch_install": 300,
        "switch_wiring": 1500,
        "chandelier": 1000,
        "panel_work": 3000,
    },
    ServiceCategory.PLUMBING: {
        "base": 1800,
        "faucet": 800,
        "sink": 1500,
        "toilet": 2000,
        "pipe_repair": 1200,
    },
    ServiceCategory.APPLIANCE: {
        "base": 2000,
        "washing_machine": 1500,
        "dishwasher": 1800,
        "refrigerator": 2500,
        "oven": 2200,
    },
    ServiceCategory.GENERAL: {
        "base": 1200,
        "repair": 800,
        "installation": 1000,
    },
    ServiceCategory.HVAC: {
        "base": 3000,
        "ac_install": 4000,
        "ac_service": 2000,
        "ventilation": 3500,
    },
    ServiceCategory.EMERGENCY: {
        "base": 2500,
    }
}

# Коэффициенты срочности
URGENCY_MULTIPLIERS = {
    Urgency.NORMAL: 1.0,
    Urgency.URGENT: 1.5,      # +50%
    Urgency.EMERGENCY: 2.0,   # +100%
}

# Коэффициенты времени суток
TIME_MULTIPLIERS = {
    TimeOfDay.MORNING: 1.0,
    TimeOfDay.DAY: 1.0,
    TimeOfDay.EVENING: 1.2,   # +20%
    TimeOfDay.NIGHT: 1.5,     # +50%
}

# Коэффициенты районов (расстояние от центра)
DISTRICT_MULTIPLIERS = {
    District.CENTER: 1.0,
    District.LENINGRADSKY: 1.05,
    District.MOSKOVSKУ: 1.05,
    District.OKTYABRSKY: 1.05,
    District.BALTIKA: 1.1,
    District.SVETLOGORSK: 1.2,  # Пригород
}

# Скидки за объём
VOLUME_DISCOUNTS = [
    (21, 0.20),  # 21+ точек: -20%
    (11, 0.15),  # 11-20 точек: -15%
    (6, 0.10),   # 6-10 точек: -10%
    (3, 0.05),   # 3-5 точек: -5%
]


class PriceCalculator:
    """Калькулятор цен на услуги"""
    
    def __init__(self):
        self.base_prices = BASE_PRICES
    
    def calculate(self, factors: PriceFactors) -> Dict:
        """
        Рассчитать финальную цену
        
        Returns:
            dict: {
                'base_price': float,
                'total_price': float,
                'breakdown': dict,
                'discount': float,
                'multipliers': dict
            }
        """
        # Базовая цена
        base_price = self._get_base_price(factors)
        
        # Расчёт цены за точки
        points_price = self._calculate_points_price(factors)
        
        # Сумма перед коэффициентами
        subtotal = base_price + points_price
        
        # Применить коэффициенты
        multipliers = self._calculate_multipliers(factors)
        price_with_multipliers = subtotal
        
        for name, mult in multipliers.items():
            price_with_multipliers *= mult
        
        # Применить скидку за объём
        total_points = factors.outlets + factors.switches + factors.chandeliers
        discount_percent = self._get_volume_discount(total_points)
        discount_amount = price_with_multipliers * discount_percent
        
        # Финальная цена
        final_price = price_with_multipliers - discount_amount
        
        # Округление
        final_price = round(final_price, -1)  # До десятков
        
        return {
            'base_price': round(base_price, 2),
            'points_price': round(points_price, 2),
            'subtotal': round(subtotal, 2),
            'total_price': round(final_price, 2),
            'discount': {
                'percent': discount_percent * 100,
                'amount': round(discount_amount, 2)
            },
            'multipliers': {k: round(v, 2) for k, v in multipliers.items()},
            'breakdown': self._get_breakdown(factors, base_price, points_price)
        }
    
    def _get_base_price(self, factors: PriceFactors) -> float:
        """Получить базовую цену"""
        category_prices = self.base_prices.get(factors.category, {})
        base = category_prices.get('base', 1500)
        
        # Учёт сложности
        if factors.complexity > 1:
            base *= (1 + (factors.complexity - 1) * 0.2)  # +20% за каждый уровень
        
        # Учёт времени работы
        if factors.estimated_hours > 1:
            base += (factors.estimated_hours - 1) * 800  # +800₽ за каждый час
        
        # Дополнительные факторы
        if factors.materials_needed:
            base *= 1.15  # +15% если нужны материалы
        
        if factors.high_voltage:
            base *= 1.3  # +30% для работы с 380V
        
        if factors.height_work:
            base *= 1.25  # +25% за работу на высоте
        
        if factors.outdoors:
            base *= 1.2  # +20% за уличные работы
        
        return base
    
    def _calculate_points_price(self, factors: PriceFactors) -> float:
        """Рассчитать цену за точки (розетки, выключатели, люстры)"""
        if factors.category != ServiceCategory.ELECTRICAL:
            return 0
        
        prices = self.base_prices[ServiceCategory.ELECTRICAL]
        total = 0
        
        # Розетки
        if factors.outlets > 0:
            outlet_price = prices['outlet_install']
            if factors.materials_needed:
                outlet_price += prices['outlet_wiring']
            total += outlet_price * factors.outlets
        
        # Выключатели
        if factors.switches > 0:
            switch_price = prices['switch_install']
            if factors.materials_needed:
                switch_price += prices['switch_wiring']
            total += switch_price * factors.switches
        
        # Люстры
        if factors.chandeliers > 0:
            total += prices['chandelier'] * factors.chandeliers
        
        return total
    
    def _calculate_multipliers(self, factors: PriceFactors) -> Dict[str, float]:
        """Рассчитать все коэффициенты"""
        multipliers = {}
        
        # Срочность
        urgency_mult = URGENCY_MULTIPLIERS[factors.urgency]
        if urgency_mult != 1.0:
            multipliers['urgency'] = urgency_mult
        
        # Время суток
        time_mult = TIME_MULTIPLIERS[factors.time_of_day]
        if time_mult != 1.0:
            multipliers['time_of_day'] = time_mult
        
        # Район
        district_mult = DISTRICT_MULTIPLIERS[factors.district]
        if district_mult != 1.0:
            multipliers['district'] = district_mult
        
        # Расстояние (дополнительно к району)
        if factors.distance_km > 10:
            km_mult = 1.0 + (factors.distance_km - 10) * 0.02  # +2% за каждый км после 10км
            multipliers['distance'] = km_mult
        
        return multipliers
    
    def _get_volume_discount(self, total_points: int) -> float:
        """Получить скидку за объём"""
        for min_points, discount in VOLUME_DISCOUNTS:
            if total_points >= min_points:
                return discount
        return 0.0
    
    def _get_breakdown(self, factors: PriceFactors, base: float, points: float) -> Dict:
        """Детальная разбивка цены"""
        breakdown = {
            'base_service': round(base, 2),
        }
        
        if points > 0:
            breakdown['installation_points'] = {
                'outlets': factors.outlets,
                'switches': factors.switches,
                'chandeliers': factors.chandeliers,
                'total_price': round(points, 2)
            }
        
        if factors.materials_needed:
            breakdown['materials_included'] = True
        
        return breakdown


# Готовые шаблоны для частых услуг
QUICK_TEMPLATES = {
    "outlet_single": PriceFactors(
        category=ServiceCategory.ELECTRICAL,
        description="Установка одной розетки",
        outlets=1,
        materials_needed=False,
    ),
    "outlet_block_3": PriceFactors(
        category=ServiceCategory.ELECTRICAL,
        description="Установка блока из 3 розеток",
        outlets=3,
        materials_needed=True,
    ),
    "chandelier": PriceFactors(
        category=ServiceCategory.ELECTRICAL,
        description="Установка люстры",
        chandeliers=1,
    ),
    "washing_machine": PriceFactors(
        category=ServiceCategory.APPLIANCE,
        description="Подключение стиральной машины",
        estimated_hours=1.5,
    ),
    "ac_install": PriceFactors(
        category=ServiceCategory.HVAC,
        description="Установка кондиционера",
        estimated_hours=3.0,
        complexity=3,
        height_work=True,
    ),
    "emergency_electrical": PriceFactors(
        category=ServiceCategory.EMERGENCY,
        description="Экстренный вызов электрика",
        urgency=Urgency.EMERGENCY,
    ),
}


def get_quick_price(template_name: str, **kwargs) -> Dict:
    """
    Быстрый расчёт по шаблону
    
    Args:
        template_name: Название шаблона
        **kwargs: Дополнительные параметры для переопределения
    
    Returns:
        dict: Результат расчёта цены
    """
    if template_name not in QUICK_TEMPLATES:
        raise ValueError(f"Неизвестный шаблон: {template_name}")
    
    template = QUICK_TEMPLATES[template_name]
    
    # Переопределить параметры если переданы
    for key, value in kwargs.items():
        if hasattr(template, key):
            setattr(template, key, value)
    
    calculator = PriceCalculator()
    return calculator.calculate(template)


def estimate_from_description(description: str, category: str = "electrical") -> Dict:
    """
    Автоматическая оценка цены по описанию проблемы
    
    Args:
        description: Текстовое описание проблемы
        category: Категория услуги
    
    Returns:
        dict: Результат расчёта цены
    """
    desc_lower = description.lower()
    
    # Определить категорию
    service_category = ServiceCategory.ELECTRICAL
    if category == "plumbing" or any(word in desc_lower for word in ["кран", "труба", "слив", "сантехника"]):
        service_category = ServiceCategory.PLUMBING
    elif category == "appliance" or any(word in desc_lower for word in ["стиральная", "холодильник", "техника"]):
        service_category = ServiceCategory.APPLIANCE
    elif category == "hvac" or any(word in desc_lower for word in ["кондиционер", "вентиляция"]):
        service_category = ServiceCategory.HVAC
    
    # Определить срочность
    urgency = Urgency.NORMAL
    if any(word in desc_lower for word in ["срочно", "сейчас", "экстренно", "горит"]):
        urgency = Urgency.EMERGENCY if "экстренно" in desc_lower or "горит" in desc_lower else Urgency.URGENT
    
    # Подсчитать точки
    outlets = desc_lower.count("розетк")
    switches = desc_lower.count("выключател")
    chandeliers = desc_lower.count("люстр")
    
    # Определить сложность
    complexity = 1
    if len(description) > 200:
        complexity = 3
    elif len(description) > 100:
        complexity = 2
    
    if any(word in desc_lower for word in ["щит", "автомат", "380", "трёхфазн"]):
        complexity = max(complexity, 4)
        high_voltage = True
    else:
        high_voltage = False
    
    # Оценить время
    estimated_hours = 1.0
    if outlets + switches > 5:
        estimated_hours = 2.0
    if complexity >= 3:
        estimated_hours += 1.0
    
    factors = PriceFactors(
        category=service_category,
        description=description,
        urgency=urgency,
        complexity=complexity,
        estimated_hours=estimated_hours,
        outlets=outlets,
        switches=switches,
        chandeliers=chandeliers,
        high_voltage=high_voltage,
        materials_needed=urgency == Urgency.NORMAL,  # Только для обычных заказов
    )
    
    calculator = PriceCalculator()
    return calculator.calculate(factors)


# Пример использования
if __name__ == "__main__":
    # Тест 1: Простая розетка
    print("=== ТЕСТ 1: Установка розетки ===")
    result = get_quick_price("outlet_single")
    print(f"Цена: {result['total_price']}₽")
    print(f"Разбивка: {result['breakdown']}")
    print()
    
    # Тест 2: Срочный вызов
    print("=== ТЕСТ 2: Срочный вызов электрика ===")
    result = get_quick_price("emergency_electrical", district=District.BALTIKA)
    print(f"Цена: {result['total_price']}₽")
    print(f"Коэффициенты: {result['multipliers']}")
    print()
    
    # Тест 3: По описанию
    print("=== ТЕСТ 3: Автоматическая оценка ===")
    desc = "Срочно нужно установить 3 розетки и 2 выключателя в новой квартире"
    result = estimate_from_description(desc)
    print(f"Описание: {desc}")
    print(f"Цена: {result['total_price']}₽")
    print(f"Детали: {result['breakdown']}")
