"""Главное окно приложения."""

from __future__ import annotations

import sys
import tkinter as tk
from tkinter import ttk

from models import Settings, Stats
from theme import Styles, Theme
from timer_service import TimerService
from ui.stats_tab import StatsTab
from ui.timer_tab import TimerTab

from config import APP_TITLE, WINDOW_HEIGHT, WINDOW_MIN_HEIGHT, WINDOW_MIN_WIDTH, WINDOW_WIDTH


class MainWindow:
    """Главное окно приложения с вкладками."""

    def __init__(self, settings: Settings, stats: Stats) -> None:
        self._root = tk.Tk()
        self._root.title(APP_TITLE)
        self._root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self._root.minsize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        self._root.configure(bg=Theme.BG)

        self._settings = settings
        self._stats = stats
        self._timer_service: TimerService | None = None

        self._setup_styles()
        self._build_ui()

    @property
    def root(self) -> tk.Tk:
        return self._root

    @property
    def timer_service(self) -> TimerService:
        if self._timer_service is None:
            raise RuntimeError("TimerService not initialized")
        return self._timer_service

    def _setup_styles(self) -> None:
        style = ttk.Style()
        Styles.apply(style)

    def _build_ui(self) -> None:
        self._build_header()

        self._notebook = ttk.Notebook(self.root)
        self._notebook.pack(fill="both", expand=True, padx=20, pady=5)

        self._timer_tab = TimerTab(self._notebook)
        self._stats_tab = StatsTab(self._notebook)

        self._notebook.add(self._timer_tab._outer, text="⏱  Таймер")
        self._notebook.add(self._stats_tab._outer, text="▥  Статистика")

        self._footer_label = tk.Label(
            self.root, text="✓ Готов к работе",
            bg=Theme.BG, fg=Theme.GREEN, anchor="w",
            font=("Segoe UI", 9),
        )
        self._footer_label.pack(fill="x", padx=26, pady=(4, 12))

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_header(self) -> None:
        header = tk.Frame(self.root, bg=Theme.BG)
        header.pack(fill="x", padx=24, pady=(18, 10))

        tk.Label(
            header, text="\U0001f345", bg=Theme.BG, fg=Theme.CORAL,
            font=("Segoe UI Emoji", 24),
        ).pack(side="left", padx=(0, 10))
        tk.Label(
            header, text="Таймер активности", bg=Theme.BG, fg=Theme.TEXT,
            font=("Segoe UI", 20, "bold"),
        ).pack(side="left")
        tk.Label(
            header, text="\u201cФокус \u2022 Результат \u2022 Баланс\u201d",
            bg=Theme.BG, fg=Theme.MUTED, font=("Segoe UI", 10),
        ).pack(side="right", pady=(8, 0))

    def initialize(self) -> None:
        """Инициализировать TimerService и привязать UI."""
        self._timer_service = TimerService(
            settings=self._settings,
            stats=self._stats,
            on_notification=self._on_notification,
            on_sound=self._play_sound,
            on_error=self._on_error,
        )

        self._timer_tab.initialize(self._timer_service, self._footer_label)
        self._stats_tab.initialize(self._timer_service)

        self._start_tick_loop()

    def _start_tick_loop(self) -> None:
        """Запустить цикл обновлений таймера."""
        if self._timer_service is None:
            return
        state = self._timer_service.tick()
        self._timer_tab.update_state(state)
        self._stats_tab.update_state(state)
        self.root.after(150, self._start_tick_loop)

    def _on_notification(self, message: str, color: str) -> None:
        self._footer_label.configure(text=message, fg=color)

    def _on_error(self, message: str) -> None:
        messagebox.showerror("Ошибка настроек", message)

    def _play_sound(self) -> None:
        try:
            if sys.platform == "win32":
                import winsound
                winsound.MessageBeep(winsound.MB_OK)
            else:
                self.root.bell()
        except Exception:
            pass

    def _on_close(self) -> None:
        if self._timer_service:
            self._timer_service.stop()
        self.root.destroy()

    def mainloop(self) -> None:
        self.root.mainloop()
