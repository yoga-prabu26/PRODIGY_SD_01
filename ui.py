"""
ui.py
-----
ThermoConvert Pro – complete UI layer.

Layout engine: grid throughout (root → content → left/right columns).
Every row/column that should grow carries an explicit weight.
Panels that should NOT grow have weight=0 and no sticky="ns".

Author  : Yoga Prabu
Project : PRODIGY_SD_01 – ThermoConvert Pro
"""

from __future__ import annotations

import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Optional

from converter import ConversionHistory, ConversionResult, TemperatureConverter


# ─────────────────────────────────────────────────────────────────────
#  Design tokens
# ─────────────────────────────────────────────────────────────────────

class Palette:
    DARK = {
        "bg_primary":    "#0D1117",
        "bg_secondary":  "#161B22",
        "bg_tertiary":   "#21262D",
        "bg_hover":      "#30363D",
        "accent":        "#58A6FF",
        "accent_hover":  "#79BBFF",
        "accent_dim":    "#1F4172",
        "success":       "#3FB950",
        "warning":       "#D29922",
        "danger":        "#F85149",
        "text_primary":  "#E6EDF3",
        "text_secondary":"#8B949E",
        "text_muted":    "#484F58",
        "border":        "#30363D",
    }
    LIGHT = {
        "bg_primary":    "#F0F2F5",
        "bg_secondary":  "#FFFFFF",
        "bg_tertiary":   "#F6F8FA",
        "bg_hover":      "#E8ECF0",
        "accent":        "#0969DA",
        "accent_hover":  "#0550AE",
        "accent_dim":    "#D0E8FF",
        "success":       "#1A7F37",
        "warning":       "#9A6700",
        "danger":        "#CF222E",
        "text_primary":  "#1F2328",
        "text_secondary":"#656D76",
        "text_muted":    "#AFB8C1",
        "border":        "#D0D7DE",
    }


class Fonts:
    LABEL       = ("Segoe UI", 10, "bold")
    BODY        = ("Segoe UI", 10)
    SMALL       = ("Segoe UI", 9)
    BADGE       = ("Segoe UI", 11, "bold")
    RESULT_UNIT = ("Segoe UI", 14)
    # Slightly larger mono for history rows so entries are readable
    MONO_HIST   = ("Cascadia Code", 9) if sys.platform == "win32" else ("Menlo", 9)


# ─────────────────────────────────────────────────────────────────────
#  Re-usable widget primitives
# ─────────────────────────────────────────────────────────────────────

class HoverButton(tk.Button):
    def __init__(self, parent, palette: dict,
                 bg_key="bg_tertiary", hover_key="bg_hover",
                 fg_key="text_primary", **kw):
        self._pal   = palette
        self._bg_k  = bg_key
        self._hov_k = hover_key
        self._fg_k  = fg_key
        super().__init__(
            parent,
            bg=palette[bg_key], fg=palette[fg_key],
            activebackground=palette[hover_key],
            activeforeground=palette[fg_key],
            relief="flat", cursor="hand2", bd=0,
            **kw,
        )
        self.bind("<Enter>", lambda _: self.config(bg=self._pal[self._hov_k]))
        self.bind("<Leave>", lambda _: self.config(bg=self._pal[self._bg_k]))


class AccentButton(HoverButton):
    def __init__(self, parent, palette: dict, **kw):
        super().__init__(parent, palette,
                         bg_key="accent", hover_key="accent_hover",
                         fg_key="bg_primary", **kw)
        self.config(font=("Segoe UI", 10, "bold"))


class SectionCard(tk.Frame):
    """1-px border card.  .inner is the content surface."""
    def __init__(self, parent, palette: dict, key="bg_secondary", **kw):
        super().__init__(parent, bg=palette["border"], bd=0, **kw)
        self._inner = tk.Frame(self, bg=palette[key], bd=0)
        self._inner.pack(fill="both", expand=True, padx=1, pady=1)
        self._key = key

    @property
    def inner(self) -> tk.Frame:
        return self._inner


# ─────────────────────────────────────────────────────────────────────
#  Treeview style helper
# ─────────────────────────────────────────────────────────────────────

def _style_treeview(style: ttk.Style, palette: dict, tag: str) -> None:
    """Apply palette colours to a named ttk.Treeview style."""
    bg  = palette["bg_tertiary"]
    fg  = palette["text_primary"]
    sel = palette["accent_dim"]
    hdr = palette["bg_secondary"]

    style.theme_use("default")
    style.configure(f"{tag}.Treeview",
                    background=bg, foreground=fg, fieldbackground=bg,
                    rowheight=24, borderwidth=0, relief="flat", font=Fonts.BODY)
    style.configure(f"{tag}.Treeview.Heading",
                    background=hdr, foreground=palette["text_secondary"],
                    relief="flat", font=("Segoe UI", 9, "bold"), borderwidth=0)
    style.map(f"{tag}.Treeview",
              background=[("selected", sel)], foreground=[("selected", fg)])
    style.map(f"{tag}.Treeview.Heading",
              background=[("active", palette["bg_hover"])])
    style.configure(f"{tag}.Vertical.TScrollbar",
                    background=hdr, troughcolor=bg,
                    arrowcolor=palette["text_muted"],
                    borderwidth=0, relief="flat")


# ─────────────────────────────────────────────────────────────────────
#  Main application window
# ─────────────────────────────────────────────────────────────────────

class ThermoConvertApp(tk.Tk):
    APP_TITLE   = "ThermoConvert Pro"
    APP_VERSION = "v2.0.0"
    WIN_SIZE    = "1400x900"
    MIN_SIZE    = (1100, 700)

    def __init__(self) -> None:
        super().__init__()
        self._dark_mode          = True
        self._palette            = Palette.DARK.copy()
        self._history            = ConversionHistory()
        self._last_result: Optional[ConversionResult] = None
        self._filtered_entries: list[ConversionResult] = []
        self._stat_labels: dict[str, tk.Label] = {}

        self.title(f"{self.APP_TITLE}  {self.APP_VERSION}")
        self.geometry(self.WIN_SIZE)
        self.minsize(*self.MIN_SIZE)
        self.configure(bg=self._palette["bg_primary"])
        self._style = ttk.Style(self)
        try:
            self.iconbitmap(default="")
        except Exception:
            pass

        self._build_layout()
        self._bind_keyboard()
        self._update_status("Ready — enter a temperature and press Convert  (↵)")

    # ─────────────────────────────────────────────────────────────────
    #  Root grid:  row 0 = navbar (fixed)
    #              row 1 = content (weight=1, fills all vertical space)
    #              row 2 = status bar (fixed)
    # ─────────────────────────────────────────────────────────────────

    def _build_layout(self) -> None:
        p = self._palette

        self.rowconfigure(0, weight=0)
        self.rowconfigure(1, weight=1)
        self.rowconfigure(2, weight=0)
        self.columnconfigure(0, weight=1)

        # ── Navbar ───────────────────────────────────────────────────
        self._nav = tk.Frame(self, bg=p["bg_secondary"], height=54)
        self._nav.grid(row=0, column=0, sticky="ew")
        self._nav.grid_propagate(False)
        self._build_navbar(self._nav)

        # ── Content (left 55 % + right 45 %) ─────────────────────────
        content = tk.Frame(self, bg=p["bg_primary"])
        content.grid(row=1, column=0, sticky="nsew", padx=14, pady=(8, 0))
        content.rowconfigure(0, weight=1)
        content.columnconfigure(0, weight=55)   # left – converter
        content.columnconfigure(1, weight=45)   # right – history / stats

        left = tk.Frame(content, bg=p["bg_primary"])
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        # Left column rows:
        #   0 – input card        (fixed)
        #   1 – result card       (fixed)
        #   2 – reference table   (fixed natural height, NOT weight=1)
        #   3 – spacer row        (weight=1, absorbs all leftover space cleanly)
        left.rowconfigure(0, weight=0)
        left.rowconfigure(1, weight=0)
        left.rowconfigure(2, weight=0)
        left.rowconfigure(3, weight=1)   # invisible spacer row
        left.columnconfigure(0, weight=1)

        right = tk.Frame(content, bg=p["bg_primary"])
        right.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        # Right column rows:
        #   0 – history card   (weight=1, fills remaining space)
        #   1 – stats card     (fixed, always fully visible)
        right.rowconfigure(0, weight=1)
        right.rowconfigure(1, weight=0)
        right.columnconfigure(0, weight=1)

        self._build_converter_panel(left)
        self._build_history_panel(right)

        # ── Status bar ───────────────────────────────────────────────
        self._status_bar = tk.Frame(self, bg=p["bg_secondary"], height=26)
        self._status_bar.grid(row=2, column=0, sticky="ew")
        self._status_bar.grid_propagate(False)
        self._build_status_bar(self._status_bar)

    # ─────────────────────────────────────────────────────────────────
    #  Navbar
    # ─────────────────────────────────────────────────────────────────

    def _build_navbar(self, parent: tk.Frame) -> None:
        p = self._palette

        logo = tk.Frame(parent, bg=p["bg_secondary"])
        logo.pack(side="left", padx=18, pady=8)
        tk.Label(logo, text="🌡", font=("Segoe UI", 18),
                 bg=p["bg_secondary"], fg=p["accent"]).pack(side="left")
        tk.Label(logo, text=f"  {self.APP_TITLE}", font=("Segoe UI", 14, "bold"),
                 bg=p["bg_secondary"], fg=p["text_primary"]).pack(side="left")
        tk.Label(logo, text=f"  {self.APP_VERSION}", font=Fonts.SMALL,
                 bg=p["bg_secondary"], fg=p["text_muted"]).pack(side="left", pady=(4, 0))

        right = tk.Frame(parent, bg=p["bg_secondary"])
        right.pack(side="right", padx=18)

        self._theme_btn = HoverButton(
            right, p, bg_key="bg_tertiary", hover_key="bg_hover",
            text="☀  Light Mode", font=Fonts.SMALL,
            padx=12, pady=4, command=self._toggle_theme)
        self._theme_btn.pack(side="right", padx=4)

        HoverButton(right, p, text="📥  Export CSV", font=Fonts.SMALL,
                    padx=12, pady=4, command=self._export_csv
                    ).pack(side="right", padx=4)

        tk.Label(right,
                 text="⌨  ↵ convert  |  Ctrl+C copy  |  Ctrl+R reset  |  Ctrl+E export",
                 font=Fonts.SMALL, bg=p["bg_secondary"],
                 fg=p["text_muted"]).pack(side="right", padx=16)

    # ─────────────────────────────────────────────────────────────────
    #  Left column: Input card → Result card → Reference table
    # ─────────────────────────────────────────────────────────────────

    def _build_converter_panel(self, parent: tk.Frame) -> None:
        p = self._palette

        # ── Input card (row 0) ───────────────────────────────────────
        input_card = SectionCard(parent, p)
        input_card.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        ic = input_card.inner

        tk.Label(ic, text="Temperature Input", font=Fonts.LABEL,
                 bg=p["bg_secondary"], fg=p["text_secondary"]
                 ).pack(anchor="w", padx=18, pady=(10, 4))

        input_row = tk.Frame(ic, bg=p["bg_secondary"])
        input_row.pack(fill="x", padx=18, pady=(0, 6))

        self._input_var = tk.StringVar()
        self._input_var.trace_add("write", self._on_input_change)
        self._input_entry = tk.Entry(
            input_row, textvariable=self._input_var,
            font=("Segoe UI", 26, "bold"),
            bg=p["bg_tertiary"], fg=p["text_primary"],
            insertbackground=p["accent"], selectbackground=p["accent_dim"],
            relief="flat", bd=0, width=14)
        self._input_entry.pack(side="left", ipady=10, padx=(0, 14))
        self._input_entry.focus()

        unit_frame = tk.Frame(input_row, bg=p["bg_secondary"])
        unit_frame.pack(side="left")
        tk.Label(unit_frame, text="From unit", font=Fonts.SMALL,
                 bg=p["bg_secondary"], fg=p["text_muted"]).pack(anchor="w")
        self._unit_var = tk.StringVar(value="Celsius")
        unit_menu = tk.OptionMenu(unit_frame, self._unit_var,
                                  "Celsius", "Fahrenheit", "Kelvin",
                                  command=lambda _: self._auto_convert())
        unit_menu.config(font=Fonts.BODY, bg=p["bg_tertiary"], fg=p["text_primary"],
                         activebackground=p["bg_hover"], activeforeground=p["text_primary"],
                         relief="flat", bd=0, cursor="hand2", width=11)
        unit_menu["menu"].config(bg=p["bg_tertiary"], fg=p["text_primary"],
                                 activebackground=p["accent_dim"], font=Fonts.BODY)
        unit_menu.pack(anchor="w")

        self._validation_label = tk.Label(ic, text="", font=Fonts.SMALL,
                                          bg=p["bg_secondary"], fg=p["danger"])
        self._validation_label.pack(anchor="w", padx=18, pady=(0, 6))

        btn_row = tk.Frame(ic, bg=p["bg_secondary"])
        btn_row.pack(fill="x", padx=18, pady=(0, 10))
        self._convert_btn = AccentButton(
            btn_row, p, text="  ⚡  Convert  ",
            font=("Segoe UI", 11, "bold"), padx=18, pady=8, command=self.do_convert)
        self._convert_btn.pack(side="left", padx=(0, 8))
        HoverButton(btn_row, p, text="✕  Clear", font=Fonts.BODY,
                    padx=12, pady=8, command=self._clear_input
                    ).pack(side="left", padx=(0, 8))
        HoverButton(btn_row, p, text="↺  Reset All", font=Fonts.BODY,
                    padx=12, pady=8, command=self._reset_all
                    ).pack(side="left", padx=(0, 8))
        self._copy_btn = HoverButton(btn_row, p, text="⎘  Copy",
                                     font=Fonts.BODY, padx=12, pady=8,
                                     command=self._copy_result)
        self._copy_btn.pack(side="left")

        # ── Result card (row 1) ──────────────────────────────────────
        result_card = SectionCard(parent, p)
        result_card.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        rc = result_card.inner

        tk.Label(rc, text="Conversion Results", font=Fonts.LABEL,
                 bg=p["bg_secondary"], fg=p["text_secondary"]
                 ).pack(anchor="w", padx=18, pady=(10, 6))

        tiles_frame = tk.Frame(rc, bg=p["bg_secondary"])
        tiles_frame.pack(fill="x", padx=18, pady=(0, 12))
        tiles_frame.columnconfigure(0, weight=1)
        tiles_frame.columnconfigure(1, weight=1)
        tiles_frame.columnconfigure(2, weight=1)

        self._tiles: dict[str, dict] = {}
        for col, (label, symbol, colour) in enumerate([
            ("Celsius",    "°C", "#58A6FF"),
            ("Fahrenheit", "°F", "#BC8CFF"),
            ("Kelvin",     "K",  "#3FB950"),
        ]):
            tile = tk.Frame(tiles_frame, bg=p["bg_tertiary"])
            tile.grid(row=0, column=col, sticky="nsew",
                      padx=(0, 8 if col < 2 else 0), ipady=8)
            tk.Label(tile, text=label, font=Fonts.SMALL,
                     bg=p["bg_tertiary"], fg=p["text_secondary"]).pack(pady=(6, 0))
            val_lbl = tk.Label(tile, text="—",
                               font=("Segoe UI", 22, "bold"),
                               bg=p["bg_tertiary"], fg=colour)
            val_lbl.pack()
            sym_lbl = tk.Label(tile, text=symbol, font=Fonts.RESULT_UNIT,
                               bg=p["bg_tertiary"], fg=p["text_secondary"])
            sym_lbl.pack(pady=(0, 6))
            self._tiles[label] = {"frame": tile, "val": val_lbl,
                                  "sym": sym_lbl, "colour": colour}

        badge_row = tk.Frame(rc, bg=p["bg_secondary"])
        badge_row.pack(fill="x", padx=18, pady=(0, 10))
        tk.Label(badge_row, text="Category:", font=Fonts.LABEL,
                 bg=p["bg_secondary"], fg=p["text_secondary"]).pack(side="left")
        self._cat_badge = tk.Label(badge_row, text="  ─  ", font=Fonts.BADGE,
                                   bg=p["bg_tertiary"], fg=p["text_primary"],
                                   padx=14, pady=4)
        self._cat_badge.pack(side="left", padx=8)

        # ── Reference table card (row 2) – natural height, NO weight ──
        self._build_reference_card(parent, p)

        # Row 3 is an invisible spacer that absorbs leftover vertical space
        # so the three cards above stay pinned to the top.

    def _build_reference_card(self, parent: tk.Frame, p: dict) -> None:
        """
        Reference-points card placed at grid row 2 of the left column.
        Height is natural (fits its content); the Treeview scrolls internally.
        The card does NOT expand vertically – leftover space goes to row 3.
        """
        ref_card = SectionCard(parent, p)
        # sticky="ew" only – no "ns", no expand in the vertical direction
        ref_card.grid(row=2, column=0, sticky="ew", pady=(0, 8))

        ic = ref_card.inner
        # inner frame: title row 0, treeview row 1
        ic.columnconfigure(0, weight=1)
        ic.rowconfigure(0, weight=0)
        ic.rowconfigure(1, weight=0)   # treeview row also fixed – height set explicitly

        tk.Label(ic, text="Common Reference Points", font=Fonts.LABEL,
                 bg=p["bg_secondary"], fg=p["text_secondary"]
                 ).grid(row=0, column=0, sticky="w", padx=18, pady=(10, 4))

        self._build_reference_treeview(ic, p)

    def _build_reference_treeview(self, parent: tk.Frame, p: dict) -> None:
        """
        Scrollable ttk.Treeview showing 10 reference points.

        The widget is given an explicit height (in rows) so the card sizes
        itself to fit exactly those rows – no blank space beneath.
        Mouse-wheel scrolling is bound locally (enter/leave) so it does not
        interfere with the history listbox.
        """
        _style_treeview(self._style, p, "ref")

        references = [
            ("⚛️  Absolute Zero",   -273.15),
            ("🧊  Nitrogen boils",  -195.79),
            ("❄️  Water Freezes",      0.0),
            ("🌤️  Room Temp",          22.0),
            ("🫀  Human Body",         37.0),
            ("☀️  Desert Day",         50.0),
            ("♨️  Water Boils",       100.0),
            ("🍞  Oven (bake)",       180.0),
            ("🔥  Oven (broil)",      260.0),
            ("🌋  Lava surface",     1000.0),
        ]

        container = tk.Frame(parent, bg=p["bg_secondary"])
        container.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 10))
        container.columnconfigure(0, weight=1)
        container.rowconfigure(0, weight=0)

        vsb = ttk.Scrollbar(container, orient="vertical",
                            style="ref.Vertical.TScrollbar")
        vsb.grid(row=0, column=1, sticky="ns")

        cols = ("name", "celsius", "fahrenheit", "kelvin")
        # height=7 shows 7 rows; remaining rows scroll via vsb
        tree = ttk.Treeview(container, columns=cols, show="headings",
                            style="ref.Treeview", yscrollcommand=vsb.set,
                            selectmode="none", height=7)
        tree.grid(row=0, column=0, sticky="ew")
        vsb.config(command=tree.yview)

        tree.heading("name",       text="Reference Point")
        tree.heading("celsius",    text="Celsius")
        tree.heading("fahrenheit", text="Fahrenheit")
        tree.heading("kelvin",     text="Kelvin")
        tree.column("name",       width=190, minwidth=150, anchor="w",   stretch=True)
        tree.column("celsius",    width=100, minwidth=80,  anchor="center", stretch=True)
        tree.column("fahrenheit", width=100, minwidth=80,  anchor="center", stretch=True)
        tree.column("kelvin",     width=100, minwidth=80,  anchor="center", stretch=True)

        tree.tag_configure("odd",  background=p["bg_tertiary"],  foreground=p["text_primary"])
        tree.tag_configure("even", background=p["bg_secondary"], foreground=p["text_primary"])

        for i, (name, c_val) in enumerate(references):
            f_val = TemperatureConverter.celsius_to_fahrenheit(c_val)
            k_val = TemperatureConverter.celsius_to_kelvin(c_val)
            tree.insert("", "end", tags=("odd" if i % 2 == 0 else "even",), values=(
                name,
                f"{c_val:.2f} °",
                f"{f_val:.2f} °",
                f"{k_val:.2f}",
            ))

        # ── Local mouse-wheel scroll (cursor must be over the widget) ──
        def _on_enter(_):
            tree.bind("<MouseWheel>",
                      lambda e: tree.yview_scroll(int(-1 * (e.delta / 120)), "units"))
            tree.bind("<Button-4>",
                      lambda _: tree.yview_scroll(-1, "units"))
            tree.bind("<Button-5>",
                      lambda _: tree.yview_scroll(1, "units"))

        def _on_leave(_):
            tree.unbind("<MouseWheel>")
            tree.unbind("<Button-4>")
            tree.unbind("<Button-5>")

        tree.bind("<Enter>", _on_enter)
        tree.bind("<Leave>", _on_leave)

    # ─────────────────────────────────────────────────────────────────
    #  Right column: History card (row 0, grows) + Stats card (row 1, fixed)
    # ─────────────────────────────────────────────────────────────────

    def _build_history_panel(self, parent: tk.Frame) -> None:
        p = self._palette

        # ── History card (row 0, stretches vertically) ───────────────
        hist_card = SectionCard(parent, p)
        hist_card.grid(row=0, column=0, sticky="nsew", pady=(0, 8))

        hc = hist_card.inner
        hc.columnconfigure(0, weight=1)
        # rows inside history card:
        #   0 – header            fixed
        #   1 – search bar        fixed
        #   2 – filter row        fixed
        #   3 – listbox           weight=1, grows
        #   4 – hint label        fixed
        #   5 – footer (count + export-selected)  fixed
        hc.rowconfigure(0, weight=0)
        hc.rowconfigure(1, weight=0)
        hc.rowconfigure(2, weight=0)
        hc.rowconfigure(3, weight=1)
        hc.rowconfigure(4, weight=0)
        hc.rowconfigure(5, weight=0)

        # Row 0 – header
        hdr = tk.Frame(hc, bg=p["bg_secondary"])
        hdr.grid(row=0, column=0, sticky="ew", padx=14, pady=(10, 4))
        tk.Label(hdr, text="🕐  Conversion History", font=Fonts.LABEL,
                 bg=p["bg_secondary"], fg=p["text_secondary"]).pack(side="left")
        HoverButton(hdr, p, text="🗑  Clear", font=Fonts.SMALL, padx=8, pady=2,
                    command=self._clear_history_confirm).pack(side="right")

        # Row 1 – search bar
        sf = tk.Frame(hc, bg=p["bg_secondary"])
        sf.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 4))
        tk.Label(sf, text="🔍", font=("Segoe UI", 10),
                 bg=p["bg_secondary"], fg=p["text_muted"]).pack(side="left", padx=(0, 4))
        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._apply_history_filters())
        tk.Entry(sf, textvariable=self._search_var, font=Fonts.SMALL,
                 bg=p["bg_tertiary"], fg=p["text_primary"],
                 insertbackground=p["accent"], relief="flat", bd=0
                 ).pack(side="left", fill="x", expand=True, ipady=5)
        HoverButton(sf, p, text="✕", font=Fonts.SMALL, padx=6, pady=2,
                    command=lambda: self._search_var.set("")
                    ).pack(side="left", padx=(4, 0))

        # Row 2 – filter row
        ff = tk.Frame(hc, bg=p["bg_secondary"])
        ff.grid(row=2, column=0, sticky="ew", padx=14, pady=(0, 6))

        def _make_menu(container, var, choices, label_text, menu_width=9):
            tk.Label(container, text=label_text, font=Fonts.SMALL,
                     bg=p["bg_secondary"], fg=p["text_muted"]).pack(side="left")
            m = tk.OptionMenu(container, var, *choices,
                              command=lambda _: self._apply_history_filters())
            m.config(font=Fonts.SMALL, bg=p["bg_tertiary"], fg=p["text_primary"],
                     activebackground=p["bg_hover"], activeforeground=p["text_primary"],
                     relief="flat", bd=0, cursor="hand2", width=menu_width)
            m["menu"].config(bg=p["bg_tertiary"], fg=p["text_primary"],
                             activebackground=p["accent_dim"], font=Fonts.SMALL)
            m.pack(side="left", padx=(4, 12))

        self._filter_unit_var = tk.StringVar(value="All")
        self._filter_cat_var  = tk.StringVar(value="All")
        _make_menu(ff, self._filter_unit_var,
                   ["All", "Celsius", "Fahrenheit", "Kelvin"], "Unit:", menu_width=9)
        _make_menu(ff, self._filter_cat_var,
                   ["All", "Absolute Zero", "Extreme Cold", "Freezing Point",
                    "Cold", "Moderate", "Warm", "Hot", "Extreme Heat"], "Cat:", menu_width=12)

        # Row 3 – scrollable listbox (grows to fill available height)
        lf = tk.Frame(hc, bg=p["bg_secondary"])
        lf.grid(row=3, column=0, sticky="nsew", padx=14, pady=(0, 4))
        lf.rowconfigure(0, weight=1)
        lf.columnconfigure(0, weight=1)

        vsb = tk.Scrollbar(lf, orient="vertical",
                           bg=p["bg_secondary"], troughcolor=p["bg_tertiary"],
                           relief="flat")
        vsb.grid(row=0, column=1, sticky="ns")

        self._history_list = tk.Listbox(
            lf,
            font=Fonts.MONO_HIST,
            bg=p["bg_tertiary"], fg=p["text_primary"],
            selectbackground=p["accent_dim"], selectforeground=p["text_primary"],
            relief="flat", bd=0, activestyle="none",
            yscrollcommand=vsb.set,
            selectmode="extended",    # Shift / Ctrl multi-select
            height=10,
        )
        self._history_list.grid(row=0, column=0, sticky="nsew")
        vsb.config(command=self._history_list.yview)

        # Mouse-wheel scrolling for history listbox
        def _hist_wheel(event):
            self._history_list.yview_scroll(int(-1 * (event.delta / 120)), "units")
        def _hist_wheel_up(_):
            self._history_list.yview_scroll(-1, "units")
        def _hist_wheel_dn(_):
            self._history_list.yview_scroll(1, "units")
        self._history_list.bind("<MouseWheel>", _hist_wheel)
        self._history_list.bind("<Button-4>",   _hist_wheel_up)
        self._history_list.bind("<Button-5>",   _hist_wheel_dn)

        # Row 4 – hint
        tk.Label(hc, text="Shift / Ctrl+click to multi-select rows",
                 font=("Segoe UI", 8), bg=p["bg_secondary"],
                 fg=p["text_muted"]).grid(row=4, column=0, sticky="w",
                                          padx=14, pady=(2, 0))

        # Row 5 – footer: count label + export-selected button
        foot = tk.Frame(hc, bg=p["bg_secondary"])
        foot.grid(row=5, column=0, sticky="ew", padx=14, pady=(4, 8))
        self._hist_count_lbl = tk.Label(foot, text="0 conversions",
                                        font=Fonts.SMALL, bg=p["bg_secondary"],
                                        fg=p["text_muted"])
        self._hist_count_lbl.pack(side="left")
        HoverButton(foot, p, text="⬇  Export Selected", font=Fonts.SMALL,
                    padx=8, pady=2, command=self._export_selected_csv
                    ).pack(side="right")

        # ── Statistics card (row 1, fixed height – always fully visible) ─
        self._build_stats_card(parent, p)

    def _build_stats_card(self, parent: tk.Frame, p: dict) -> None:
        """
        Session Statistics panel.
        Layout: 4 columns × 2 rows of stat cells for a compact, wide layout.
        Placed at grid row 1 of the right column with weight=0 (fixed height).
        """
        stats_card = SectionCard(parent, p, key="bg_tertiary")
        stats_card.grid(row=1, column=0, sticky="ew", pady=(0, 10))

        sc = stats_card.inner
        sc.columnconfigure(0, weight=1)
        sc.rowconfigure(0, weight=0)
        sc.rowconfigure(1, weight=0)

        # Header
        hdr_row = tk.Frame(sc, bg=p["bg_tertiary"])
        hdr_row.grid(row=0, column=0, sticky="ew", padx=14, pady=(8, 6))
        tk.Label(hdr_row, text="📊  Session Statistics", font=Fonts.LABEL,
                 bg=p["bg_tertiary"], fg=p["text_secondary"]).pack(side="left")

        # 4-column × 2-row grid of stat cells (compact, fits in fixed height)
        grid = tk.Frame(sc, bg=p["bg_tertiary"])
        grid.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 8))
        for c in range(4):
            grid.columnconfigure(c, weight=1)

        self._stat_labels = {}
        # (key, label, row, col)
        stat_defs = [
            ("total",   "Total",      0, 0),
            ("max_c",   "Max  °C",    0, 1),
            ("min_c",   "Min  °C",    0, 2),
            ("avg_c",   "Avg  °C",    0, 3),
            ("by_unit", "By Unit",    1, 0),
            ("max_f",   "Max  °F",    1, 1),
            ("min_f",   "Min  °F",    1, 2),
            ("by_cat",  "Hot/Warm",   1, 3),
        ]

        for key, label, row, col in stat_defs:
            padx_left  = 0 if col == 0 else 3
            padx_right = 3 if col < 3  else 0
            cell = tk.Frame(grid, bg=p["bg_tertiary"],
                            highlightbackground=p["border"],
                            highlightthickness=1)
            cell.grid(row=row, column=col, sticky="ew",
                      padx=(padx_left, padx_right),
                      pady=2, ipady=2)

            tk.Label(cell, text=label, font=("Segoe UI", 8),
                     bg=p["bg_tertiary"], fg=p["text_muted"]
                     ).pack(anchor="w", padx=7, pady=(4, 0))
            val = tk.Label(cell, text="—",
                           font=("Segoe UI", 10, "bold"),
                           bg=p["bg_tertiary"], fg=p["accent"])
            val.pack(anchor="w", padx=7, pady=(0, 4))
            self._stat_labels[key] = val

    # ─────────────────────────────────────────────────────────────────
    #  Status bar
    # ─────────────────────────────────────────────────────────────────

    def _build_status_bar(self, parent: tk.Frame) -> None:
        p = self._palette
        self._status_lbl = tk.Label(parent, text="", font=Fonts.SMALL,
                                    bg=p["bg_secondary"], fg=p["text_secondary"],
                                    anchor="w")
        self._status_lbl.pack(side="left", padx=12, fill="y")
        tk.Label(parent,
                 text=f"ThermoConvert Pro  {self.APP_VERSION}  |  Python {sys.version[:6]}",
                 font=Fonts.SMALL, bg=p["bg_secondary"],
                 fg=p["text_muted"]).pack(side="right", padx=12)

    # ─────────────────────────────────────────────────────────────────
    #  Core logic callbacks
    # ─────────────────────────────────────────────────────────────────

    def _on_input_change(self, *_) -> None:
        raw = self._input_var.get()
        if not raw.strip():
            self._validation_label.config(text="")
            return
        ok, _, err = TemperatureConverter.validate_input(raw)
        if ok:
            self._validation_label.config(text="✔  Valid input",
                                          fg=self._palette["success"])
            self._auto_convert()
        else:
            self._validation_label.config(text=f"✖  {err}",
                                          fg=self._palette["danger"])

    def _auto_convert(self) -> None:
        ok, value, _ = TemperatureConverter.validate_input(self._input_var.get())
        if not ok:
            return
        try:
            self._render_result(
                TemperatureConverter.convert(value, self._unit_var.get()),
                record=False)
        except ValueError:
            pass

    def do_convert(self) -> None:
        raw = self._input_var.get().strip()
        ok, value, err = TemperatureConverter.validate_input(raw)
        if not ok:
            self._update_status(f"⚠  {err}", error=True)
            messagebox.showerror("Invalid Input", err)
            return
        try:
            result = TemperatureConverter.convert(value, self._unit_var.get())
        except ValueError as exc:
            self._update_status(f"⚠  {exc}", error=True)
            messagebox.showerror("Physical Error", str(exc))
            return
        self._render_result(result, record=True)
        r = result
        self._update_status(
            f"✔  {r.fmt(value)} {r.input_unit}  →  "
            f"C: {r.fmt(r.celsius)}°   F: {r.fmt(r.fahrenheit)}°   K: {r.fmt(r.kelvin)}")

    def _render_result(self, result: ConversionResult, record: bool) -> None:
        self._last_result = result

        scale_map = {"Celsius": result.celsius,
                     "Fahrenheit": result.fahrenheit,
                     "Kelvin": result.kelvin}
        for name, tile in self._tiles.items():
            tile["val"].config(text=result.fmt(scale_map[name]))
            is_src = (name == result.input_unit)
            bg = self._palette["accent_dim"] if is_src else self._palette["bg_tertiary"]
            tile["frame"].config(bg=bg)
            tile["val"].config(bg=bg)
            tile["sym"].config(bg=bg)

        cat_colours = {
            "Absolute Zero":  ("#8250DF", "#FFFFFF"),
            "Extreme Cold":   ("#58A6FF", "#0D1117"),
            "Freezing Point": ("#79C0FF", "#0D1117"),
            "Cold":           ("#3FB950", "#0D1117"),
            "Moderate":       ("#D29922", "#0D1117"),
            "Warm":           ("#F0883E", "#0D1117"),
            "Hot":            ("#F85149", "#FFFFFF"),
            "Extreme Heat":   ("#FF7B72", "#FFFFFF"),
        }
        bg, fg = cat_colours.get(result.category, ("#484F58", "#FFFFFF"))
        self._cat_badge.config(text=f"  {result.emoji}  {result.category}  ",
                               bg=bg, fg=fg)
        self._pulse_tiles()

        if record:
            self._history.add(result)
            self._refresh_history_list()

    def _pulse_tiles(self) -> None:
        steps = 6
        orig  = self._palette["bg_tertiary"]
        flash = self._palette["accent_dim"]
        src   = self._last_result.input_unit if self._last_result else ""

        def step(n: int) -> None:
            if n == 0:
                return
            colour = flash if n % 2 == 0 else orig
            for name, tile in self._tiles.items():
                if name != src:
                    tile["val"].config(bg=colour)
            self.after(60, lambda: step(n - 1))

        step(steps)

    def _refresh_history_list(self) -> None:
        self._apply_history_filters()
        self._update_stats()

    # ─────────────────────────────────────────────────────────────────
    #  Button / action handlers
    # ─────────────────────────────────────────────────────────────────

    def _clear_input(self) -> None:
        self._input_var.set("")
        self._validation_label.config(text="")
        self._input_entry.focus()
        self._update_status("Input cleared.")

    def _reset_all(self) -> None:
        self._clear_input()
        self._unit_var.set("Celsius")
        self._last_result = None
        for tile in self._tiles.values():
            for k in ("frame", "val", "sym"):
                tile[k].config(bg=self._palette["bg_tertiary"])
            tile["val"].config(text="—")
        self._cat_badge.config(text="  ─  ",
                               bg=self._palette["bg_tertiary"],
                               fg=self._palette["text_primary"])
        self._update_status("Reset — all fields cleared.")

    def _copy_result(self) -> None:
        if not self._last_result:
            self._update_status("Nothing to copy — convert first.", error=True)
            return
        r = self._last_result
        self.clipboard_clear()
        self.clipboard_append(
            f"Celsius: {r.fmt(r.celsius)}°  |  "
            f"Fahrenheit: {r.fmt(r.fahrenheit)}°  |  "
            f"Kelvin: {r.fmt(r.kelvin)}  |  Category: {r.category}")
        self._update_status("✔  Result copied to clipboard.")
        self._copy_btn.config(text="✔  Copied!", fg=self._palette["success"])
        self.after(1500, lambda: self._copy_btn.config(
            text="⎘  Copy", fg=self._palette["text_primary"]))

    def _clear_history_confirm(self) -> None:
        if len(self._history) == 0:
            self._update_status("History is already empty.")
            return
        if messagebox.askyesno(
            "Clear History",
            f"Delete all {len(self._history)} conversion records?\n\nThis cannot be undone.",
            icon="warning",
        ):
            self._history.clear()
            self._filtered_entries = []
            self._refresh_history_list()
            self._update_stats()
            self._update_status("History cleared.")

    # Alias so Ctrl+L shortcut still works
    def _clear_history(self) -> None:
        self._clear_history_confirm()

    def _export_csv(self) -> None:
        if len(self._history) == 0:
            messagebox.showinfo("Export", "No history to export yet.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile="thermoconvert_history.csv",
            title="Export Full Conversion History",
        )
        if not path:
            return
        try:
            saved = self._history.export_csv(path)
            self._update_status(f"✔  Exported {len(self._history)} records → {saved}")
            messagebox.showinfo("Export Successful",
                                f"All {len(self._history)} records exported to:\n{saved}")
        except Exception as exc:
            messagebox.showerror("Export Failed", str(exc))

    def _export_selected_csv(self) -> None:
        indices = self._history_list.curselection()
        if not indices:
            messagebox.showinfo("Export Selected",
                                "No rows selected.\n\n"
                                "Use Shift+click or Ctrl+click to select rows.")
            return
        selected = [self._filtered_entries[i] for i in indices
                    if i < len(self._filtered_entries)]
        if not selected:
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=f"thermoconvert_selected_{len(selected)}.csv",
            title=f"Export {len(selected)} Selected Records",
        )
        if not path:
            return
        try:
            saved = self._history.export_csv(path, entries=selected)
            self._update_status(
                f"✔  Exported {len(selected)} selected records → {saved}")
            messagebox.showinfo("Export Successful",
                                f"{len(selected)} selected records exported to:\n{saved}")
        except Exception as exc:
            messagebox.showerror("Export Failed", str(exc))

    # ─────────────────────────────────────────────────────────────────
    #  Search / filter / statistics helpers
    # ─────────────────────────────────────────────────────────────────

    def _apply_history_filters(self) -> None:
        query = self._search_var.get()     if hasattr(self, "_search_var")     else ""
        unit  = self._filter_unit_var.get() if hasattr(self, "_filter_unit_var") else "All"
        cat   = self._filter_cat_var.get()  if hasattr(self, "_filter_cat_var")  else "All"

        entries = self._history.get_all()   # newest-first

        if unit != "All":
            entries = [e for e in entries if e.input_unit == unit]
        if cat != "All":
            entries = [e for e in entries if e.category == cat]
        if query.strip():
            q = query.strip().lower()
            entries = [e for e in entries if q in " ".join([
                e.timestamp, e.input_unit, e.category, str(e.input_value),
                f"{e.celsius:.4f}", f"{e.fahrenheit:.4f}", f"{e.kelvin:.4f}",
            ]).lower()]

        self._filtered_entries = entries
        self._history_list.delete(0, "end")
        for entry in entries:
            self._history_list.insert(
                "end",
                f"  {entry.timestamp}  {entry.emoji}  {entry.summary}")

        total = len(self._history)
        shown = len(entries)
        self._hist_count_lbl.config(
            text=f"{shown} shown / {total} total"
            if shown != total
            else f"{total} conversion{'s' if total != 1 else ''}")

    def _update_stats(self) -> None:
        if not self._stat_labels:
            return
        s = self._history.statistics()
        if s.get("total", 0) == 0:
            for lbl in self._stat_labels.values():
                lbl.config(text="—")
            return

        def fmt(v: float) -> str:
            return f"{v:.2f}"

        hot_warm = sum(s["by_category"].get(k, 0)
                       for k in ("Hot", "Warm", "Extreme Heat"))
        unit_str = "  ".join(f"{k[0]}:{v}" for k, v in s["by_unit"].items())

        updates = {
            "total":   str(s["total"]),
            "max_c":   fmt(s["max_celsius"]),
            "min_c":   fmt(s["min_celsius"]),
            "avg_c":   fmt(s["avg_celsius"]),
            "max_f":   fmt(s["max_fahrenheit"]),
            "min_f":   fmt(s["min_fahrenheit"]),
            "by_unit": unit_str or "—",
            "by_cat":  str(hot_warm),
        }
        for key, text in updates.items():
            self._stat_labels[key].config(text=text)

    # ─────────────────────────────────────────────────────────────────
    #  Theme toggle – full rebuild preserves all grid weights
    # ─────────────────────────────────────────────────────────────────

    def _toggle_theme(self) -> None:
        self._dark_mode = not self._dark_mode
        self._palette = Palette.DARK.copy() if self._dark_mode else Palette.LIGHT.copy()
        for widget in self.winfo_children():
            widget.destroy()
        self.configure(bg=self._palette["bg_primary"])
        self._build_layout()
        if self._last_result:
            self._render_result(self._last_result, record=False)
        self._refresh_history_list()
        self._update_status(
            f"Theme switched to {'dark' if self._dark_mode else 'light'} mode.")

    # ─────────────────────────────────────────────────────────────────
    #  Status helper
    # ─────────────────────────────────────────────────────────────────

    def _update_status(self, msg: str, error: bool = False) -> None:
        colour = self._palette["danger"] if error else self._palette["text_secondary"]
        self._status_lbl.config(text=f"  {msg}", fg=colour)

    # ─────────────────────────────────────────────────────────────────
    #  Keyboard shortcuts
    # ─────────────────────────────────────────────────────────────────

    def _bind_keyboard(self) -> None:
        self.bind("<Return>",    lambda _: self.do_convert())
        self.bind("<KP_Enter>",  lambda _: self.do_convert())
        self.bind("<Control-c>", lambda _: self._copy_result())
        self.bind("<Control-r>", lambda _: self._reset_all())
        self.bind("<Control-e>", lambda _: self._export_csv())
        self.bind("<Escape>",    lambda _: self._clear_input())
        self.bind("<Control-l>", lambda _: self._clear_history())
        self.bind("<Control-t>", lambda _: self._toggle_theme())
