from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from models import TimerState
from theme import Theme
from timer_service import TimerService

from config import (
    MAX_WORK_MINUTES, MAX_REST_MINUTES, MIN_WORK_MINUTES, MIN_REST_MINUTES
)


class TimerTab:
    """UI вкладка таймера."""

    def __init__(self, parent: tk.Widget) -> None:
        self._parent = parent
        self._service: TimerService | None = None
        self._footer_label: tk.Label | None = None

        self._build_tab()

    def initialize(
        self, service: TimerService, footer_label: tk.Label
    ) -> None:
        self._service = service
        self._footer_label = footer_label
        self._refresh_settings_ui()
        self._set_settings_enabled(True)

    def _build_tab(self) -> None:
        outer = tk.Frame(self._parent, bg=Theme.BG)
        self._outer = outer
        outer.pack(fill="both", expand=True, padx=10, pady=10)

        # ---------- Settings card ----------
        settings_card = tk.Frame(outer, bg=Theme.PANEL, padx=18, pady=14)
        settings_card.pack(fill="x", pady=(0, 14))

        work_box = tk.Frame(settings_card, bg=Theme.PANEL)
        work_box.pack(side="left", expand=True, fill="x")
        tk.Label(
            work_box, text="\u25c0  РАБОТА", bg=Theme.PANEL, fg=Theme.CORAL,
            font=("Segoe UI", 10, "bold"),
        ).pack(anchor="w")
        self._work_var = tk.IntVar(value=25)
        self._work_spin = ttk.Spinbox(
            work_box, from_=MIN_WORK_MINUTES, to=MAX_WORK_MINUTES, width=6,
            textvariable=self._work_var, justify="center",
            command=self._on_settings_change,
        )
        self._work_spin.pack(anchor="w", pady=(6, 0))
        self._work_spin.bind("<FocusOut>", self._on_settings_change)
        self._work_spin.bind("<Return>", self._on_settings_change)

        divider = tk.Frame(settings_card, bg="#454856", width=1)
        divider.pack(side="left", fill="y", padx=22)

        rest_box = tk.Frame(settings_card, bg=Theme.PANEL)
        rest_box.pack(side="left", expand=True, fill="x")
        tk.Label(
            rest_box, text="\u2615  ОТДЫХ", bg=Theme.PANEL, fg=Theme.BLUE,
            font=("Segoe UI", 10, "bold"),
        ).pack(anchor="w")
        self._rest_var = tk.IntVar(value=5)
        self._rest_spin = ttk.Spinbox(
            rest_box, from_=MIN_REST_MINUTES, to=MAX_REST_MINUTES, width=6,
            textvariable=self._rest_var, justify="center",
            command=self._on_settings_change,
        )
        self._rest_spin.pack(anchor="w", pady=(6, 0))
        self._rest_spin.bind("<FocusOut>", self._on_settings_change)
        self._rest_spin.bind("<Return>", self._on_settings_change)

        # ---------- Timer display ----------
        self._activity_label = tk.Label(
            outer, text="ГОТОВ К РАБОТЕ", bg=Theme.BG, fg=Theme.MUTED,
            font=("Segoe UI", 11, "bold"),
        )
        self._activity_label.pack(pady=(5, 0))

        self._timer_label = tk.Label(
            outer, text="25:00", bg=Theme.BG, fg=Theme.TEXT,
            font=("Segoe UI", 54, "bold"),
        )
        self._timer_label.pack(pady=(0, 2))

        self._progress = tk.Canvas(
            outer, width=340, height=14, bg=Theme.BG,
            highlightthickness=0, bd=0,
        )
        self._progress.pack(pady=(0, 12))

        self._phase_detail = tk.Label(
            outer, text="Настрой время и нажми «Старт»",
            bg=Theme.BG, fg=Theme.MUTED, font=("Segoe UI", 10),
        )
        self._phase_detail.pack(pady=(0, 14))

        # ---------- Buttons ----------
        buttons = tk.Frame(outer, bg=Theme.BG)
        buttons.pack()

        self._start_button = tk.Button(
            buttons, text="\u25b6  Старт", command=self._on_start,
            bg=Theme.GREEN, fg="#FFFFFF", activebackground="#2AA56E",
            activeforeground="#FFFFFF", relief="flat", bd=0,
            font=("Segoe UI", 11, "bold"), padx=22, pady=11,
            cursor="hand2",
        )
        self._start_button.pack(side="left", padx=5)

        self._pause_button = tk.Button(
            buttons, text="\u2062  Пауза", command=self._on_pause_resume,
            bg=Theme.PANEL_ALT, fg=Theme.TEXT, activebackground="#3A3D4B",
            activeforeground=Theme.TEXT, relief="flat", bd=0,
            font=("Segoe UI", 11, "bold"), padx=22, pady=11,
            cursor="hand2", state="disabled",
        )
        self._pause_button.pack(side="left", padx=5)

        self._stop_button = tk.Button(
            buttons, text="\u25a0  Стоп", command=self._on_stop,
            bg=Theme.CORAL_DARK, fg="#FFFFFF", activebackground=Theme.CORAL,
            activeforeground="#FFFFFF", relief="flat", bd=0,
            font=("Segoe UI", 11, "bold"), padx=22, pady=11,
            cursor="hand2",
        )
        self._stop_button.pack(side="left", padx=5)

        # ---------- Summary ----------
        summary = tk.Frame(outer, bg=Theme.PANEL, padx=18, pady=12)
        summary.pack(fill="x", pady=(18, 0))
        self._cycle_label = tk.Label(
            summary, text="Текущий цикл: работа",
            bg=Theme.PANEL, fg=Theme.TEXT, font=("Segoe UI", 10, "bold"),
        )
        self._cycle_label.pack(side="left")
        self._today_cycle_label = tk.Label(
            summary, text="Сегодня завершено: 0",
            bg=Theme.PANEL, fg=Theme.MUTED, font=("Segoe UI", 10),
        )
        self._today_cycle_label.pack(side="right")

    def _refresh_settings_ui(self) -> None:
        if self._service:
            self._work_var.set(self._service.settings.work_minutes)
            self._rest_var.set(self._service.settings.rest_minutes)

    def _set_settings_enabled(self, enabled: bool) -> None:
        state = "normal" if enabled else "disabled"
        self._work_spin.configure(state=state)
        self._rest_spin.configure(state=state)

    def _read_settings(self) -> tuple[int, int] | None:
        """Прочитать значения из UI."""
        try:
            work = int(self._work_var.get())
            rest = int(self._rest_var.get())
            return work, rest
        except (ValueError, tk.TclError):
            messagebox.showerror("Ошибка", "Введите целое число минут.")
            return None

    def _on_settings_change(self, _event=None) -> None:
        if self._service and not self._service.running:
            values = self._read_settings()
            if values is not None:
                work, rest = values
                self._service.update_settings(work, rest)

    def _on_start(self) -> None:
        if self._service is None:
            return
        if self._service.running:
            return

        values = self._read_settings()
        if values is None:
            return

        work, rest = values
        success = self._service.start_with_validation(work, rest)
        if success:
            self._set_settings_enabled(False)
            self._start_button.configure(state="disabled")
            self._pause_button.configure(state="normal", text="\u2062  Пауза")
            if self._footer_label:
                self._footer_label.configure(
                    text="● Таймер запущен", fg=Theme.GREEN)

    def _on_pause_resume(self) -> None:
        if self._service is None:
            return
        if not self._service.running:
            return

        if not self._service.paused:
            self._service.pause()
            self._pause_button.configure(text="\u25b6  Продолжить")
            if self._footer_label:
                self._footer_label.configure(
                    text="Ⅱ Таймер на паузе", fg=Theme.BLUE)
        else:
            self._service.resume()
            self._pause_button.configure(text="\u2062  Пауза")
            if self._footer_label:
                self._footer_label.configure(
                    text="● Таймер запущен", fg=Theme.GREEN)

    def _on_stop(self) -> None:
        if self._service:
            self._service.stop()
            self._set_settings_enabled(True)
            self._start_button.configure(state="normal")
            self._pause_button.configure(
                state="disabled", text="\u2062  Пауза")
            if self._footer_label:
                self._footer_label.configure(
                    text="✓ Таймер сброшен; статистика сохранена",
                    fg=Theme.GREEN
                )

    def update_state(self, state: TimerState) -> None:
        """Обновить UI по состоянию таймера."""
        # Activity label
        if state.phase == "work":
            color = Theme.CORAL
        else:
            color = Theme.BLUE

        if not state.running:
            color = Theme.MUTED
        elif state.paused:
            color = Theme.BLUE

        self._activity_label.configure(text=state.activity_text, fg=color)
        self._timer_label.configure(
            text=(
                self._service.get_formatted_timer()
                if self._service
                else "00:00"
            )
        )
        self._phase_detail.configure(text=state.detail_text)

        # Progress bar
        self._update_progress(state.progress_fraction, color)

        # Cycle info
        self._cycle_label.configure(text=state.cycle_label)
        self._today_cycle_label.configure(
            text=f"Сегодня завершено: {state.today_cycles}"
        )

    def _update_progress(self, fraction: float, color: str) -> None:
        self._progress.delete("all")
        width = max(self._progress.winfo_width(), 340)
        self._progress.create_rectangle(
            0, 3, width, 11, fill=Theme.PANEL_ALT, outline="")
        self._progress.create_rectangle(
            0, 3, width * fraction, 11, fill=color, outline=""
        )
