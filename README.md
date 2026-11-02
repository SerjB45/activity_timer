# 🍅 Activity Timer

Pomodoro-таймер для контроля рабочих сессий и отдыха.

## Возможности

- Настраиваемое время работы и отдыха
- Автоматическое переключение между фазами
- Подсчёт завершённых циклов и затраченного времени
- Статистика за последние 7 дней
- Сохранение настроек и статистики

## Установка

```powershell
# Виртуальное окружение
python -m venv venv
venv\Scripts\activate

# Запуск
python main.py
```

## Компиляция

```powershell
pip install pyinstaller
pyinstaller --onefile --windowed --name activity_timer main.py
```

## Тесты

```powershell
python -m unittest discover tests/ -v
```

## Стек

| Компонент    | Технология        |
|-------------|-------------------|
| Язык        | Python 3.10+      |
| GUI         | tkinter           |
| Тесты       | unittest          |
| Компиляция  | PyInstaller       |

## Инструменты разработки

- **GigaCode** — AI-ассистент для рефакторинга и генерации кода
- **PyInstaller** — упаковка в `.exe`
- **unittest** — модульные тесты (71 тест)

## Структура

```
main.py              # Точка входа
config.py            # Константы и настройки
theme.py             # Цветовая палитра и стили
models.py            # Модели данных
storage.py           # Репозитории (JSON)
timer_service.py     # Бизнес-логика таймера
ui/                  # Графический интерфейс
tests/               # Модульные тесты
```

## Настройки

Файл `activity_settings.json` создаётся автоматически:

```json
{
  "work_minutes": 25,
  "rest_minutes": 5
}
```

## Лицензия

MIT
