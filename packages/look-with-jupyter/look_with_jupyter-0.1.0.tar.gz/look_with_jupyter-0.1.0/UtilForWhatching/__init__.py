"""
LookWithJupyter - модуль для просмотра таблиц pandas и polars в Jupyter.

Основные компоненты:
    - DataOut: класс для управления срезом DataFrame
    - DataShow: класс для интерактивного отображения данных в Jupyter
"""

from .LookInJupyter import DataOut, DataShow

__version__ = "0.1.0"
__all__ = ["DataOut", "DataShow"]
