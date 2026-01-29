# Smallpy Utility Functions
A collection of reusable Python utility functions and classes for:
- console output control
- JSON "memory" file management
- Excel exporting
- basic image recognition and screen navigation
- progression tracking with time estimation

This module is intended to be imported and reused across automation and data-processing scripts.

---

## Features
- Enable ANSI color / cursor control on Windows terminals
- Clear previously printed terminal lines
- Write Pandas DataFrames to Excel
- Persist structured data to JSON "memory"
  - check for existing entries in "memory"
- Wait for UI images to appear or disappear (via PyAutoGUI)
- Click UI elements based on image matching
- Track progess of iteration with dynamic formatting options
- Get most recentely created file in a directory

## Installation
```bash
pip install small-py
```

**Dependencies:**
```bash
pip install pandas pyautogui
```

---

## Usage
Import the functions or classes you need:
```python
from utils import (
  enable_virtual_terminal,
  clear_terminal,
  write_to_excel,
  add_to_memory,
  is_in_memory,
  wait_for_image,
  find_and_click,
  Counter,
  get_most_recent_file,
)
```

## Console Utilities
### Enable ANSI / Virtual Terminal Support (Windows)
```python
enable_virtual_terminal()
```

### Clear Previously Printed Lines
```python
clear_terminal(lines=2)
```

## Excel Output
### Write Dataframe to Excel
```python
import pandas as pd

df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
write_to_excel(df, "output.xlsx")
```

## Persistent Memory (JSON)
Stored in ./memory/memory.json by default
### Memory Strucutre
```python
{"key":"entry"}
```
```json
{
  "key1":{
    "id":"entry1",
    "optional_field_1":"value",
    ...
    "optional_field_n":"value"
  },
  ...
}
```
- "Key" identifies a shared entry structure for a particular purpose
  - All entries under the same key must share the same structure
  - A "memory" file can have multiple "keys"
- Entries **must** contain an "id" field
- New entries replace existing entries with the same id
### Add or Update an Entry
```python
entry = {"id": 1, "status": "done"}
add_to_memory(
  memory_key = "tasks",
  new_entry = entry
)
```

### Check if an Entry Exists
```python
exists = is_in_memory(
  memory_key="tasks",
  new_entry={"id": 1, "status": "done"},
  comparison_field="status"
)
```

## Screen Automation (PyAutoGUI)
### Wait for an Image
```python
coord = wait_for_image("button.png", timeout=10)
```
- Accepts a single image path or a list of paths
- Can optionally wait for an image to **disappear**:
```python
wait_for_image("loading.png", invert_search=True)
```

### Find and Click an Image
Clicks on the center of the found image
```python
find_and_click("submit.png")
```
- Optionally offset the click location, measured in pixels from the center of the reference image
  - offset=(x_offset,y_offset)
  - increasing x offsets to right, increasing y offsets down
```python
find_and_click("submit.png",offset=(5,5))
```
## Progress Tracking
### Counter Class

Tracks progress and estimates remaining time.
```python
counter = Counter(
    count=10
)

for _ in range(10):
    # do work
    counter.display()
```
- Output of `counter.display()` will default to `n/N` where `n` is the iteration number and `N` is the total count
- A custom format can be passed upon initialization
```python
counter = Counter(
    count=10,
    format = "Iteration %n/%N"
)

for _ in range(10):
    # do work
    counter.display()
```
- Or by changing the `formatter` attribute to utilize dynamic formatting with f-strings
```python
counter = Counter(
    count=10
)

for item in ['foo','bar','baz','qux']:
    # do work
    counter.formatter = f"Iteration %n/%N - {item}"
    counter.display()
```

#### Format tokens:
- `%n` — iteration number
- `%N` — total count
- `%T` — estimated completion time (e.g. "02:04 PM")
- `%t` — raw seconds remaining as float
- `%f` — time remaining split by unit (e.g. "2h 4m 8s")

## File Utilities
### Get Most Recent File in a Directory
```python
latest = get_most_recent_file("downloads")
```
Returns the path to the most recently created file, or "No files found".

## Notes & Limitations
- Screen automation relies on image matching and screen resolution
- JSON memory assumes consistent dictionary structure per key
- Designed for scripting and automation, not as a full framework

## License
MIT License (or update as appropriate)