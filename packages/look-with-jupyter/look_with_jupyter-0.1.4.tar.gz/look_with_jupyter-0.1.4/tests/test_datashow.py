"""Тесты для класса DataShow."""

from unittest.mock import MagicMock, patch

from UtilForWhatching import DataShow


class TestDataShowInit:
    """Тесты инициализации класса DataShow."""

    def test_init(self):
        """Проверяет инициализацию класса DataShow."""
        data_show = DataShow()
        assert data_show.display is None
        assert data_show.tab is None
        assert data_show.slider_database is None
        assert data_show.slider_range_index is None
        assert data_show.tags_column is None


class TestDataShowTablet:
    """Тесты метода show_tablet."""

    @patch("UtilForWhatching.LookInJupyter.display")
    @patch("UtilForWhatching.LookInJupyter.clear_output")
    def test_show_tablet_pandas(self, mock_clear, mock_display, sample_pandas_df):
        """Проверяет отображение pandas DataFrame."""
        mock_display_obj = MagicMock()
        mock_display.return_value = mock_display_obj

        data_show = DataShow()
        data_show.show_tablet(sample_pandas_df)

        assert data_show.tab is not None
        assert data_show.slider_database is not None
        assert data_show.slider_range_index is not None
        assert data_show.tags_column is not None
        assert mock_display.called

    @patch("UtilForWhatching.LookInJupyter.display")
    @patch("UtilForWhatching.LookInJupyter.clear_output")
    def test_show_tablet_polars(self, mock_clear, mock_display, sample_polars_df):
        """Проверяет отображение polars DataFrame."""
        mock_display_obj = MagicMock()
        mock_display.return_value = mock_display_obj

        data_show = DataShow()
        data_show.show_tablet(sample_polars_df)

        assert data_show.tab is not None
        assert data_show.slider_database is not None
        assert data_show.slider_range_index is not None
        assert data_show.tags_column is not None
        assert mock_display.called

    @patch("UtilForWhatching.LookInJupyter.display")
    @patch("UtilForWhatching.LookInJupyter.clear_output")
    def test_show_tablet_custom_params(self, mock_clear, mock_display, sample_pandas_df):
        """Проверяет отображение с пользовательскими параметрами."""
        mock_display_obj = MagicMock()
        mock_display.return_value = mock_display_obj

        data_show = DataShow()
        data_show.show_tablet(sample_pandas_df, id_start=5, line_range=(2, 8))

        assert data_show.slider_database.value == 5
        assert data_show.slider_range_index.value == (2, 8)

    @patch("UtilForWhatching.LookInJupyter.display")
    @patch("UtilForWhatching.LookInJupyter.clear_output")
    def test_show_tablet_clears_previous_display(self, mock_clear, mock_display, sample_pandas_df):
        """Проверяет очистку предыдущего отображения."""
        mock_display_obj = MagicMock()
        mock_display.return_value = mock_display_obj

        data_show = DataShow()
        data_show.show_tablet(sample_pandas_df)

        # Вызываем еще раз
        data_show.show_tablet(sample_pandas_df)
        assert mock_clear.called


class TestDataShowWidgets:
    """Тесты создания виджетов."""

    @patch("UtilForWhatching.LookInJupyter.display")
    def test_tab_structure(self, mock_display, sample_pandas_df):
        """Проверяет структуру вкладок."""
        mock_display_obj = MagicMock()
        mock_display.return_value = mock_display_obj

        data_show = DataShow()
        data_show.show_tablet(sample_pandas_df)

        assert len(data_show.tab.children) == 3
        assert len(data_show.tab.titles) == 3
        assert data_show.tab.titles == ("Индексы", "Диапазон", "Колонки")

    @patch("UtilForWhatching.LookInJupyter.display")
    def test_slider_database_config(self, mock_display, sample_pandas_df):
        """Проверяет конфигурацию слайдера для индексов."""
        mock_display_obj = MagicMock()
        mock_display.return_value = mock_display_obj

        data_show = DataShow()
        data_show.show_tablet(sample_pandas_df)

        assert data_show.slider_database.min == 0
        assert data_show.slider_database.max == len(sample_pandas_df) - 1
        assert data_show.slider_database.step == 10

    @patch("UtilForWhatching.LookInJupyter.display")
    def test_slider_range_config(self, mock_display, sample_pandas_df):
        """Проверяет конфигурацию слайдера для диапазона."""
        mock_display_obj = MagicMock()
        mock_display.return_value = mock_display_obj

        data_show = DataShow()
        data_show.show_tablet(sample_pandas_df, line_range=(0, 10))

        assert data_show.slider_range_index.value == (0, 10)
        assert data_show.slider_range_index.min == 0
        assert data_show.slider_range_index.max == 10

    @patch("UtilForWhatching.LookInJupyter.display")
    def test_tags_column_init(self, mock_display, sample_pandas_df):
        """Проверяет инициализацию виджета выбора колонок."""
        mock_display_obj = MagicMock()
        mock_display.return_value = mock_display_obj

        data_show = DataShow()
        data_show.show_tablet(sample_pandas_df)

        # Проверяем что все колонки присутствуют
        expected_columns = set(sample_pandas_df.columns)
        actual_columns = set(data_show.tags_column.value)
        assert expected_columns == actual_columns


class TestDataShowIntegration:
    """Интеграционные тесты."""

    @patch("UtilForWhatching.LookInJupyter.display")
    def test_widgets_created(self, mock_display, sample_pandas_df):
        """Проверяет создание виджетов."""
        mock_display_obj = MagicMock()
        mock_display.return_value = mock_display_obj

        data_show = DataShow()
        data_show.show_tablet(sample_pandas_df)

        # Проверяем что все виджеты созданы
        assert data_show.slider_database is not None
        assert data_show.slider_range_index is not None
        assert data_show.tags_column is not None

    @patch("UtilForWhatching.LookInJupyter.display")
    def test_show_tablet_with_small_df(self, mock_display, small_pandas_df):
        """Проверяет отображение маленького DataFrame."""
        mock_display_obj = MagicMock()
        mock_display.return_value = mock_display_obj

        data_show = DataShow()
        data_show.show_tablet(small_pandas_df)

        assert data_show.slider_database.max == len(small_pandas_df) - 1
