"""Тесты Storage (SettingsRepository, StatsRepository)."""

import json
import tempfile
import unittest
from pathlib import Path

from models import DayStats, Settings, Stats
from storage import SettingsRepository, StatsRepository


class TestSettingsRepositoryLoad(unittest.TestCase):
    """Проверка загрузки настроек."""

    def test_load_defaults_when_file_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "settings.json"
            SettingsRepository._file = filepath
            settings = SettingsRepository.load()
            self.assertEqual(settings.work_minutes, 25)
            self.assertEqual(settings.rest_minutes, 5)

    def test_load_valid_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "settings.json"
            SettingsRepository._file = filepath
            filepath.write_text(json.dumps({"work_minutes": 45, "rest_minutes": 10}))
            settings = SettingsRepository.load()
            self.assertEqual(settings.work_minutes, 45)
            self.assertEqual(settings.rest_minutes, 10)

    def test_load_rejects_work_too_low(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "settings.json"
            SettingsRepository._file = filepath
            filepath.write_text(json.dumps({"work_minutes": 0, "rest_minutes": 5}))
            settings = SettingsRepository.load()
            self.assertEqual(settings.work_minutes, 25)

    def test_load_rejects_work_too_high(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "settings.json"
            SettingsRepository._file = filepath
            filepath.write_text(json.dumps({"work_minutes": 300, "rest_minutes": 5}))
            settings = SettingsRepository.load()
            self.assertEqual(settings.work_minutes, 25)

    def test_load_rejects_rest_too_low(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "settings.json"
            SettingsRepository._file = filepath
            filepath.write_text(json.dumps({"work_minutes": 25, "rest_minutes": 0}))
            settings = SettingsRepository.load()
            self.assertEqual(settings.rest_minutes, 5)

    def test_load_rejects_rest_too_high(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "settings.json"
            SettingsRepository._file = filepath
            filepath.write_text(json.dumps({"work_minutes": 25, "rest_minutes": 200}))
            settings = SettingsRepository.load()
            self.assertEqual(settings.rest_minutes, 5)

    def test_load_invalid_json_uses_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "settings.json"
            SettingsRepository._file = filepath
            filepath.write_text("not valid json{{{")
            settings = SettingsRepository.load()
            self.assertEqual(settings.work_minutes, 25)

    def test_load_empty_object_uses_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "settings.json"
            SettingsRepository._file = filepath
            filepath.write_text("{}")
            settings = SettingsRepository.load()
            self.assertEqual(settings.work_minutes, 25)


class TestSettingsRepositorySave(unittest.TestCase):
    """Проверка сохранения настроек."""

    def test_save_writes_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "settings.json"
            SettingsRepository._file = filepath
            settings = Settings(work_minutes=40, rest_minutes=10)
            result = SettingsRepository.save(settings)
            self.assertTrue(result)
            self.assertTrue(filepath.exists())

    def test_save_writes_correct_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "settings.json"
            SettingsRepository._file = filepath
            settings = Settings(work_minutes=40, rest_minutes=10)
            SettingsRepository.save(settings)
            data = json.loads(filepath.read_text())
            self.assertEqual(data["work_minutes"], 40)
            self.assertEqual(data["rest_minutes"], 10)

    def test_save_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "settings.json"
            SettingsRepository._file = filepath
            original = Settings(work_minutes=50, rest_minutes=15)
            SettingsRepository.save(original)
            loaded = SettingsRepository.load()
            self.assertEqual(loaded.work_minutes, 50)
            self.assertEqual(loaded.rest_minutes, 15)


class TestStatsRepositoryLoad(unittest.TestCase):
    """Проверка загрузки статистики."""

    def test_load_defaults_when_file_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "stats.json"
            StatsRepository._file = filepath
            stats = StatsRepository.load()
            self.assertIsInstance(stats, Stats)
            self.assertEqual(len(stats.days), 0)

    def test_load_valid_stats(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "stats.json"
            StatsRepository._file = filepath
            data = {
                "days": {
                    "2025-01-01": {
                        "completed_cycles": 5,
                        "work_seconds": 7500.0,
                        "rest_seconds": 1500.0,
                    }
                }
            }
            filepath.write_text(json.dumps(data))
            stats = StatsRepository.load()
            self.assertEqual(len(stats.days), 1)
            record = stats.days["2025-01-01"]
            self.assertEqual(record.completed_cycles, 5)
            self.assertEqual(record.work_seconds, 7500.0)

    def test_load_invalid_json_uses_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "stats.json"
            StatsRepository._file = filepath
            filepath.write_text("{invalid}")
            stats = StatsRepository.load()
            self.assertEqual(len(stats.days), 0)


class TestStatsRepositorySave(unittest.TestCase):
    """Проверка сохранения статистики."""

    def test_save_writes_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "stats.json"
            StatsRepository._file = filepath
            stats = Stats()
            result = StatsRepository.save(stats)
            self.assertTrue(result)
            self.assertTrue(filepath.exists())

    def test_save_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "stats.json"
            StatsRepository._file = filepath
            original = Stats(days={
                "2025-06-15": DayStats(
                    completed_cycles=3,
                    work_seconds=4500.0,
                    rest_seconds=900.0,
                )
            })
            StatsRepository.save(original)
            loaded = StatsRepository.load()
            self.assertEqual(len(loaded.days), 1)
            record = loaded.days["2025-06-15"]
            self.assertEqual(record.completed_cycles, 3)
            self.assertEqual(record.work_seconds, 4500.0)


class TestStatsToday(unittest.TestCase):
    """Проверка получения сегодняшней статистики."""

    def test_today_creates_record(self) -> None:
        stats = Stats()
        record = stats.today()
        self.assertIsInstance(record, DayStats)

    def test_today_returns_same_record(self) -> None:
        stats = Stats()
        record1 = stats.today()
        record2 = stats.today()
        self.assertIs(record1, record2)

    def test_today_normalizes_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "stats.json"
            StatsRepository._file = filepath
            stats = Stats()
            record = stats.today()
            record.completed_cycles = -5  # Негативное значение
            record.work_seconds = -100.0
            record.rest_seconds = -50.0
            StatsRepository.save(stats)
            loaded = StatsRepository.load()
            self.assertEqual(loaded.today().completed_cycles, 0)
            self.assertEqual(loaded.today().work_seconds, 0.0)


if __name__ == "__main__":
    unittest.main()
