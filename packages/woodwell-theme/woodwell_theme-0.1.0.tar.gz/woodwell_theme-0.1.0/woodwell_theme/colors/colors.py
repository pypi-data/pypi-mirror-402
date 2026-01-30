from __future__ import annotations

from collections import OrderedDict
from collections.abc import Mapping
from typing import Iterable


class _Colors(Mapping):
    """
    Read‑only Mapping that stores an ordered color palette.

    * `colors['primary']`     → hex string.
    * `dict(colors)`          → a mutable copy (plain dict).
    * `print(colors)`         → multi‑line, nicely aligned output.
    #  'accent' in colors     → True
    #  for name, hex in colors: …
    #  print(colors)          → nicely formatted list

    * Supports `len()`, `in`, `keys()`, `values()`, `items()`.
    """

    _colors: 'OrderedDict[str, str]' = OrderedDict(
        [
            # primary
            ('primary', '#36363C'),
            ('secondary', '#ffffff'),
            ('edge', '#36363C'),
            ('line', '#36363C'),

            # neutrals
            ('black', '#36363C'),      # graphite
            ('darkgray', '#42433B'),   # charcoal
            ('gray', '#DCDAD2'),       # dust gray
            ('lightgray', '#EFEEEE'),  # platinum

            # signature
            ('orange', '#FF5700'),     # blaze orange
            ('blue', '#233E99'),       # french blue
        ]
    )

    # mapping protocol (required by collections.abc.Mapping)
    def __getitem__(self, key: str) -> str:
        """
        Return the hex code for a given color name.

        Raises KeyError if the color name is missing.
        """
        return self._colors[key]

    def __iter__(self) -> Iterable[str]:
        """
        Iterate over color names (keys) in defined order.
        """
        return iter(self._colors)

    def __len__(self) -> int:
        """
        Number of colors in the theme.
        """
        return len(self._colors)

    def get(self, key: str, default: str | None = None) -> str | None:
        """
        Dictionary‑style `get` – returns *default* if *key* is absent.

        Users can alternatively use colors[key] to get a specific color.
        """
        return self._colors.get(key, default)

    def __str__(self) -> str:
        """
        Allows users to call `print(colors)` to get full list of
        color key, value pairs.
        """
        # get the key (color name) with the longest length to make it easy to
        # align all key, value print lines
        max_key_len = max(len(k) for k in self._colors)
        lines = [
            f'{name.ljust(max_key_len)}  {hexcode}'
            for name, hexcode in self._colors.items()
        ]

        return '\n'.join(lines)

    __repr__ = __str__


# export colors
colors = _Colors()
