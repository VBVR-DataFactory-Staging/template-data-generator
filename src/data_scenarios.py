"""Realistic chart scenarios used by the default G-29 task."""

import random
from dataclasses import dataclass
from typing import List, Optional, Tuple


@dataclass
class ChartMetadata:
    title: str
    x_label: str
    y_label: str
    x_unit: str = ""
    y_unit: str = ""
    data_labels: Optional[List[str]] = None


@dataclass
class DataScenario:
    name: str
    chart_type: str
    metadata: ChartMetadata
    min_value: float
    max_value: float
    data_range: Tuple[int, int]


SCENARIOS = {
    "monthly_sales": DataScenario(
        name="Monthly Sales",
        chart_type="bar",
        metadata=ChartMetadata(
            title="Monthly Product Sales Statistics 2024",
            x_label="Month",
            y_label="Sales",
            y_unit="units",
            data_labels=["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
        ),
        min_value=1000,
        max_value=50000,
        data_range=(3, 5),
    ),
    "website_visits": DataScenario(
        name="Website Visits",
        chart_type="bar",
        metadata=ChartMetadata(
            title="Weekly Website Visit Statistics",
            x_label="Day of Week",
            y_label="Visits",
            y_unit="visits",
            data_labels=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
        ),
        min_value=5000,
        max_value=30000,
        data_range=(3, 5),
    ),
    "temperature": DataScenario(
        name="Temperature",
        chart_type="line",
        metadata=ChartMetadata(
            title="Monthly Average Temperature in Beijing 2024",
            x_label="Month",
            y_label="Average Temperature",
            y_unit="C",
            data_labels=["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
        ),
        min_value=-10,
        max_value=35,
        data_range=(3, 5),
    ),
    "stock_price": DataScenario(
        name="Stock Price",
        chart_type="line",
        metadata=ChartMetadata(
            title="Stock Closing Price Trend",
            x_label="Day",
            y_label="Closing Price",
            y_unit="USD",
        ),
        min_value=45,
        max_value=65,
        data_range=(3, 5),
    ),
    "student_grades": DataScenario(
        name="Student Grades",
        chart_type="scatter",
        metadata=ChartMetadata(
            title="Correlation Analysis: Math vs Physics Scores",
            x_label="Math Score",
            y_label="Physics Score",
            x_unit="points",
            y_unit="points",
        ),
        min_value=60,
        max_value=100,
        data_range=(4, 5),
    ),
    "sales_share": DataScenario(
        name="Sales Share",
        chart_type="pie",
        metadata=ChartMetadata(
            title="Product Category Sales Share 2024",
            x_label="",
            y_label="",
            data_labels=["Electronics", "Clothing", "Food", "Books", "Daily Goods"],
        ),
        min_value=15,
        max_value=40,
        data_range=(4, 5),
    ),
}


def get_scenario_for_chart_type(chart_type: str) -> DataScenario:
    """Return a random scenario compatible with the requested chart type."""

    matches = [scenario for scenario in SCENARIOS.values() if scenario.chart_type == chart_type]
    return random.choice(matches)


def generate_realistic_data(scenario: DataScenario) -> Tuple[List[float], List[float]]:
    """Generate small, readable chart values for a given scenario."""

    num_points = random.randint(*scenario.data_range)
    value_range = scenario.max_value - scenario.min_value

    if scenario.chart_type == "pie":
        raw_values = [random.uniform(scenario.min_value, scenario.max_value) for _ in range(num_points)]
        total = sum(raw_values)
        values = [round(v / total * 100.0, 1) for v in raw_values]
        return values, list(range(num_points))

    if scenario.chart_type == "scatter":
        x_values = []
        y_values = []
        span = value_range * random.uniform(0.55, 0.8)
        x_center = random.uniform(scenario.min_value + span / 2, scenario.max_value - span / 2)
        y_center = random.uniform(scenario.min_value + span / 2, scenario.max_value - span / 2)
        correlation = random.uniform(0.4, 0.8)

        for index in range(num_points):
            ratio = 0.5 if num_points == 1 else index / float(num_points - 1)
            x_val = x_center - span / 2 + span * ratio + random.uniform(-span * 0.04, span * 0.04)
            x_val = max(scenario.min_value, min(scenario.max_value, x_val))
            normalized = (x_val - x_center) / max(span / 2, 1.0)
            y_val = y_center + correlation * normalized * (span / 2)
            y_val += random.uniform(-span * 0.12, span * 0.12)
            y_val = max(scenario.min_value, min(scenario.max_value, y_val))
            x_values.append(round(x_val, 1))
            y_values.append(round(y_val, 1))

        return y_values, x_values

    if scenario.chart_type == "line":
        values = []
        x_values = list(range(1, num_points + 1))
        start_value = random.uniform(
            scenario.min_value + value_range * 0.2,
            scenario.max_value - value_range * 0.2,
        )
        trend = random.choice([-1, 1]) * value_range * random.uniform(0.05, 0.14) / max(num_points - 1, 1)

        for index in range(num_points):
            noise = random.uniform(-value_range * 0.05, value_range * 0.05)
            value = start_value + trend * index + noise
            value = max(scenario.min_value, min(scenario.max_value, value))
            values.append(round(value, 1))

        return values, x_values

    values = [round(random.uniform(scenario.min_value, scenario.max_value), 0) for _ in range(num_points)]
    return values, list(range(1, num_points + 1))
