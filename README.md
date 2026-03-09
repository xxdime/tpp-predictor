# TPP Predictor — Прогнозирование износа деталей турбин ТЭС

Десктопное приложение на Python для прогнозирования стачивания (гидроэрозионного износа) лопаток последних ступеней тепловых турбин на ТЭС. Поддерживает пользовательские шаблоны деталей с произвольными параметрами измерения.

## Возможности

- Управление шаблонами деталей с произвольными параметрами (название, единица измерения, критическое значение)
- Ведение базы данных деталей и журнала измерений
- Прогнозирование износа методом наименьших квадратов (МНК) с выбором вида функции
- Оценка доверительного интервала с помощью гауссовской регрессии (GPR)
- Визуализация данных на интерактивном графике
- Экспорт данных по всем деталям в ZIP-архив (Excel-файлы)

## Требования

- Python 3.11 или выше
- Зависимости (см. `requirements.txt`):
  - PySide6 >= 6.6.0
  - pyqtgraph >= 0.13.3
  - SQLAlchemy >= 2.0.0
  - scipy >= 1.11.0
  - scikit-learn >= 1.3.0
  - numpy >= 1.24.0
  - openpyxl >= 3.1.0

## Установка зависимостей

```bash
pip install -r requirements.txt
```

## Запуск приложения

```bash
python main.py
```

## Сборка установщика с помощью Briefcase

Установите Briefcase:

```bash
pip install briefcase
```

Создайте установщик для вашей платформы:

```bash
# Windows
briefcase create windows
briefcase build windows
briefcase package windows

# Linux
briefcase create linux
briefcase build linux
briefcase package linux
```

## Структура проекта

```
tpp-predictor/
├── main.py                        # Точка входа
├── pyproject.toml                 # Конфигурация Briefcase
├── requirements.txt               # Зависимости
├── app/
│   ├── database/
│   │   └── engine.py              # SQLAlchemy engine, сессия, init_db
│   ├── models/
│   │   ├── template.py            # Template, TemplateParameter
│   │   ├── part.py                # Part
│   │   ├── measurement.py         # Measurement
│   │   └── forecast_settings.py   # ForecastSettings
│   ├── services/
│   │   ├── forecast_service.py    # МНК и GPR прогнозирование
│   │   └── export_service.py      # Экспорт в ZIP/Excel
│   └── views/
│       ├── main_window.py         # Главное окно
│       ├── part_window.py         # Окно детали
│       ├── templates_window.py    # Окно шаблонов
│       ├── dialogs/
│       │   ├── part_dialog.py     # Диалог добавления/редактирования детали
│       │   ├── measurement_dialog.py
│       │   ├── template_dialog.py
│       │   ├── parameter_dialog.py
│       │   └── settings_dialog.py # Настройки прогнозирования
│       └── widgets/
│           └── forecast_plot.py   # Виджет графика
```

## Лицензия

MIT