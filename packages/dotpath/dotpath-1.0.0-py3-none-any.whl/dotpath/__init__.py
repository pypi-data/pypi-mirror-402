from __future__ import annotations

from pathlib import Path
import re

try:
    import tomllib  # py3.11+
except ModuleNotFoundError:  # pragma: no cover - only for older python
    tomllib = None

try:
    import tomli  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - optional
    tomli = None


def _read_version_from_pyproject() -> str | None:
    pyproject = Path(__file__).resolve().parents[1] / "pyproject.toml"
    if not pyproject.exists():
        return None
    try:
        content = pyproject.read_text(encoding="utf-8")
        if tomllib is not None:
            data = tomllib.loads(content)
            return data.get("project", {}).get("version")
        if tomli is not None:
            data = tomli.loads(content)
            return data.get("project", {}).get("version")
        # Minimal fallback parser for the [project] version field.
        in_project = False
        for line in content.splitlines():
            stripped = line.strip()
            if stripped.startswith("[") and stripped.endswith("]"):
                in_project = stripped == "[project]"
                continue
            if not in_project or not stripped or stripped.startswith("#"):
                continue
            match = re.match(r'version\s*=\s*["\']([^"\']+)["\']', stripped)
            if match:
                return match.group(1)
    except Exception:
        return None
    return None


__version__ = _read_version_from_pyproject()


def get_path(obj: object, dotpath: str, default=None, **kwargs):
    """Return a value from an object using a dot-delimited path.

    This function traverses mappings, sequences, and attributes using the
    keys or indexes found in ``dotpath``. For sequences (list, tuple, set),
    numeric indexes are converted to strings internally.
    ``getpath`` is an alias of this function.

    Example:

    .. code-block:: python

        data = {"pets": {"dog": {"name": "Billy"}}}
        name = getpath(data, "pets.dog.name")

    :param obj: The object, mapping, or sequence to traverse.
    :param dotpath: Dot-delimited path (e.g. ``"a.b.0.c"``).
    :param default: Value returned when traversal fails.
    :param kwargs: Optional settings.
    :keyword bool raise_exception: If ``True``, re-raise the underlying
        exception instead of returning ``default``.
    :returns: The resolved value or ``default`` if not found.
    :rtype: object
    :raises AttributeError: When ``raise_exception`` is ``True`` and an
        attribute is missing.
    :raises KeyError: When ``raise_exception`` is ``True`` and a key is missing.
    :raises IndexError: When ``raise_exception`` is ``True`` and an index is
        out of range.
    """
    raise_exception = kwargs.get("raise_exception", False)
    try:
        indexes = dotpath.split(".")
        index = indexes[0]

        # Cast list, set and tuple to dict, need to get the value from index
        if type(obj) in (list, set, tuple):
            obj = {str(i): v for i, v in tuple(enumerate(obj))}

        if isinstance(obj, dict):
            if len(indexes) > 1:
                return get_path(obj[index], ".".join(indexes[1:]), default, **kwargs)
            return obj[index]

        # Get value when the obj is a dict, tuple, list or set
        if type(obj) in (dict, tuple):
            if len(indexes) > 1:
                return get_path(obj[index], ".".join(indexes[1:]), default, **kwargs)
            return getattr(obj, index)

        # Get value when the obj is an other object
        if isinstance(obj, object):
            if len(indexes) > 1:
                return get_path(
                    getattr(obj, index), ".".join(indexes[1:]), default, **kwargs
                )
            return getattr(obj, index)
    except (AttributeError, KeyError, IndexError) as err:
        if raise_exception:
            raise err
        return default


def set_path(obj: object, dotpath: str, value, default=None, **kwargs):
    """Set a value on an object using a dot-delimited path.

    This function traverses mappings, sequences, and attributes using the
    keys or indexes found in ``dotpath``. When a child is missing, a new
    ``dict`` is created by default.
    ``setpath`` is an alias of this function.

    Example:

    .. code-block:: python

        data = {}
        setpath(data, "pets.dog.name", "Billy")
        # data == {"pets": {"dog": {"name": "Billy"}}}

    :param obj: The object, mapping, or sequence to mutate.
    :param dotpath: Dot-delimited path (e.g. ``"a.b.0.c"``).
    :param value: Value to assign at the resolved path.
    :param default: Value returned when traversal fails.
    :param kwargs: Optional settings.
    :keyword bool create_child: If ``True`` (default), create missing
        children as ``dict``.
    :keyword bool raise_exception: If ``True``, re-raise the underlying
        exception instead of returning ``default``.
    :returns: The mutated root object or ``default`` if it fails.
    :rtype: object
    :raises AttributeError: When ``raise_exception`` is ``True`` and an
        attribute is missing.
    :raises KeyError: When ``raise_exception`` is ``True`` and a key is missing.
    :raises IndexError: When ``raise_exception`` is ``True`` and an index is
        out of range.
    :raises TypeError: When ``raise_exception`` is ``True`` and a value cannot
        be set on the current object.
    :raises ValueError: When ``raise_exception`` is ``True`` and a list index
        is not an integer.
    """
    raise_exception = kwargs.get("raise_exception", False)
    create_child = kwargs.get("create_child", True)
    try:
        indexes = dotpath.split(".")
        index = indexes[0]

        if isinstance(obj, list):
            list_index = int(index)
            if list_index >= len(obj):
                if not create_child:
                    raise IndexError(list_index)
                obj.extend([None] * (list_index - len(obj) + 1))
            if len(indexes) > 1:
                if obj[list_index] is None and create_child:
                    obj[list_index] = {}
                return set_path(
                    obj[list_index], ".".join(indexes[1:]), value, default, **kwargs
                )
            obj[list_index] = value
            return obj

        if isinstance(obj, dict):
            if len(indexes) > 1:
                if index not in obj or obj[index] is None:
                    if not create_child:
                        raise KeyError(index)
                    obj[index] = {}
                return set_path(
                    obj[index], ".".join(indexes[1:]), value, default, **kwargs
                )
            obj[index] = value
            return obj

        if len(indexes) > 1:
            if not hasattr(obj, index) or getattr(obj, index) is None:
                if not create_child:
                    raise AttributeError(index)
                setattr(obj, index, {})
            return set_path(
                getattr(obj, index), ".".join(indexes[1:]), value, default, **kwargs
            )
        setattr(obj, index, value)
        return obj
    except (AttributeError, KeyError, IndexError, TypeError, ValueError) as err:
        if raise_exception:
            raise err
        return default


def getpath(obj: object, dotpath: str, default=None, **kwargs):
    """Wrapper for :func:`get_path`.

    This exists for backward compatibility with earlier releases.
    """
    return get_path(obj, dotpath, default, **kwargs)


def setpath(obj: object, dotpath: str, value, default=None, **kwargs):
    """Wrapper for :func:`set_path`.

    This exists for backward compatibility with earlier releases.
    """
    return set_path(obj, dotpath, value, default, **kwargs)
