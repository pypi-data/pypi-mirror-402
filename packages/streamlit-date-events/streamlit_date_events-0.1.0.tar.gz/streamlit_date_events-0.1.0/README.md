# Streamlit Date Events

En forbedret date input komponent til Streamlit med event markers.

## Features

- 📅 Kalender-baseret date picker i Streamlit-stil
- 🔴 Event markers (små prikker) under specifikke datoer
- 🎨 Matchende Streamlit design
- ⚙️ Min/max dato begrænsninger
- 🎨 Tilpasselig event farve

## Installation

```bash
pip install streamlit-date-events
```

## Brug

```python
import streamlit as st
from streamlit_date_events import date_input_with_events
from datetime import date, timedelta

# Definer nogle event datoer
today = date.today()
events = [
    today,
    today + timedelta(days=3),
    today + timedelta(days=7),
    today + timedelta(days=14),
]

# Brug komponenten
selected_date = date_input_with_events(
    label="Vælg en dato",
    value=today,
    event_dates=events,
    event_color="#FF4B4B",  # Streamlit rød
    min_date=today - timedelta(days=30),
    max_date=today + timedelta(days=90),
)

if selected_date:
    st.write(f"Du valgte: {selected_date}")
    if selected_date in events:
        st.success("Denne dato har en event! 🎉")
```

## Parameters

- **label** (str): Label tekst for komponenten
- **value** (date/datetime): Standard valgt dato
- **event_dates** (list): Liste af datoer med events
- **min_date** (date/datetime): Mindste valgbare dato
- **max_date** (date/datetime): Største valgbare dato
- **event_color** (str): Farve på event markers (hex/rgb)
- **key** (str): Unik nøgle til komponenten

## Development Setup

### Frontend

```bash
cd streamlit_date_events/frontend
npm install
npm start  # Kører på localhost:3000
```

### Python Package

I `__init__.py`, sæt `_RELEASE = False` for development mode.

```bash
cd streamlit_date_events
python -m pip install -e .
```

### Build til release

```bash
cd frontend
npm run build
```

Sæt `_RELEASE = True` i `__init__.py` før release.

## License

MIT