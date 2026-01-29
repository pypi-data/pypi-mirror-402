# LookWithJupyter

## English

Interactive module for viewing `polars` or `pandas` tables using Jupyter widgets.

A convenient solution for working with large DataFrames directly in Jupyter Notebook/Lab with interactive controls for data navigation and filtering.

![Exemple](./Images/Exemple.png)

### Features

- ✨ Support for pandas and polars DataFrames
- 📊 Interactive Jupyter widgets
- 🎛️ Display range control for rows
- 🏷️ Column selection
- 🧪 Full test coverage
- 📦 Ready to install as a module
- 🔧 Simple and intuitive API

### Installation

#### Requirements

- Python >= 3.11
- Jupyter Notebook or Jupyter Lab
- pandas and/or polars

#### Via GitHub Releases (recommended)

Download the latest `.whl` file from [Releases](https://github.com/yourusername/look-with-jupyter/releases) and install:

```bash
pip install look-with-jupyter-0.1.0-py3-none-any.whl
```

#### From sources (development mode)

```bash
git clone https://github.com/yourusername/look-with-jupyter.git
cd look-with-jupyter
pip install -e ".[dev]"
```

#### From PyPI (when published)

```bash
pip install look-with-jupyter
```

### Quick Start

```python
from UtilForWhatching import DataShow
import pandas as pd

# Create a DataFrame
df = pd.DataFrame({
    'name': ['Alice', 'Bob', 'Charlie', 'David', 'Eve'],
    'age': [25, 30, 35, 28, 32],
    'salary': [50000, 60000, 75000, 55000, 65000]
})

# Display interactive widget in one line!
DataShow().show_tablet(df)
```

After execution you will get an interactive interface with:

- Slider for scrolling data
- Display range control
- Column visibility selection

### Usage

#### Example 1: DataShow - High-level API (recommended)

The simplest way to use for quick data viewing:

```python
from UtilForWhatching import DataShow
import pandas as pd

# Create a DataFrame
df = pd.DataFrame({
    'name': ['Alice', 'Bob', 'Charlie'],
    'age': [25, 30, 35],
    'salary': [50000, 60000, 75000]
})

# Display interactive widget
show = DataShow()
show.show_tablet(df)  # Pandas is used by default
```

**Parameters for `show_tablet()`:**

- `data_set`: DataFrame to display
- `id_start` (int, default=0): Starting index
- `line_range` (tuple, default=(0, 10)): Number of rows per page
- `lib_work` (str, default="pandas"): "pandas" or "polars"

---

## Русский

Интерактивный модуль для просмотра таблиц `polars` или `pandas` с помощью виджетов Jupyter.

Удобное решение для работы с большими DataFrame'ами прямо в Jupyter Notebook/Lab с интерактивными элементами управления для навигации и фильтрации данных.

![Exemple](./Images/Exemple.png)

## Особенности

- ✨ Поддержка pandas и polars DataFrames
- 📊 Интерактивные Jupyter виджеты
- 🎛️ Управление диапазоном выводимых строк  
- 🏷️ Выбор отображаемых колонок
- 🧪 Полное покрытие тестами
- 📦 Готов к установке как модуль
- 🔧 Простой и интуитивный API

## Установка

### Требования

- Python >= 3.11
- Jupyter Notebook или Jupyter Lab
- pandas и/или polars

### Через GitHub Releases (рекомендуется)

Скачайте последнюю версию `.whl` файла из [Releases](https://github.com/yourusername/look-with-jupyter/releases) и установите:

```bash
pip install look-with-jupyter-0.1.0-py3-none-any.whl
```

### Из исходников (в режиме разработки)

```bash
git clone https://github.com/yourusername/look-with-jupyter.git
cd look-with-jupyter
pip install -e ".[dev]"
```

### Из PyPI (когда будет опубликовано)

```bash
pip install look-with-jupyter
```

## Быстрый старт

```python
from UtilForWhatching import DataShow
import pandas as pd

# Создаем DataFrame
df = pd.DataFrame({
    'name': ['Alice', 'Bob', 'Charlie', 'David', 'Eve'],
    'age': [25, 30, 35, 28, 32],
    'salary': [50000, 60000, 75000, 55000, 65000]
})

# Отображаем интерактивный виджет в одной строке!
DataShow().show_tablet(df)
```

После выполнения вы получите интерактивный интерфейс с:

- Слайдером для прокрутки данных
- Контролем диапазона отображаемых строк
- Выбором видимых колонок

## Использование

### Пример 1: DataShow - Высокоуровневый API (рекомендуется)

Самый простой способ использования для быстрого просмотра данных:

```python
from UtilForWhatching import DataShow
import pandas as pd

# Создаем DataFrame
df = pd.DataFrame({
    'name': ['Alice', 'Bob', 'Charlie'],
    'age': [25, 30, 35],
    'salary': [50000, 60000, 75000]
})

# Отображаем интерактивный виджет
show = DataShow()
show.show_tablet(df)  # Используется по умолчанию pandas
```

**Параметры `show_tablet()`:**

- `data_set`: DataFrame для отображения
- `id_start` (int, default=0): Начальный индекс
- `line_range` (tuple, default=(0, 10)): Кол-во строк на странице
- `lib_work` (str, default="pandas"): "pandas" или "polars"

### Пример 2: DataOut - Низкоуровневый API

Для более гибкого управления данными и программной работы:

```python
from UtilForWhatching import DataOut
import polars as pl

# Создаем DataFrame с Polars
df = pl.DataFrame({
    'A': [1, 2, 3, 4, 5],
    'B': [10, 20, 30, 40, 50],
    'C': [100, 200, 300, 400, 500]
})

# Создаем объект для управления срезом
data_out = DataOut(df, id_start=0, line_range=(0, 10))

# Получаем срез данных
slice_data = data_out._get_data_slice()
print(slice_data)

# Обновляем диапазон просмотра
data_out.on_range_change((0, 5))  # Теперь показываем 5 строк
```

## API Справочник

### Класс `DataOut`

Отвечает за управление срезом DataFrame и его обновление. Создает визуальное представление данных с возможностью интерактивного управления.

**Параметры конструктора:**

| Параметр | Тип | Описание | По умолчанию |
| --- | --- | --- | --- |
| `data_set` | pd.DataFrame \| pl.DataFrame | Просматриваемый DataFrame | Обязателен |
| `id_start` | int | Начальный индекс для смещения | 0 |
| `line_range` | tuple[int, int] | Диапазон строк для отображения (от, до) | (0, 10) |

**Методы:**

| Метод | Описание | Возвращает |
| --- | --- | --- |
| `_get_data_slice()` | Получить срез данных согласно текущим параметрам | pd.DataFrame \| pl.DataFrame |
| `on_range_change(data)` | Обработчик изменения диапазона строк | None |
| `on_value_change(data)` | Обработчик изменения начального индекса | None |
| `on_change_tag(data)` | Обработчик изменения выбранных колонок | None |

**Примеры использования методов:**

```python
# Изменение диапазона отображаемых строк
data_out.on_range_change((0, 20))

# Переход на другой индекс
data_out.on_value_change(100)

# Выбор определенных колонок
data_out.on_change_tag({'value': ['name', 'salary']})
```

### Класс `DataShow`

Создает полный интерактивный интерфейс для отображения DataFrame в Jupyter с виджетами управления.

**Методы:**

| Метод | Описание |
| --- | --- |
| `show_tablet(data_set, id_start=0, line_range=(0, 10), lib_work="pandas")` | Отобразить DataFrame с интерактивными виджетами |

**Создаваемые виджеты:**

- **IntSlider**: Слайдер для выбора начального индекса (прокрутка)
- **IntRangeSlider**: Range slider для выбора диапазона строк (от, до)
- **TagsInput**: Тегированный ввод для выбора колонок для отображения

## Тестирование

Проект полностью покрыт тестами для обеспечения надежности работы.

### Запуск всех тестов

```bash
pytest
```

или с использованием `uv`:

```bash
uv run pytest -v
```

### Запуск тестов с отчетом о покрытии

```bash
pytest --cov=UtilForWhatching --cov-report=html
```

Отчет будет доступен в `htmlcov/index.html`

### Запуск конкретного теста

```bash
pytest tests/test_dataout.py::TestDataOutInit::test_init_pandas_df -v
```

### Тестовые наборы

- **test_dataout.py**: Тесты класса `DataOut` (инициализация, получение срезов, обработчики)
- **test_datashow.py**: Тесты класса `DataShow` (интеграция с виджетами)

Смотрите [TESTING.md](./TESTING.md) для более подробной информации о тестировании.

## Сборка и публикация

### Собрать wheel (бинарный пакет)

```bash
uv build --target wheel
```

### Собрать исходный код (sdist)

```bash
uv build --target sdist
```

### Собрать оба варианта

```bash
uv build
```

Результаты сборки будут в папке `dist/`

### Публикация на PyPI

```bash
# Требуется python-twine или использование GitHub Actions
twine upload dist/*
```

## Развитие проекта

### Требования для разработки

- Python >= 3.11
- uv (менеджер пакетов) - [установка](https://docs.astral.sh/uv/getting-started/installation/)
- pytest (тестирование)
- black (форматирование)
- ruff (линтинг)
- mypy (проверка типов)
- ipywidgets (для интерактивных виджетов)

### Установка dev-зависимостей

```bash
uv sync --all-groups
```

### Форматирование кода

```bash
black .
```

### Проверка кода (линтинг)

```bash
ruff check .
```

### Проверка типов

```bash
mypy UtilForWhatching
```

### Полная проверка перед коммитом

```bash
# Запустить все проверки
black .
ruff check --fix .
mypy UtilForWhatching
pytest -v
```

## Структура проекта

```bash
look-with-jupyter/
├── UtilForWhatching/          # Основной пакет
│   ├── __init__.py            # Экспорт публичного API
│   └── LookInJupyter.py       # Основной код
├── tests/                     # Модульные и интеграционные тесты
│   ├── __init__.py            
│   ├── conftest.py            # Конфигурация pytest и fixtures
│   ├── test_dataout.py        # Тесты класса DataOut
│   └── test_datashow.py       # Тесты класса DataShow
├── .github/workflows/         # GitHub Actions CI/CD
├── Images/                    # Примеры и скриншоты
├── pyproject.toml             # Конфигурация проекта
├── TESTING.md                 # Руководство по тестированию
├── example.py                 # Примеры использования
└── README.md                  # Этот файл
```

## Лицензия

Этот проект лицензирован под [MIT License](LICENSE) - см. файл [LICENSE](./LICENSE) для деталей.

## Контрибьютинг

Мы приветствуем контрибьюции! Пожалуйста, следуйте этим шагам:

1. **Форкните репозиторий**
2. **Создайте ветку для вашей фичи**:

   ```bash
   git checkout -b feature/amazing-feature
   ```

3. **Совершите ваши изменения** с понятными commit messages:

   ```bash
   git commit -m 'Add amazing feature: описание'
   ```

4. **Отправьте ветку в репозиторий**:

   ```bash
   git push origin feature/amazing-feature
   ```

5. **Откройте Pull Request** с описанием ваших изменений

**Перед отправкой PR убедитесь, что:**

- ✅ Все тесты проходят: `pytest -v`
- ✅ Код отформатирован: `black .`
- ✅ Нет ошибок линтинга: `ruff check .`
- ✅ Типы проверены: `mypy UtilForWhatching`
- ✅ Добавлены тесты для новых функций
- ✅ Обновлена документация если необходимо

## Автор

Создано как полезный инструмент для работы с данными в Jupyter окружении.
