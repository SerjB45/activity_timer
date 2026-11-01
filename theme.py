"""Темы и стили приложения."""

import tkinter as tk
from tkinter import ttk


class Theme:
    """Цветовая палитра приложения."""

    BG = "#171820"
    PANEL = "#242631"
    PANEL_ALT = "#2D303D"
    TEXT = "#F5F6FA"
    MUTED = "#AEB4C8"
    CORAL = "#FF625F"
    CORAL_DARK = "#E94C50"
    GREEN = "#39B980"
    BLUE = "#5795F5"
    PURPLE = "#9A6BE8"


class Styles:
    """Настройка ttk-стилей."""

    @staticmethod
    def apply(style: ttk.Style) -> None:
        """Применить все стили приложения."""
        Styles._set_theme(style)
        Styles._setup_notebook(style)
        Styles._setup_spinbox(style)

    @staticmethod
    def _set_theme(style: ttk.Style) -> None:
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

    @staticmethod
    def _setup_notebook(style: ttk.Style) -> None:
        style.configure(
            "TNotebook",
            background=Theme.BG,
            borderwidth=0,
        )
        style.configure(
            "TNotebook.Tab",
            background=Theme.PANEL,
            foreground=Theme.MUTED,
            padding=(18, 10),
            font=("Segoe UI", 10, "bold"),
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", Theme.CORAL)],
            foreground=[("selected", "#FFFFFF")],
        )

    @staticmethod
    def _setup_spinbox(style: ttk.Style) -> None:
        style.configure(
            "TSpinbox",
            fieldbackground=Theme.PANEL_ALT,
            background=Theme.PANEL_ALT,
            foreground=Theme.TEXT,
            arrowcolor=Theme.TEXT,
            bordercolor=Theme.PANEL_ALT,
            padding=6,
        )
