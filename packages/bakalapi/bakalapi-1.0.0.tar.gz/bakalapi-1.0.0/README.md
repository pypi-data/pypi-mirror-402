# Bakalapi Python Library

A Python library for accessing the Bakalapi timetable API. This library provides a simple interface to query timetable information by teacher, room, or class.

## Installation

### Install from local directory

If you have the source code, you can install it directly:

```bash
pip install .
```

Or in development mode (editable install):

```bash
pip install -e .
```

### Install from PyPI (if published)

If the package is published to PyPI, you can install it with:

```bash
pip install bakalapi
```

### Development Installation

For development, you can also install dependencies separately:

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

```python
from bakalapi import BakalapiClient

# Create a client instance
client = BakalapiClient()

# Get timetable by teacher
timetable = client.get_teacher_timetable("Hana Jaitnerová")
print(f"Found {len(timetable.timetable)} entries")
for entry in timetable.timetable:
    print(f"{entry.date} {entry.time}: {entry.subject} - {entry.class_name}")

# Get timetable by room
timetable = client.get_room_timetable("a1")
print(f"Room a1 has {len(timetable.timetable)} scheduled entries")

# Get timetable by class
timetable = client.get_class_timetable("4.B Sk1")
print(f"Class 4.B Sk1 has {len(timetable.timetable)} scheduled entries")

# Close the client when done
client.close()
```

### Using Context Manager

```python
from bakalapi import BakalapiClient

with BakalapiClient() as client:
    timetable = client.get_teacher_timetable("Mgr. Hana Jaitnerová")
    # Client is automatically closed when exiting the context
```

### Accessing Data

The library provides structured data models:

```python
from bakalapi import BakalapiClient

client = BakalapiClient()
timetable = client.get_teacher_timetable("Mgr. Hana Jaitnerová")

# Access hour definitions
for hour in timetable.hours:
    print(f"Hour {hour.number}: {hour.start_time} - {hour.end_time}")

# Access timetable entries
for entry in timetable.timetable:
    print(f"Day: {entry.day}")
    print(f"Date: {entry.date}")
    print(f"Time: {entry.time}")
    print(f"Subject: {entry.subject}")
    print(f"Teacher: {entry.teacher}")
    print(f"Room: {entry.room}")
    print(f"Class: {entry.class_name}")
    print(f"Theme: {entry.theme}")
    print(f"Change info: {entry.changeinfo}")
    print("---")
```

### Error Handling

```python
from bakalapi import BakalapiClient, BakalapiAPIError

client = BakalapiClient()

try:
    timetable = client.get_teacher_timetable("Non-existent Teacher")
except BakalapiAPIError as e:
    print(f"API Error: {e}")
    print(f"Status Code: {e.status_code}")
except ValueError as e:
    print(f"Invalid parameter: {e}")
```

## API Methods

### `get_teacher_timetable(teacher_name: str) -> TimetableResponse`

Get the timetable for a specific teacher.

**Parameters:**
- `teacher_name`: The name of the teacher (e.g., "Mgr. Hana Jaitnerová")

**Returns:**
- `TimetableResponse`: Object containing hours and timetable entries

### `get_room_timetable(room_index: str) -> TimetableResponse`

Get the timetable for a specific room.

**Parameters:**
- `room_index`: The room index/identifier (e.g., "a1")

**Returns:**
- `TimetableResponse`: Object containing hours and timetable entries

### `get_class_timetable(class_name: str) -> TimetableResponse`

Get the timetable for a specific class.

**Parameters:**
- `class_name`: The name of the class (e.g., "4.B Sk1")

**Returns:**
- `TimetableResponse`: Object containing hours and timetable entries

## Data Models

### `TimetableResponse`

- `hours: List[Hour]` - List of hour definitions
- `timetable: List[TimetableEntry]` - List of timetable entries

### `Hour`

- `number: int` - Hour number
- `start_time: str` - Start time (e.g., "8:00")
- `end_time: str` - End time (e.g., "8:45")

### `TimetableEntry`

- `day: str` - Day abbreviation (e.g., "po", "út", "st")
- `date: str` - Date (e.g., "12.1.")
- `hour_number: int` - Hour number
- `time: str` - Time range (e.g., "8:00 - 8:45")
- `subject: str` - Subject name
- `teacher: str` - Teacher name(s)
- `room: str` - Room identifier
- `class_name: str` - Class name(s)
- `theme: Optional[str]` - Lesson theme/topic
- `notice: Optional[str]` - Notice/note
- `changeinfo: Optional[str]` - Change information
- `entry_type: str` - Entry type (e.g., "atom")

## Notes

- **Parameters cannot be combined**: You can only query by one type (teacher, room, or class) at a time.
- The API endpoint is: `https://bakalapi-production.up.railway.app/api/timetable/`
- All parameters are automatically URL-encoded for safe transmission.

## Publishing to PyPI

If you want to publish this package to PyPI so others can install it with `pip install bakalapi`:

1. Install build tools:
   ```bash
   pip install build twine
   ```

2. Build the package:
   ```bash
   python -m build
   ```

3. Upload to PyPI (test first with TestPyPI):
   ```bash
   # Test upload
   twine upload --repository testpypi dist/*
   
   # Production upload
   twine upload dist/*
   ```

Note: Update the `pyproject.toml` file with your actual author information and repository URLs before publishing.

## License

This library is provided as-is for accessing the Bakalapi timetable API.
