# dotpath
A tiny utility to read values from nested dicts/lists using dot-separated paths.

## Install
```bash
pip install dotpath
```

## Example
```python
from dotpath import get_path, set_path

data = {
    'pets': {
        'dog': {
            'name': 'Billy',
            'age': 5,
            'friends': ['Joe', 'Jack'],
        },
        'cat': {
            'name': 'Joe',
            'age': 6,
            'friends': ['Billy', 'Pop'],
        },
    },
}

dog_name = get_path(data, 'pets.dog.name')  # "Billy"
cat_name = get_path(data, 'pets.cat.name')  # "Joe"
first_friend = get_path(data, 'pets.dog.friends.0')  # "Joe"

set_path(data, 'pets.dog.age', 6) # Modifies the object in place
set_path(data, 'pets.bird.name', 'Kiwi') # Creates a new key
print(data) # {"pets": {"dog": {"name": "Billy", "age": 6, "friends": ["Joe", "Jack"]}, "cat": {"name": "Joe", "age": 6, "friends": ["Billy", "Pop"]}, "bird": {"name": "Kiwi"}}}
```

## API
- `get_path(obj, path, default=None)`: Returns the value at `path` or `default`
  if the path cannot be resolved.
- `set_path(obj, path, value, default=None)`: Sets `value` at `path` and returns
  the mutated object or `default` if it fails.

## Notes
- Path segments are split by `.`.
- List indexes are supported via numeric segments (e.g. `friends.0`).