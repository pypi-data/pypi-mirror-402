from typing import Any

import ipywidgets as widgets
import pandas as pd
import polars as pol
from IPython.display import DisplayHandle, clear_output, display


class DataOut:
    """Класс для просмотра DataFrame элементов по 10 за раз."""

    def __init__(
        self,
        data_set: pd.DataFrame | pol.DataFrame,
        id_start: int = 0,
        line_range: tuple[int, int] = (0, 10),
    ) -> None:
        """Инициализация класса.

        Args:
            data_set: Просматриваемый DataFrame (pandas или polars)
            id_start: С какого индекса начинаем. По умолчанию 0.
            line_range: Диапазон строк для просмотра. По умолчанию (0, 10).
            lib_work: Используемая библиотека ('pandas' или 'polars'). По умолчанию 'pandas'.
        """
        self.data_set = data_set
        self.id_start = id_start
        self.line_range = line_range

        # Получение списка колонок в зависимости от библиотеки
        if isinstance(data_set, pd.DataFrame):
            self.columns = data_set.columns.tolist()
        elif isinstance(self.data_set, pol.DataFrame):
            self.columns = list(data_set.columns)
        else:
            raise TypeError(
                "Unsupported data type. Only pandas and polars DataFrames are supported."
            )

        # Инициализация отображения
        self.to_display = DisplayHandle()
        self.to_display.display(self._get_data_slice())

    def _get_data_slice(self):
        """Получить срез данных в зависимости от используемой библиотеки.

        Returns:
            DataFrame: Срез данных для отображения
        """
        start_idx = self.id_start + self.line_range[0]
        end_idx = self.id_start + self.line_range[1]

        if isinstance(self.data_set, pd.DataFrame):
            return self.data_set[self.columns].iloc[start_idx:end_idx]
        elif isinstance(self.data_set, pol.DataFrame):
            return self.data_set[self.columns][start_idx:end_idx]
        else:
            raise TypeError(
                "Unsupported data type. Only pandas and polars DataFrames are supported."
            )

    def on_range_change(self, data: dict) -> None:
        """Обработчик изменения диапазона выводимого DataFrame.

        Args:
            data: Данные от события ipywidgets
        """
        self.line_range = data["new"]
        self.to_display.update(self._get_data_slice())

    def on_value_change(self, data: dict) -> None:
        """Обработчик изменения индекса начала просмотра.

        Args:
            data: Данные от события ipywidgets
        """
        self.id_start = data["new"]
        self.to_display.update(self._get_data_slice())

    def on_change_tag(self, data: dict) -> None:
        """Обработчик изменения выбранных колонок.

        Args:
            data: Данные от события ipywidgets
        """
        self.columns = data["new"]
        self.to_display.update(self._get_data_slice())


class DataShow:
    """Класс для отображения DataFrame в Jupyter."""

    def __init__(self) -> None:
        self.display: Any = None
        self.tab: widgets.Tab | None = None
        self.slider_database: widgets.IntSlider | None = None
        self.slider_range_index: widgets.IntRangeSlider | None = None
        self.tags_column: widgets.TagsInput | None = None

    def show_tablet(
        self,
        data_set: pd.DataFrame | pol.DataFrame,
        id_start: int = 0,
        line_range: tuple[int, int] = (0, 10),
        lib_work: str = "pandas",
    ) -> None:
        """Отобразить интерактивный виджет для просмотра DataFrame.

        Args:
            data_set: DataFrame для отображения
            id_start: Начальный индекс. По умолчанию 0.
            line_range: Диапазон строк. По умолчанию (0, 10).
            lib_work: Используемая библиотека. По умолчанию 'pandas'.
        """
        # Очистка предыдущего отображения
        if self.display:
            clear_output()
            self.display = None

        # Создание виджетов
        self.tab = widgets.Tab()
        self.slider_database = widgets.IntSlider(
            value=id_start, min=0, max=len(data_set) - 1, step=10, description="Индекс: "
        )
        self.slider_range_index = widgets.IntRangeSlider(
            value=line_range, min=0, max=10, step=1, description="С .. по .."
        )

        # Создание виджета для выбора колонок
        if isinstance(data_set, pd.DataFrame):
            columns = data_set.columns.tolist()
        else:
            columns = list(data_set.columns)

        self.tags_column = widgets.TagsInput(value=columns, allowed_tags=columns)

        # Настройка вкладок
        self.tab.children = [self.slider_database, self.slider_range_index, self.tags_column]
        self.tab.titles = ["Индексы", "Диапазон", "Колонки"]

        # Отображение виджетов
        self.display = display(self.tab, display_id=True, clear=True)

        # Создание обработчика данных и привязка событий
        data_out = DataOut(
            data_set,
            id_start=id_start,
            line_range=line_range,
        )
        self.slider_range_index.observe(data_out.on_range_change, names="value")
        self.slider_database.observe(data_out.on_value_change, names="value")
        self.tags_column.observe(data_out.on_change_tag, names="value")
