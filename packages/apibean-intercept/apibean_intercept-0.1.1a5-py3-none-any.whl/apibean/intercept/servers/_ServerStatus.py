"""
Server status representation with dict-like behavior and notebook-friendly output.
"""

from collections.abc import MutableMapping
import yaml


class ServerStatus(MutableMapping):
    """Dict-like container for server runtime status.

    Supports YAML string output for CLI/logging and optional Markdown
    rendering for Jupyter notebooks.
    """

    def __init__(self, **data):
        """Initialize status data."""
        self._data = dict(data)
        self._enable_markdown_repr = True

    def enable_markdown(self, flag: bool):
        """Enable or disable Markdown representation."""
        self._enable_markdown_repr = flag
        return self

    # ---- Mapping protocol ----
    def __getitem__(self, key):
        """Return value for the given key."""
        return self._data[key]

    def __setitem__(self, key, value):
        """Set value for the given key."""
        self._data[key] = value

    def __delitem__(self, key):
        """Delete the given key."""
        del self._data[key]

    def __iter__(self):
        """Iterate over keys."""
        return iter(self._data)

    def __len__(self):
        """Return number of items."""
        return len(self._data)

    # ---- Dict-like helpers ----
    def to_dict(self) -> dict:
        """Return a shallow dict copy."""
        return dict(self._data)

    # ---- Presentation ----
    def __str__(self) -> str:
        """Return YAML-formatted string."""
        return yaml.safe_dump(
            self._data,
            sort_keys=False,
            default_flow_style=False,
        )

    def __repr__(self) -> str:
        """Return YAML-formatted representation."""
        return yaml.safe_dump(
            self._data,
            sort_keys=False,
            default_flow_style=False,
        )

    def _repr_markdown_(self) -> str:
        """Return YAML wrapped in Markdown code block for Jupyter."""
        if not self._enable_markdown_repr:
            return None
        yaml_text = yaml.safe_dump(
            self._data,
            sort_keys=False,
            default_flow_style=False,
        )
        return f"```yaml\n{yaml_text}```"
