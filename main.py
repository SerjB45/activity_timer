import logging

from storage import SettingsRepository, StatsRepository
from ui.main_window import MainWindow


def setup_logging() -> None:
    """Настроить базовое логирование."""
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )


def main() -> None:
    setup_logging()

    # Загрузка данных
    settings = SettingsRepository.load()
    stats = StatsRepository.load()

    # Создание и запуск приложения
    app = MainWindow(settings=settings, stats=stats)
    app.initialize()
    app.mainloop()


if __name__ == "__main__":
    main()
