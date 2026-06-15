"""
converter.py
------------
Core temperature conversion engine.
Handles all mathematical conversions, validation, category detection,
and history management. Fully decoupled from the UI layer.

Author  : Yoga Prabu
Project : PRODIGY_SD_01 – ThermoConvert Pro
"""

from __future__ import annotations

import csv
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


# ─────────────────────────────────────────────
#  Data model
# ─────────────────────────────────────────────

@dataclass
class ConversionResult:
    """Immutable snapshot of a single conversion event."""
    input_value: float
    input_unit: str
    celsius: float
    fahrenheit: float
    kelvin: float
    category: str
    emoji: str
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%H:%M:%S"))

    # ── Formatted display helpers ──────────────────────────────────────

    def fmt(self, value: float) -> str:
        """Return a value formatted to 4 decimal places, stripped of trailing zeros."""
        return f"{value:.4f}".rstrip("0").rstrip(".")

    @property
    def summary(self) -> str:
        return (
            f"{self.fmt(self.input_value)} {self.input_unit}  →  "
            f"C: {self.fmt(self.celsius)}°  |  "
            f"F: {self.fmt(self.fahrenheit)}°  |  "
            f"K: {self.fmt(self.kelvin)}"
        )

    @property
    def csv_row(self) -> list:
        return [
            self.timestamp,
            self.input_value,
            self.input_unit,
            round(self.celsius, 4),
            round(self.fahrenheit, 4),
            round(self.kelvin, 4),
            self.category,
        ]


# ─────────────────────────────────────────────
#  Conversion engine
# ─────────────────────────────────────────────

class TemperatureConverter:
    """
    Stateless conversion engine.

    All public methods are class-level utilities so no instantiation
    is required by the UI. History management is handled by
    ConversionHistory.
    """

    # Absolute zero in Celsius – physically meaningful lower bound
    ABSOLUTE_ZERO_C: float = -273.15

    # ── Category thresholds (°C) ─────────────────────────────────────
    CATEGORIES: list[tuple[float, str, str]] = [
        (-273.15, "Absolute Zero",  "⚛️"),
        (-50.0,   "Extreme Cold",   "🧊"),
        (0.0,     "Freezing Point", "❄️"),
        (10.0,    "Cold",           "🌨️"),
        (20.0,    "Moderate",       "🌤️"),
        (30.0,    "Warm",           "☀️"),
        (40.0,    "Hot",            "🔥"),
        (float("inf"), "Extreme Heat", "🌋"),
    ]

    # ── Core maths ───────────────────────────────────────────────────

    @staticmethod
    def celsius_to_fahrenheit(c: float) -> float:
        return (c * 9 / 5) + 32

    @staticmethod
    def celsius_to_kelvin(c: float) -> float:
        return c + 273.15

    @staticmethod
    def fahrenheit_to_celsius(f: float) -> float:
        return (f - 32) * 5 / 9

    @staticmethod
    def fahrenheit_to_kelvin(f: float) -> float:
        return TemperatureConverter.fahrenheit_to_celsius(f) + 273.15

    @staticmethod
    def kelvin_to_celsius(k: float) -> float:
        return k - 273.15

    @staticmethod
    def kelvin_to_fahrenheit(k: float) -> float:
        return TemperatureConverter.celsius_to_fahrenheit(k - 273.15)

    # ── Unified entry point ──────────────────────────────────────────

    @classmethod
    def convert(cls, value: float, from_unit: str) -> ConversionResult:
        """
        Convert *value* from *from_unit* to all three scales.

        Parameters
        ----------
        value     : numeric temperature
        from_unit : "Celsius" | "Fahrenheit" | "Kelvin"

        Returns
        -------
        ConversionResult with all three values pre-populated.

        Raises
        ------
        ValueError  – physically impossible input (below absolute zero).
        """
        unit = from_unit.strip().capitalize()

        # Normalise to Celsius first
        if unit == "Celsius":
            c = value
        elif unit == "Fahrenheit":
            c = cls.fahrenheit_to_celsius(value)
        elif unit == "Kelvin":
            c = cls.kelvin_to_celsius(value)
        else:
            raise ValueError(f"Unknown unit: '{from_unit}'")

        # Physical guard
        if c < cls.ABSOLUTE_ZERO_C - 1e-9:
            raise ValueError(
                f"{value} {unit} is below absolute zero "
                f"({cls.ABSOLUTE_ZERO_C} °C). Please enter a valid temperature."
            )

        f = cls.celsius_to_fahrenheit(c)
        k = cls.celsius_to_kelvin(c)
        cat, emoji = cls._categorise(c)

        return ConversionResult(
            input_value=value,
            input_unit=unit,
            celsius=c,
            fahrenheit=f,
            kelvin=k,
            category=cat,
            emoji=emoji,
        )

    # ── Category detection ───────────────────────────────────────────

    @classmethod
    def _categorise(cls, celsius: float) -> tuple[str, str]:
        """Return (category_label, emoji) for the given Celsius value."""
        for threshold, label, emoji in cls.CATEGORIES:
            if celsius <= threshold:
                return label, emoji
        return "Extreme Heat", "🌋"

    # ── Input validation ─────────────────────────────────────────────

    @staticmethod
    def validate_input(raw: str) -> tuple[bool, Optional[float], str]:
        """
        Validate raw string input.

        Returns
        -------
        (is_valid, parsed_float_or_None, error_message_or_empty)
        """
        raw = raw.strip()
        if not raw:
            return False, None, "Input is empty."
        try:
            value = float(raw)
        except ValueError:
            return False, None, f"'{raw}' is not a valid number."
        if value != value:          # NaN guard
            return False, None, "Not a number (NaN)."
        if abs(value) > 1e15:
            return False, None, "Value is unreasonably large."
        return True, value, ""


# ─────────────────────────────────────────────
#  History manager
# ─────────────────────────────────────────────

class ConversionHistory:
    """
    Maintains an in-memory list of ConversionResult objects and
    provides CSV export functionality.
    """

    CSV_HEADERS = ["Time", "Input Value", "Input Unit",
                   "Celsius", "Fahrenheit", "Kelvin", "Category"]

    def __init__(self, max_entries: int = 200) -> None:
        self._entries: list[ConversionResult] = []
        self._max = max_entries

    # ── Mutation ─────────────────────────────────────────────────────

    def add(self, result: ConversionResult) -> None:
        """Append a result; evict oldest if capacity is exceeded."""
        self._entries.append(result)
        if len(self._entries) > self._max:
            self._entries.pop(0)

    def clear(self) -> None:
        self._entries.clear()

    # ── Queries ──────────────────────────────────────────────────────

    def get_all(self) -> list[ConversionResult]:
        """Return entries newest-first."""
        return list(reversed(self._entries))

    def __len__(self) -> int:
        return len(self._entries)

    # ── Search & Filter ───────────────────────────────────────────────

    def search(self, query: str) -> list[ConversionResult]:
        """
        Case-insensitive substring search across timestamp, unit,
        category, and all numeric values.

        Returns newest-first, filtered list.
        """
        q = query.strip().lower()
        if not q:
            return self.get_all()
        results = []
        for entry in reversed(self._entries):
            haystack = " ".join([
                entry.timestamp,
                entry.input_unit,
                entry.category,
                str(entry.input_value),
                f"{entry.celsius:.4f}",
                f"{entry.fahrenheit:.4f}",
                f"{entry.kelvin:.4f}",
            ]).lower()
            if q in haystack:
                results.append(entry)
        return results

    def filter_by_unit(self, unit: str) -> list[ConversionResult]:
        """Return newest-first entries whose input_unit matches *unit* exactly."""
        if unit == "All":
            return self.get_all()
        return [e for e in reversed(self._entries) if e.input_unit == unit]

    def filter_by_category(self, category: str) -> list[ConversionResult]:
        """Return newest-first entries matching a temperature category."""
        if category == "All":
            return self.get_all()
        return [e for e in reversed(self._entries) if e.category == category]

    # ── Statistics ────────────────────────────────────────────────────

    def statistics(self) -> dict:
        """
        Compute summary statistics over all stored entries.

        Returns a dict with keys:
          total, by_unit, by_category,
          min_celsius, max_celsius, avg_celsius,
          min_fahrenheit, max_fahrenheit, avg_fahrenheit,
          min_kelvin, max_kelvin, avg_kelvin
        """
        if not self._entries:
            return {"total": 0}

        c_vals = [e.celsius    for e in self._entries]
        f_vals = [e.fahrenheit for e in self._entries]
        k_vals = [e.kelvin     for e in self._entries]

        by_unit: dict[str, int] = {}
        by_cat:  dict[str, int] = {}
        for e in self._entries:
            by_unit[e.input_unit] = by_unit.get(e.input_unit, 0) + 1
            by_cat[e.category]    = by_cat.get(e.category,    0) + 1

        n = len(self._entries)
        return {
            "total":           n,
            "by_unit":         by_unit,
            "by_category":     by_cat,
            "min_celsius":     min(c_vals),
            "max_celsius":     max(c_vals),
            "avg_celsius":     sum(c_vals) / n,
            "min_fahrenheit":  min(f_vals),
            "max_fahrenheit":  max(f_vals),
            "avg_fahrenheit":  sum(f_vals) / n,
            "min_kelvin":      min(k_vals),
            "max_kelvin":      max(k_vals),
            "avg_kelvin":      sum(k_vals) / n,
        }

    # ── Export ───────────────────────────────────────────────────────

    def export_csv(self, path: str,
                   entries: Optional[list[ConversionResult]] = None) -> str:
        """
        Write *entries* (or all history if None) to *path* as a CSV file.

        Returns the absolute path written, or raises IOError.
        """
        rows = entries if entries is not None else self._entries
        abs_path = os.path.abspath(path)
        with open(abs_path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow(self.CSV_HEADERS)
            for entry in rows:
                writer.writerow(entry.csv_row)
        return abs_path
