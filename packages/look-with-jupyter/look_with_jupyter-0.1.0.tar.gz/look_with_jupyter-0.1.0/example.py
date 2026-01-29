"""
Пример использования модуля LookWithJupyter.

Этот скрипт демонстрирует основную функциональность модуля.
"""

import pandas as pd
import polars as pl

from UtilForWhatching import DataOut


def example_pandas():
    """Пример использования с pandas DataFrame."""
    print("=" * 50)
    print("Пример с pandas DataFrame")
    print("=" * 50)

    # Создаем DataFrame
    df = pd.DataFrame(
        {
            "name": ["Alice", "Bob", "Charlie", "David", "Eve", "Frank"],
            "age": [25, 30, 35, 28, 32, 27],
            "salary": [50000, 60000, 75000, 55000, 70000, 52000],
            "city": ["New York", "London", "Paris", "Berlin", "Tokyo", "Sydney"],
        }
    )

    print(f"\nDataFrame shape: {df.shape}")
    print(f"Columns: {list(df.columns)}")

    # Создаем объект DataOut
    data_out = DataOut(df, id_start=0, line_range=(0, 3))
    print(f"\nID Start: {data_out.id_start}")
    print(f"Line Range: {data_out.line_range}")
    print(f"Columns: {data_out.columns}")


def example_polars():
    """Пример использования с polars DataFrame."""
    print("\n" + "=" * 50)
    print("Пример с polars DataFrame")
    print("=" * 50)

    # Создаем DataFrame с polars
    df = pl.DataFrame(
        {
            "name": ["Alice", "Bob", "Charlie", "David", "Eve", "Frank"],
            "age": [25, 30, 35, 28, 32, 27],
            "salary": [50000, 60000, 75000, 55000, 70000, 52000],
            "city": ["New York", "London", "Paris", "Berlin", "Tokyo", "Sydney"],
        }
    )

    print(f"\nDataFrame shape: {df.shape}")
    print(f"Columns: {list(df.columns)}")

    # Создаем объект DataOut
    data_out = DataOut(df, id_start=0, line_range=(0, 3))
    print(f"\nID Start: {data_out.id_start}")
    print(f"Line Range: {data_out.line_range}")
    print(f"Columns: {data_out.columns}")


def example_datashow():
    """Пример использования DataShow (требует Jupyter окружение)."""
    print("\n" + "=" * 50)
    print("Пример с DataShow (только в Jupyter)")
    print("=" * 50)

    df = pd.DataFrame(
        {
            "A": list(range(20)),
            "B": list(range(20, 40)),
            "C": list(range(40, 60)),
        }
    )

    print(f"DataFrame created with shape: {df.shape}")
    print("В Jupyter окружении используйте:")
    print("  from UtilForWhatching import DataShow")
    print("  show = DataShow()")
    print("  show.show_tablet(df)")


if __name__ == "__main__":
    example_pandas()
    example_polars()
    example_datashow()
    print("\n" + "=" * 50)
    print("Примеры выполнены успешно!")
    print("=" * 50)
