from __future__ import annotations

from pathlib import Path
from collections.abc import Mapping
from typing import Dict, Iterable

from pyfonts import load_font
import matplotlib
from matplotlib import font_manager


def _register_ttf(ttf_path: Path) -> str:
    """
    Register a TrueType font with Matplotlib's global FontManager
    and return the family name that Matplotlib extracts from the file.
    """
    font_manager.fontManager.addfont(str(ttf_path))
    prop = font_manager.FontProperties(fname=str(ttf_path))

    return prop.get_name()


class _Fonts(Mapping):
    """
    Read‑only mapping of bundled TrueType fonts to
    Matplotlib FontProperties objects.
    """
    _fonts_dir: Path = Path(__file__).parent / 'ttf'
    # ex: {'Ginto Normal': <matplotlib.font_manager.FontProperties>}
    _family_to_prop: Dict[str, matplotlib.font_manager.FontProperties] = {}

    # Register every *.ttf file that lives next to this file
    for ttf_path in _fonts_dir.glob('*.ttf'):
        family = _register_ttf(ttf_path)            # registers globally
        font_properties = load_font(str(ttf_path))  # FontProperties object
        _family_to_prop[family] = font_properties

    # mapping protocol
    def __getitem__(self, key: str):
        """
        Return the Matplotlib FontProperties for a given font name.

        Raises KeyError if the font name is missing.
        """
        return self._family_to_prop[key]

    def __iter__(self) -> Iterable[str]:
        """
        Iterate over font names (keys).
        """
        return iter(self._family_to_prop)

    def __len__(self) -> int:
        """
        Number of fonts in the theme.
        """
        return len(self._family_to_prop)

    def get(self, key: str, default=None) -> str | None:
        """
        Return the Matplotlib FontProperties for a given font name.
        """
        return self._family_to_prop.get(key, default)

    def as_dict(self, key: str) -> Dict[str, str | float]:
        """
        Return a shallow copy of a FontProperties object as a Python `dict`.
        """
        font_prop = self._family_to_prop.get(key)

        font_dict = {
            'family': font_prop.get_family()[0],
            'style': font_prop.get_style(),
            'weight': font_prop.get_weight(),
            'size': font_prop.get_size(),
            'stretch': font_prop.get_stretch(),
            'variant': font_prop.get_variant(),
        }

        return font_dict

    def all_fonts(self) -> Dict[str, matplotlib.font_manager.FontProperties]:
        """
        Mutable copy of the internal font dictionary.
        """
        return dict(self._family_to_prop)

    def __str__(self) -> str:
        max_len = max(len(k) for k in self._family_to_prop)
        lines = [
            f"{k.ljust(max_len)}"
            for k, v in self._family_to_prop.items()
        ]

        return "\n".join(lines)

    __repr__ = __str__


# export fonts
fonts = _Fonts()
