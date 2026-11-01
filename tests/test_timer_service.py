"""Тесты TimerService."""

import time
import unittest
from unittest.mock import MagicMock

from models import Settings, Stats, TimerState
from timer_service import TimerService


def _make_service(
    work_minutes: int = 25,
    rest_minutes: int = 5,
    **kwargs,
) -> TimerService:
    """Создать TimerService с mock-коллбэками."""
    on_notification = MagicMock()
    on_sound = MagicMock()
    on_error = MagicMock()
    for k, v in kwargs.items():
        setattr(TimerService.__init__, f"_{k}", v)

    service = TimerService(
        settings=Settings(work_minutes=work_minutes, rest_minutes=rest_minutes),
        stats=Stats(),
        on_notification=on_notification,
        on_sound=on_sound,
        on_error=on_error,
    )
    service._on_notification = on_notification
    service._on_sound = on_sound
    service._on_error = on_error
    return service


class TestTimerServiceInitialState(unittest.TestCase):
    """Проверка начального состояния."""

    def test_initial_phase_is_work(self) -> None:
        service = _make_service()
        self.assertEqual(service.phase, "work")

    def test_initial_running_is_false(self) -> None:
        service = _make_service()
        self.assertFalse(service.running)

    def test_initial_paused_is_false(self) -> None:
        service = _make_service()
        self.assertFalse(service.paused)

    def test_initial_remaining_matches_work_minutes(self) -> None:
        service = _make_service(work_minutes=30)
        self.assertEqual(service.remaining, 30 * 60)


class TestTimerServiceStart(unittest.TestCase):
    """Проверка запуска таймера."""

    def test_start_sets_running_to_true(self) -> None:
        service = _make_service()
        service.start()
        self.assertTrue(service.running)

    def test_start_resets_phase_to_work(self) -> None:
        service = _make_service()
        service._phase = "rest"
        service.start()
        self.assertEqual(service.phase, "work")

    def test_start_resets_remaining(self) -> None:
        service = _make_service(work_minutes=15)
        service.start()
        self.assertEqual(service.remaining, 15 * 60)

    def test_start_does_not_restart_if_already_running(self) -> None:
        service = _make_service()
        service.start()
        running_before = service.running
        service.start()
        self.assertTrue(service.running)


class TestTimerServicePauseResume(unittest.TestCase):
    """Проверка паузы и продолжения."""

    def test_pause_sets_paused_to_true(self) -> None:
        service = _make_service()
        service.start()
        service.pause()
        self.assertTrue(service.paused)

    def test_pause_does_nothing_if_not_running(self) -> None:
        service = _make_service()
        service.pause()
        self.assertFalse(service.running)

    def test_pause_does_nothing_if_already_paused(self) -> None:
        service = _make_service()
        service.start()
        service.pause()
        service.pause()
        self.assertTrue(service.paused)

    def test_resume_sets_paused_to_false(self) -> None:
        service = _make_service()
        service.start()
        service.pause()
        service.resume()
        self.assertFalse(service.paused)

    def test_resume_does_nothing_if_not_running(self) -> None:
        service = _make_service()
        service.resume()
        self.assertFalse(service.running)

    def test_resume_does_nothing_if_not_paused(self) -> None:
        service = _make_service()
        service.start()
        service.resume()
        self.assertFalse(service.paused)


class TestTimerServiceStop(unittest.TestCase):
    """Проверка остановки таймера."""

    def test_stop_sets_running_to_false(self) -> None:
        service = _make_service()
        service.start()
        service.stop()
        self.assertFalse(service.running)

    def test_stop_resets_phase_to_work(self) -> None:
        service = _make_service()
        service.start()
        service.stop()
        self.assertEqual(service.phase, "work")

    def test_stop_resets_remaining(self) -> None:
        service = _make_service(work_minutes=20)
        service.start()
        service.stop()
        self.assertEqual(service.remaining, 20 * 60)

    def test_stop_resets_paused(self) -> None:
        service = _make_service()
        service.start()
        service.pause()
        service.stop()
        self.assertFalse(service.paused)


class TestTimerServiceValidation(unittest.TestCase):
    """Проверка валидации настроек."""

    def test_update_settings_rejects_work_too_low(self) -> None:
        service = _make_service()
        result = service.update_settings(0, 5)
        self.assertFalse(result)

    def test_update_settings_rejects_work_too_high(self) -> None:
        service = _make_service()
        result = service.update_settings(241, 5)
        self.assertFalse(result)

    def test_update_settings_rejects_rest_too_low(self) -> None:
        service = _make_service()
        result = service.update_settings(25, 0)
        self.assertFalse(result)

    def test_update_settings_rejects_rest_too_high(self) -> None:
        service = _make_service()
        result = service.update_settings(25, 121)
        self.assertFalse(result)

    def test_update_settings_accepts_valid_values(self) -> None:
        service = _make_service()
        result = service.update_settings(30, 10)
        self.assertTrue(result)
        self.assertEqual(service.settings.work_minutes, 30)
        self.assertEqual(service.settings.rest_minutes, 10)

    def test_update_settings_rejected_when_running(self) -> None:
        service = _make_service()
        service.start()
        result = service.update_settings(30, 10)
        self.assertFalse(result)

    def test_start_with_validation_rejects_invalid(self) -> None:
        service = _make_service()
        result = service.start_with_validation(0, 5)
        self.assertFalse(result)
        self.assertFalse(service.running)

    def test_start_with_validation_accepts_valid(self) -> None:
        service = _make_service()
        result = service.start_with_validation(15, 5)
        self.assertTrue(result)
        self.assertTrue(service.running)

    def test_error_callback_called_on_invalid(self) -> None:
        service = _make_service()
        service.update_settings(0, 5)
        service._on_error.assert_called_once()


class TestTimerServiceTick(unittest.TestCase):
    """Проверка тиков таймера."""

    def test_tick_returns_timer_state(self) -> None:
        service = _make_service()
        state = service.tick()
        self.assertIsInstance(state, TimerState)

    def test_tick_state_not_running_by_default(self) -> None:
        service = _make_service()
        state = service.tick()
        self.assertFalse(state.running)

    def test_tick_state_running_after_start(self) -> None:
        service = _make_service()
        service.start()
        state = service.tick()
        self.assertTrue(state.running)

    def test_tick_decreases_remaining(self) -> None:
        with unittest.mock.patch("timer_service.StatsRepository.save"):
            service = _make_service(work_minutes=1)
            service.start()
            original_remaining = service.remaining
            # Симулируем небольшую задержку (2 секунды)
            service._deadline = time.monotonic() - 2
            # Mock чтобы предотвратить переключение фазы и сохранение
            with unittest.mock.patch.object(service, "_finish_phase"):
                state = service.tick()
            # remaining должен уменьшиться (было 60, стало ~58)
            self.assertLess(state.remaining, original_remaining)
            self.assertAlmostEqual(state.remaining, 58, delta=2)

    def test_tick_state_activity_text_when_ready(self) -> None:
        service = _make_service()
        state = service.tick()
        self.assertEqual(state.activity_text, "ГОТОВ К РАБОТЕ")

    def test_tick_state_activity_text_when_running_work(self) -> None:
        service = _make_service()
        service.start()
        state = service.tick()
        self.assertEqual(state.activity_text, "ВРЕМЯ РАБОТАТЬ")


class TestTimerServicePhaseTransition(unittest.TestCase):
    """Проверка перехода между фазами."""

    def test_finish_phase_work_to_rest(self) -> None:
        service = _make_service()
        service._phase = "work"
        service._finish_phase()
        self.assertEqual(service.phase, "rest")

    def test_finish_phase_rest_to_work(self) -> None:
        service = _make_service()
        service._phase = "rest"
        service._finish_phase()
        self.assertEqual(service.phase, "work")

    def test_finish_phase_increments_cycles(self) -> None:
        service = _make_service()
        service._stats.today()  # Создаём запись
        service._phase = "rest"
        service._finish_phase()
        record = service._stats.today()
        self.assertEqual(record.completed_cycles, 1)

    def test_finish_phase_resets_cycle_seconds(self) -> None:
        service = _make_service()
        service._cycle_work_seconds = 100.0
        service._phase = "rest"
        service._finish_phase()
        self.assertEqual(service._cycle_work_seconds, 0.0)

    def test_finish_phase_triggers_sound(self) -> None:
        service = _make_service()
        service._finish_phase()
        service._on_sound.assert_called_once()


class TestTimerServiceSettingsUpdate(unittest.TestCase):
    """Проверка обновления настроек."""

    def test_update_settings_applies_new_work_time(self) -> None:
        service = _make_service(work_minutes=25)
        service.update_settings(45, 5)
        self.assertEqual(service.settings.work_minutes, 45)

    def test_update_settings_applies_new_rest_time(self) -> None:
        service = _make_service(rest_minutes=5)
        service.update_settings(25, 15)
        self.assertEqual(service.settings.rest_minutes, 15)

    def test_update_settings_updates_remaining(self) -> None:
        service = _make_service(work_minutes=10)
        service.update_settings(20, 5)
        self.assertEqual(service.remaining, 20 * 60)


class TestFormatFunctions(unittest.TestCase):
    """Проверка утилит форматирования."""

    def test_format_minutes_zero(self) -> None:
        from models import format_minutes
        self.assertEqual(format_minutes(0), "0 мин")

    def test_format_minutes_under_hour(self) -> None:
        from models import format_minutes
        self.assertEqual(format_minutes(120), "2 мин")

    def test_format_minutes_exactly_hour(self) -> None:
        from models import format_minutes
        self.assertEqual(format_minutes(3600), "1 ч 0 мин")

    def test_format_minutes_hours_and_mins(self) -> None:
        from models import format_minutes
        self.assertEqual(format_minutes(3750), "1 ч 2 мин")

    def test_format_timer_zero(self) -> None:
        from models import format_timer
        self.assertEqual(format_timer(0), "00:00")

    def test_format_timer_with_seconds(self) -> None:
        from models import format_timer
        self.assertEqual(format_timer(65), "01:05")

    def test_format_timer_rounds_up(self) -> None:
        from models import format_timer
        self.assertEqual(format_timer(65.4), "01:06")


class TestGetWeekData(unittest.TestCase):
    """Проверка получения данных для графика за неделю."""

    def test_week_data_returns_7_entries(self) -> None:
        service = _make_service()
        data = service.get_week_data()
        self.assertEqual(len(data), 7)

    def test_week_data_last_entry_is_today(self) -> None:
        from datetime import date
        service = _make_service()
        data = service.get_week_data()
        _, _, last_day = data[-1]
        self.assertEqual(last_day, date.today())

    def test_week_data_day_names_match_dates(self) -> None:
        from datetime import date, timedelta
        from config import DAY_NAMES_RU

        service = _make_service()
        data = service.get_week_data()

        for idx, (name, _, day_obj) in enumerate(data):
            expected_name = DAY_NAMES_RU[day_obj.weekday()]
            self.assertEqual(name, expected_name,
                             f"Day {idx}: expected {expected_name} for {day_obj}")

    def test_week_data_first_entry_is_6_days_ago(self) -> None:
        from datetime import date, timedelta
        service = _make_service()
        data = service.get_week_data()
        _, _, first_day = data[0]
        expected = date.today() - timedelta(days=6)
        self.assertEqual(first_day, expected)


if __name__ == "__main__":
    unittest.main()
