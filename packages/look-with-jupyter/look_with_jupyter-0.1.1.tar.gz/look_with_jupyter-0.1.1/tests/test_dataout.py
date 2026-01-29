"""Тесты для класса DataOut."""

import pandas as pd
import pytest

from UtilForWhatching import DataOut


class TestDataOutInit:
    """Тесты инициализации класса DataOut."""

    def test_init_pandas_df(self, sample_pandas_df):
        """Проверяет инициализацию с pandas DataFrame."""
        data_out = DataOut(sample_pandas_df)
        assert data_out.id_start == 0
        assert data_out.line_range == (0, 10)
        assert len(data_out.columns) == 4
        assert list(data_out.columns) == ["name", "age", "salary", "city"]

    def test_init_polars_df(self, sample_polars_df):
        """Проверяет инициализацию с polars DataFrame."""
        data_out = DataOut(sample_polars_df)
        assert data_out.id_start == 0
        assert data_out.line_range == (0, 10)
        assert len(data_out.columns) == 4
        assert list(data_out.columns) == ["name", "age", "salary", "city"]

    def test_init_custom_params(self, sample_pandas_df):
        """Проверяет инициализацию с пользовательскими параметрами."""
        data_out = DataOut(sample_pandas_df, id_start=5, line_range=(2, 8))
        assert data_out.id_start == 5
        assert data_out.line_range == (2, 8)

    def test_init_invalid_data_type(self):
        """Проверяет выброс исключения при неподдерживаемом типе данных."""
        with pytest.raises(TypeError, match="Unsupported data type"):
            DataOut([1, 2, 3])

    def test_init_empty_pandas_df(self):
        """Проверяет инициализацию с пустым pandas DataFrame."""
        empty_df = pd.DataFrame()
        data_out = DataOut(empty_df)
        assert len(data_out.columns) == 0


class TestDataOutGetDataSlice:
    """Тесты метода _get_data_slice."""

    def test_get_data_slice_pandas(self, sample_pandas_df):
        """Проверяет получение среза данных для pandas."""
        data_out = DataOut(sample_pandas_df, id_start=0, line_range=(0, 5))
        slice_data = data_out._get_data_slice()
        assert len(slice_data) == 5
        assert list(slice_data["name"]) == ["Alice", "Bob", "Charlie", "David", "Eve"]

    def test_get_data_slice_polars(self, sample_polars_df):
        """Проверяет получение среза данных для polars."""
        data_out = DataOut(sample_polars_df, id_start=0, line_range=(0, 5))
        slice_data = data_out._get_data_slice()
        assert len(slice_data) == 5
        assert slice_data["name"].to_list() == ["Alice", "Bob", "Charlie", "David", "Eve"]

    def test_get_data_slice_with_offset(self, sample_pandas_df):
        """Проверяет получение среза с смещением."""
        data_out = DataOut(sample_pandas_df, id_start=2, line_range=(1, 4))
        slice_data = data_out._get_data_slice()
        # start_idx = 2 + 1 = 3, end_idx = 2 + 4 = 6
        assert len(slice_data) == 3
        assert list(slice_data["name"]) == ["David", "Eve", "Frank"]

    def test_get_data_slice_beyond_bounds(self, small_pandas_df):
        """Проверяет получение среза за пределами размера DataFrame."""
        data_out = DataOut(small_pandas_df, id_start=0, line_range=(0, 100))
        slice_data = data_out._get_data_slice()
        assert len(slice_data) == 3  # только 3 строки в DataFrame


class TestDataOutCallbacks:
    """Тесты обработчиков событий."""

    def test_on_range_change(self, sample_pandas_df):
        """Проверяет обработчик изменения диапазона."""
        data_out = DataOut(sample_pandas_df, id_start=0, line_range=(0, 5))
        original_range = data_out.line_range

        data_out.on_range_change({"new": (2, 8)})
        assert data_out.line_range == (2, 8)
        assert data_out.line_range != original_range

    def test_on_value_change(self, sample_pandas_df):
        """Проверяет обработчик изменения индекса."""
        data_out = DataOut(sample_pandas_df, id_start=0)
        original_start = data_out.id_start

        data_out.on_value_change({"new": 5})
        assert data_out.id_start == 5
        assert data_out.id_start != original_start

    def test_on_change_tag(self, sample_pandas_df):
        """Проверяет обработчик изменения колонок."""
        data_out = DataOut(sample_pandas_df)
        original_columns = data_out.columns.copy()

        new_columns = ["name", "age"]
        data_out.on_change_tag({"new": new_columns})
        assert data_out.columns == new_columns
        assert data_out.columns != original_columns

    def test_on_change_tag_empty(self, sample_pandas_df):
        """Проверяет обработчик с пустым списком колонок."""
        data_out = DataOut(sample_pandas_df)
        data_out.on_change_tag({"new": []})
        assert data_out.columns == []


class TestDataOutColumnHandling:
    """Тесты обработки колонок."""

    def test_columns_pandas(self, sample_pandas_df):
        """Проверяет получение колонок из pandas DataFrame."""
        data_out = DataOut(sample_pandas_df)
        assert "name" in data_out.columns
        assert "age" in data_out.columns
        assert "salary" in data_out.columns
        assert "city" in data_out.columns

    def test_columns_polars(self, sample_polars_df):
        """Проверяет получение колонок из polars DataFrame."""
        data_out = DataOut(sample_polars_df)
        assert "name" in data_out.columns
        assert "age" in data_out.columns
        assert "salary" in data_out.columns
        assert "city" in data_out.columns

    def test_slice_with_selected_columns(self, sample_pandas_df):
        """Проверяет срез с выбранными колонками."""
        data_out = DataOut(sample_pandas_df, id_start=0, line_range=(0, 3))
        data_out.on_change_tag({"new": ["name", "age"]})

        slice_data = data_out._get_data_slice()
        assert list(slice_data.columns) == ["name", "age"]
        assert len(slice_data) == 3
