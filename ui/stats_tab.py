from __future__ import annotations

from datetime import date

import tkinter as tk

from theme import Theme
from timer_service import TimerService


class StatsTab:
    """UI вкладка статистики."""

    def __init__(self, parent: tk.Widget) -> None:
        self._parent = parent
        self._service: TimerService | None = None
        self._last_chart_key: tuple[
            tuple[tuple[str,
                        int,
                        date], ...], int, int
        ] | None = None

        self._build_tab()

    def initialize(self, service: TimerService) -> None:
        self._service = service

    def _build_tab(self) -> None:
        outer = tk.Frame(self._parent, bg=Theme.BG)
        self._outer = outer
        outer.pack(fill="both", expand=True, padx=12, pady=12)

        tk.Label(
            outer, text="Статистика за сегодня", bg=Theme.BG, fg=Theme.TEXT,
            font=("Segoe UI", 19, "bold"),
        ).pack(anchor="w", pady=(0, 4))
        self._date_label = tk.Label(
            outer, text="", bg=Theme.BG, fg=Theme.MUTED,
            font=("Segoe UI", 10),
        )
        self._date_label.pack(anchor="w", pady=(0, 16))

        cards = tk.Frame(outer, bg=Theme.BG)
        cards.pack(fill="x")
        self._cycle_value = self._stat_card(
            cards, "Завершённые циклы", Theme.GREEN, 0
        )
        self._work_value = self._stat_card(
            cards, "Время работы", Theme.BLUE, 1
        )
        self._rest_value = self._stat_card(
            cards, "Время отдыха", Theme.PURPLE, 2
        )

        tk.Label(
            outer, text="Последние 7 дней • завершённые циклы",
            bg=Theme.BG, fg=Theme.TEXT, font=("Segoe UI", 11, "bold"),
        ).pack(anchor="w", pady=(22, 8))

        self._week_chart = tk.Canvas(
            outer, height=190, bg=Theme.PANEL,
            highlightthickness=0, bd=0,
        )
        self._week_chart.pack(fill="both", expand=True)

        tk.Label(
            outer,
            text="Статистика сохраняется автоматически.",
            bg=Theme.BG, fg=Theme.MUTED, wraplength=760, justify="left",
            font=("Segoe UI", 9),
        ).pack(anchor="w", pady=(12, 0))

    def _stat_card(
        self, parent: tk.Widget, title: str, accent: str, column: int
    ) -> tk.Label:
        card = tk.Frame(parent, bg=Theme.PANEL, padx=12, pady=14)
        card.grid(row=0, column=column, sticky="nsew", padx=5)
        parent.grid_columnconfigure(column, weight=1)
        tk.Label(
            card, text=title, bg=Theme.PANEL, fg=Theme.MUTED,
            font=("Segoe UI", 9), wraplength=150,
        ).pack(anchor="w")
        value = tk.Label(
            card, text="0", bg=Theme.PANEL, fg=accent,
            font=("Segoe UI", 21, "bold"),
        )
        value.pack(anchor="w", pady=(8, 0))
        return value

    def update_state(self) -> None:
        """Обновить UI статистики."""
        if self._service is None:
            return

        record = self._service.get_today_stats()
        self._date_label.configure(
            text=f"Дата: {date.today().strftime('%d.%m.%Y')}")
        self._cycle_value.configure(text=str(record.completed_cycles))
        self._work_value.configure(
            text=self._service.format_minutes(record.work_seconds)
        )
        self._rest_value.configure(
            text=self._service.format_minutes(record.rest_seconds)
        )
        week_data = self._service.get_week_data()
        chart_key = (
            tuple(week_data),
            self._week_chart.winfo_width(),
            self._week_chart.winfo_height(),
        )
        if chart_key != self._last_chart_key:
            self._draw_week_chart(week_data)
            self._last_chart_key = chart_key

    def _draw_week_chart(self, week_data: list[tuple[str, int, date]]) -> None:
        canvas = self._week_chart
        canvas.delete("all")
        canvas.update_idletasks()

        width = max(canvas.winfo_width(), 420)
        height = max(canvas.winfo_height(), 170)

        values = [v for _, v, _ in week_data]
        day_names = [n for n, _, _ in week_data]
        days = [d for _, _, d in week_data]

        max_value = max(1, max(values)) if values else 1
        left, right, top, bottom = 35, width - 18, 18, height - 32
        chart_height = bottom - top

        # Grid lines
        for tick in range(4):
            y = bottom - chart_height * tick / 3
            canvas.create_line(left, y, right, y, fill="#3B3E4B")
            canvas.create_text(
                left - 12, y, text=str(round(max_value * tick / 3)),
                fill=Theme.MUTED, font=("Segoe UI", 8), anchor="e",
            )

        # Bars
        slot_width = (right - left) / 7
        bar_width = min(28, slot_width * 0.58)
        today_str = date.today().isoformat()

        for index, (day_name, value) in enumerate(zip(day_names, values)):
            center = left + slot_width * (index + 0.5)
            bar_height = chart_height * value / max_value
            is_today = days[index] == today_str
            color = Theme.CORAL if is_today else "#676B7C"
            canvas.create_rectangle(
                center - bar_width / 2, bottom - bar_height,
                center + bar_width / 2, bottom,
                fill=color, outline="",
            )
            canvas.create_text(
                center, bottom + 15, text=day_name,
                fill=Theme.TEXT, font=("Segoe UI", 8),
            )
            if value:
                canvas.create_text(
                    center, bottom - bar_height - 10, text=str(value),
                    fill=Theme.TEXT, font=("Segoe UI", 8),
                )
