# PillowStrap

**Bootstrap-like semantics for Python Image Generation.**

[![PyPI version](https://badge.fury.io/py/pillowstrap.svg)](https://badge.fury.io/py/pillowstrap)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**PillowStrap** is a wrapper around the Python Pillow (PIL) library. It replaces imperative coordinate math (e.g., `x=150, y=300`) with declarative, web-like semantics (e.g., `row`, `col-6`, `text-center`, `bg-primary`).

Stop calculating pixels. Start building layouts.

## 🚀 Features

* **12-Column Grid System:** Just like Bootstrap, organize content into rows and columns.
* **Auto-Stacking Text:** No more manual Y-coordinate tracking. Text blocks stack automatically like a Word document.
* **Smart Word Wrapping:** Text automatically breaks to the next line if it exceeds the column width.
* **Image Fit Utilities:** Easily place images with `cover` or `contain` logic.
* **Theming:** Centralized control over colors, fonts, and spacing.

## Installation

```bash
pip install pillowstrap
```

## Quick Start
Create a dashboard.py file and run this code:

```python
from pillowstrap import PillowStrap

# 1. Initialize Canvas (Width x Height)
app = PillowStrap(width=1200, height=800, bg="white")

# 2. Header Row (Height: 100px)
with app.row(height=100) as row:
    row.col(12, bg="primary").text("Monthly Report", color="white", size=50, align="center")

# 3. Content Row (Height: 500px)
with app.row(height=500) as row:
    
    # Left Column: Text (Spans 4 columns)
    ctx = row.col(4, bg="light")
    
    # Stacking Headers
    ctx.text("Executive Summary", size=30, weight="bold")
    ctx.text("Prepared by: Gemini", size=20, color="secondary")
    
    # Auto-Wrapping Body Text
    ctx.text(
        "PillowStrap handles long text automatically. "
        "You do not need to calculate line breaks manually. "
        "It respects the column width and padding.",
        size=24
    )

    # Right Column: Image (Spans 8 columns)
    # Places an image and crops it to fill the area
    row.col(8).img("charts.png", fit="cover")

# 4. Save
app.save("dashboard.png")
```
# Configuration
You can customize the colors and fonts by modifying pillowstrap/theme.py inside the library or subclassing the instance (feature coming in v1.1).