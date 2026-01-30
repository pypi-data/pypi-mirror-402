import pathlib
import matplotlib.pyplot as plt

from .colors import colors
from .fonts import fonts

# options are:
# - Ginto Normal
# - Ginto Normal Medium
# - Ginto Normal Bold
# - Gemeli Mono
# - Gemeli Mono Bold
_DEFAULT_FONT_FAMILY = 'Ginto Normal'


def load():
    """
    Apply the Matplotlib rcParams from the bundled `theme.mplstyle` file and
    set the default font family to the one that is shipped with the package.

    Example
    -------
    >>> import theme
    >>> theme.load() # style + default font are applied
    """
    style_path = pathlib.Path(__file__).parent / 'style' / 'theme.mplstyle'
    plt.style.use(str(style_path))

    if _DEFAULT_FONT_FAMILY not in fonts:
        raise ValueError(
            f"The bundled font family '{_DEFAULT_FONT_FAMILY}' was not found."
            f'Available families: {list(fonts)}'
        )
    plt.rcParams['font.family'] = _DEFAULT_FONT_FAMILY


__all__ = [
    'colors', 'fonts', 'load',
]
