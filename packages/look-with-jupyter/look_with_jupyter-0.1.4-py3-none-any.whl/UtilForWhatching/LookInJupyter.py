from typing import Any

# Проверка доступности библиотек
_available_libs = {
    "ipywidgets": False,
    "pandas": False,
    "polars": False,
    "IPython": False,
}

try:
    import ipywidgets as widgets

    _available_libs["ipywidgets"] = True
except ImportError:
    print("Внимание: ipywidgets не установлен. Install: pip install ipywidgets")

try:
    import pandas as pd

    _available_libs["pandas"] = True
except ImportError:
    print("Внимание: pandas не установлен. Install: pip install pandas")

try:
    import polars as pol

    _available_libs["polars"] = True
except ImportError:
    print("Внимание: polars не установлен. Install: pip install polars")

try:
    from IPython.display import DisplayHandle, clear_output, display

    _available_libs["IPython"] = True
except ImportError:
    print("Внимание: IPython не установлен. Install: pip install IPython")


def _check_required_libs(required_libs: list[str]) -> bool:
    """Проверить, установлены ли необходимые библиотеки.

    Args:
        required_libs: Список имён требуемых библиотек

    Returns:
        True если все библиотеки установлены, False иначе
    """
    missing = [lib for lib in required_libs if not _available_libs.get(lib, False)]
    if missing:
        print(f"Ошибка: не установлены библиотеки: {', '.join(missing)}")
        return False
    return True


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

        # Более явная проверка типа
        is_pandas = isinstance(data_set, pd.DataFrame)
        is_polars = pol is not None and isinstance(data_set, pol.DataFrame)
        # Проверка наличия требуемых библиотек
        if not (is_pandas or is_polars):
            raise TypeError(
                "Unsupported data type. Only pandas and polars DataFrames are supported."
            )

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
        # Проверка наличия требуемых библиотек
        if not _check_required_libs(["ipywidgets", "IPython"]):
            print(
                "Внимание: некоторые библиотеки не установлены. DataShow может работать неправильно."
            )

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
    ) -> None:
        """Отобразить интерактивный виджет для просмотра DataFrame.

        Args:
            data_set: DataFrame для отображения
            id_start: Начальный индекс. По умолчанию 0.
            line_range: Диапазон строк. По умолчанию (0, 10).
            lib_work: Используемая библиотека. По умолчанию 'pandas'.
        """
        lib = "pandas" if isinstance(data_set, pd.DataFrame) else "polars"
        # Проверка наличия требуемых библиотек
        if not _check_required_libs(["ipywidgets", "IPython", lib]):
            print("Ошибка: не удалось запустить show_tablet - не установлены требуемые библиотеки")
            return

        # Очистка предыдущего отображения
        if self.display:
            clear_output()
            self.display = None

        # Создание виджетов
        self.tab = widgets.Tab()
        self.slider_database = widgets.IntSlider(
            value=id_start,
            min=0,
            max=len(data_set) - 1,
            step=line_range[1] - line_range[0],
            description="Индекс: ",
        )
        self.slider_range_index = widgets.IntRangeSlider(
            value=line_range, min=line_range[0], max=line_range[1], step=1, description="С .. по .."
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
