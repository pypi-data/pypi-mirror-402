from typing import Tuple
from PIL import Image
import matplotlib.pyplot as plt


def pil_to_figure(
    img: Image.Image,
    figsize: Tuple[float, float] = (6.0, 6.0),
    title: str | None = None,
):
    """
    Wrap a Pillow image in a Matplotlib figure for Sphinx / notebooks.

    Returns the Matplotlib figure; callers should *not* call plt.show()
    when running under Sphinx.
    """
    fig, ax = plt.subplots(figsize=figsize)
    ax.imshow(img)
    ax.axis("off")
    if title is not None:
        ax.set_title(title)
    return fig
