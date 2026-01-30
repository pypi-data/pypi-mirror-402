# adroit-py

Python wrapper package for the Adroit OLE server. Provides a friendly `AdroitOLE` class
and a module-level `adroit` object for interactive use.

## Requirements

- Python 3.x on Windows (requires `pywin32>=305`)

Installation (editable/development):

```bash
python -m pip install -e .
```

Usage:

```python
from adroit import AdroitOLE

# connect when needed
adroit: AdroitOLE = AdroitOLE()
print(adroit.FetchTags(["A1.value", "A2.value"]))
```
