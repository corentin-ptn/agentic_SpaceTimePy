# SpaceTimePy

This repository host the spacetimpy python library.

## Installation

On other project : 
```cmd
# With pip
pip install git+<url of the repository>
# With uv
uv add git+<url of the repository>
```

In this repo : 
```cmd
pip install -e .
```
## Live Game Explorer

SpaceTimePy includes a Live Game Explorer tool for replaying and debugging pygame executions. Two UI frameworks are available:

- **Tkinter** (original): `live-game-explorer` - Uses Tkinter with sv-ttk theming
- **Qt** (new): `live-game-explorer-qt` - Uses PyQt5 for a modern cross-platform UI

### Installation

For Tkinter version:
```bash
pip install .[game]
```

For Qt version:
```bash
pip install .[game-qt]
```