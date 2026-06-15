# 🌡 ThermoConvert Pro

<div align="center">

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=for-the-badge&logo=python&logoColor=white)
![Tkinter](https://img.shields.io/badge/Tkinter-GUI-orange?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen?style=for-the-badge)

**A production-quality temperature conversion utility built with Python & Tkinter.**  
*Professional Temperature Conversion & Analytics Utility*

[Features](#-features) · [Screenshots](#-screenshots) · [Installation](#-installation) · [Usage](#-usage) · [Architecture](#-architecture) · [Author](#-author)

</div>

---

## 📌 Overview

ThermoConvert Pro is a **professional desktop application** that converts temperatures across Celsius, Fahrenheit, and Kelvin with real-time validation, intelligent category detection, full conversion history, and a polished dark/light theme UI.

Designed as a portfolio-grade software engineering project, ThermoConvert Pro demonstrates production-level Python development practices including clean OOP architecture, modular file structure, PEP 8 compliance, and a polished modern user experience.
---

## ✨ Features

### Core Conversion Engine
| Feature | Details |
|---|---|
| **Tri-directional conversion** | C → F & K, F → C & K, K → C & F |
| **Physical validation** | Rejects values below absolute zero (−273.15 °C) |
| **Real-time feedback** | Live input validation on every keystroke |
| **Precision output** | Results displayed to 4 significant decimal places |

### Advanced UI Features
| Feature | Details |
|---|---|
| **Dark / Light theme** | Toggle at any time; full palette swap instantly |
| **Animated result tiles** | Pulse flash on every new conversion |
| **Source-unit highlighting** | Active unit tile glows in accent blue |
| **Temperature category badge** | Colour-coded: Absolute Zero → Extreme Heat |
| **Conversion history panel** | Scrollable, timestamped, up to 200 entries |
| **Export to CSV** | One-click export of full session history |
| **Reference comparison table** | Six real-world reference points always visible |
| **Copy to clipboard** | One-click result copy with visual confirmation |
| **Status bar** | Live feedback on every action |
| **Search history** | Live substring search across all fields |
| **Filter by unit** | Show only Celsius / Fahrenheit / Kelvin inputs |
| **Filter by category** | Show only a specific thermal category |
| **Export selected** | Highlight rows and export just those records |
| **Statistics panel** | Min / max / avg per scale, count by unit & category |
| **Confirmation dialog** | Asks before clearing history |

### Keyboard Shortcuts
| Shortcut | Action |
|---|---|
| `Enter` / `↵` | Convert |
| `Ctrl + C` | Copy result |
| `Ctrl + R` | Reset all fields |
| `Ctrl + E` | Export history to CSV |
| `Ctrl + T` | Toggle dark/light theme |
| `Ctrl + L` | Clear history |
| `Escape` | Clear input |

---

## 📸 Screenshots

> Screenshots are located in the `/screenshots` folder.

| Dark Theme | Light Theme |
|---|---|
| *(run the app and press Ctrl+T to switch)* | *(run the app and press Ctrl+T to switch)* |

---

## 🛠 Technologies Used

| Technology | Purpose |
|---|---|
| **Python 3.8+** | Core language |
| **Tkinter** | GUI framework (stdlib) |
| **CustomTkinter** *(optional)* | Enhanced widget theming |
| **dataclasses** | Clean data modelling (`ConversionResult`) |
| **csv module** | History export |
| **OOP / SOLID principles** | Modular, maintainable architecture |

---

## 📁 Project Structure

```
PRODIGY_SD_01/
│
├── main.py          # Entry point — bootstraps and centres the window
├── converter.py     # Business logic: math, validation, history, data models
├── ui.py            # All UI components, event handlers, keyboard bindings
│
├── assets/          # Icon and image assets (extendable)
├── screenshots/     # App screenshots for README / portfolio
│
├── README.md        # This file
├── requirements.txt # Python dependencies
└── LICENSE          # MIT License
```

**Separation of concerns:**
- `converter.py` has **zero UI imports** — fully testable in isolation
- `ui.py` delegates all math and validation to `converter.py`
- `main.py` is a pure bootstrap — no business logic, no widgets

---

## ⚙ Installation

### Prerequisites
- Python 3.8 or higher
- pip

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/YogaPrabu/PRODIGY_SD_01.git
cd PRODIGY_SD_01

# 2. (Optional but recommended) Create a virtual environment
python -m venv venv
source venv/bin/activate        # Linux / macOS
venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the application
python main.py
```

> **Tkinter** ships with the standard Python installer on Windows and macOS.  
> On Ubuntu/Debian: `sudo apt-get install python3-tk`

---

## 🚀 Usage

1. **Enter a temperature** in the input field (supports decimals and negatives)
2. **Select the source unit** from the dropdown (Celsius / Fahrenheit / Kelvin)
3. Press **Convert** (or just `Enter`) — results appear instantly in the three tiles
4. The **Category badge** colour-codes the thermal range (e.g. "🔥 Hot" for > 30 °C)
5. Use the **History panel** on the right to review past conversions
6. Click **Export CSV** in the toolbar to save your session history
7. Toggle **Light Mode** from the top-right to switch themes

---

## 🏗 Architecture

```
ThermoConvertApp (tk.Tk)          ← root window, owns theme state
│
├── Navbar                        ← logo, theme toggle, export, shortcuts hint
├── Left Panel
│   ├── Input Card                ← entry, unit selector, validation, action buttons
│   ├── Result Card               ← three animated tiles (C / F / K) + category badge
│   └── Comparison Card          ← six real-world reference points
└── Right Panel
    └── History Card              ← scrollable listbox + count + clear button

converter.py (zero UI dependency)
├── TemperatureConverter          ← stateless math & physical validation
├── ConversionResult              ← immutable dataclass for one conversion event
└── ConversionHistory             ← append-only list, CSV export
```

---

## 🔮 Future Enhancements

- [ ] **Plot panel** — temperature trend graph via matplotlib for session history
- [ ] **Unit calculator** — extend to other measurement systems (length, weight)
- [ ] **Settings persistence** — remember theme and preferred unit via JSON config
- [ ] **Locale support** — comma vs dot decimal separator
- [ ] **System tray mode** — quick-convert from the menu bar
- [ ] **REST API backend** — expose conversion as a microservice
- [ ] **Auto-update checker** — GitHub Releases integration

---

## 👨‍💻 Author

**Yoga Prabu**  
B.Tech Computer Science & Business Systems  
Python Developer & Software Engineering Enthusiast

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-blue?style=flat&logo=linkedin)](https://linkedin.com/in/yogaprabu)
[![GitHub](https://img.shields.io/badge/GitHub-Follow-black?style=flat&logo=github)](https://github.com/YogaPrabu)

---

## 📄 License

This project is licensed under the **MIT License** — see [LICENSE](LICENSE) for details.

---

<div align="center">
<sub>Built with ❤ using Python, Tkinter and Modern Software Engineering Practices</sub>
</div>
