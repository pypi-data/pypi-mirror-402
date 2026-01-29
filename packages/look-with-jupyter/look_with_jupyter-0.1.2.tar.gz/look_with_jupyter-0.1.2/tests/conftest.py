"""Конфигурация pytest для LookWithJupyter."""

import pandas as pd
import polars as pl
import pytest


@pytest.fixture
def sample_pandas_df():
    """Создает пример DataFrame для pandas."""
    return pd.DataFrame(
        {
            "name": [
                "Alice",
                "Bob",
                "Charlie",
                "David",
                "Eve",
                "Frank",
                "Grace",
                "Henry",
                "Iris",
                "Jack",
                "Kate",
                "Liam",
            ],
            "age": [25, 30, 35, 28, 32, 27, 29, 31, 26, 33, 28, 30],
            "salary": [
                50000,
                60000,
                75000,
                55000,
                70000,
                52000,
                58000,
                65000,
                51000,
                72000,
                56000,
                62000,
            ],
            "city": [
                "New York",
                "London",
                "Paris",
                "Berlin",
                "Tokyo",
                "Sydney",
                "Toronto",
                "Mumbai",
                "Moscow",
                "Dubai",
                "Singapore",
                "Bangkok",
            ],
        }
    )


@pytest.fixture
def sample_polars_df():
    """Создает пример DataFrame для polars."""
    return pl.DataFrame(
        {
            "name": [
                "Alice",
                "Bob",
                "Charlie",
                "David",
                "Eve",
                "Frank",
                "Grace",
                "Henry",
                "Iris",
                "Jack",
                "Kate",
                "Liam",
            ],
            "age": [25, 30, 35, 28, 32, 27, 29, 31, 26, 33, 28, 30],
            "salary": [
                50000,
                60000,
                75000,
                55000,
                70000,
                52000,
                58000,
                65000,
                51000,
                72000,
                56000,
                62000,
            ],
            "city": [
                "New York",
                "London",
                "Paris",
                "Berlin",
                "Tokyo",
                "Sydney",
                "Toronto",
                "Mumbai",
                "Moscow",
                "Dubai",
                "Singapore",
                "Bangkok",
            ],
        }
    )


@pytest.fixture
def small_pandas_df():
    """Создает маленький DataFrame для pandas."""
    return pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6], "C": [7, 8, 9]})


@pytest.fixture
def small_polars_df():
    """Создает маленький DataFrame для polars."""
    return pl.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6], "C": [7, 8, 9]})
