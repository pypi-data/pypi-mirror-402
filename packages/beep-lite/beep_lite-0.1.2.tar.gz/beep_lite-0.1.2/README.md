# beep-lite 🔊

[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI version](https://badge.fury.io/py/beep-lite.svg)](https://badge.fury.io/py/beep-lite)

A simple, cross-platform notification sound library for Python.

Play the same WAV audio files on Windows / macOS / Linux with a **lightweight, low-dependency, and reliable** solution.

**[日本語](README_JA.md)**

## ✨ Features

- **Cross-platform**: Windows / macOS / Linux support
- **Lightweight**: No heavy dependencies like numpy (~30KB)
- **Exception-safe**: Never crashes your app on playback failure
- **Non-blocking**: Asynchronous playback doesn't freeze your UI
- **PyInstaller ready**: Bundle into standalone executables

## 📦 Installation

```bash
pip install beep-lite
```

### Optional: High-quality audio backend

```bash
pip install beep-lite[audio]
```

## 🚀 Usage

```python
import beep_lite as beep

# Basic notifications
beep.ok()       # ✅ Success
beep.ng()       # ❌ Error / Failure
beep.warn()     # ⚠️ Warning
beep.crit()     # 🚨 Critical / Urgent

# Fun notifications
beep.moo()      # 🐄 Low frequency
beep.mew()      # 🐱 High frequency

# Scan results
beep.scan_ok()  # 📗 Scan success
beep.scan_ng()  # 📕 Scan failure
```

### Using Sound enum

```python
from beep_lite import play, Sound

play(Sound.OK)
play(Sound.SCAN_NG)
```

### Preload at startup (optional)

```python
from beep_lite import preload_all

# Call at app startup to reduce latency on first play
preload_all()
```

## 🎵 Sound List

| Function | Sound Enum | Use Case | Characteristics |
|----------|------------|----------|-----------------|
| `ok()` | `Sound.OK` | Success | Bright, short, ascending |
| `ng()` | `Sound.NG` | Error | Descending, slightly longer |
| `warn()` | `Sound.WARN` | Warning | Two-tone alert |
| `crit()` | `Sound.CRIT` | Critical | Three low tones |
| `moo()` | `Sound.MOO` | Fun (low) | Low frequency sweep |
| `mew()` | `Sound.MEW` | Fun (high) | High frequency sweep |
| `scan_ok()` | `Sound.SCAN_OK` | Scan success | Very short, sharp |
| `scan_ng()` | `Sound.SCAN_NG` | Scan failure | Low, short |

## 🔧 Backends

The library automatically selects the best available backend:

| Priority | Backend | OS | Dependency |
|----------|---------|-----|------------|
| 1 | winsound | Windows | None (stdlib) |
| 2 | simpleaudio | All | `pip install simpleaudio` |
| 3 | terminal bell | All | None (fallback) |

## 📋 Requirements

- Python 3.10+

### Additional Requirements for Linux / Raspberry Pi

To use `simpleaudio` with the `[audio]` option, you need the ALSA development library:

```bash
# Debian / Ubuntu / Raspberry Pi OS
sudo apt-get install libasound2-dev

# Then install
pip install beep-lite[audio]
```

> **Note**: If installed without `[audio]`, the library falls back to terminal bell (`\a`), which requires no additional packages.

## 🎯 Use Cases

### Barcode Scanner

```python
def on_scan(barcode: str) -> None:
    if validate(barcode):
        beep.scan_ok()
        process(barcode)
    else:
        beep.scan_ng()
```

### Long-running Task Completion

```python
def heavy_task() -> None:
    try:
        # Heavy processing...
        result = process_data()
        beep.ok()
    except Exception:
        beep.ng()
        raise
```

### GUI Form Validation

```python
def on_submit() -> None:
    if not validate_form():
        beep.warn()
        show_error("Please check your input")
        return
    save_data()
    beep.ok()
```

## 🏭 PyInstaller Usage

```bash
pyinstaller --collect-data beep_lite your_app.py
```

Or in your `.spec` file:

```python
datas=[('path/to/beep_lite/assets', 'beep_lite/assets')]
```
```

## 📄 License

MIT License

## 📬 Links

<!-- - [PyPI](https://pypi.org/project/beep-lite/) -->
- [GitHub](https://github.com/Moge800/beep_lite)
