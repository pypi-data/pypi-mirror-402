from typing import Union


byte_units = ("KB", "MB", "GB", "TB")


def format_byte_size(size: Union[int, float, str]) -> str:
    """
    Format a bytes size into the smallest value greater than 1, with the largest unit.

    This works on strings, so perhaps relatively slow, but a good free start.

    This implementation is based on:
      https://stackoverflow.com/a/58467404
      Posted by Ofer Sadan
      Retrieved 2026-01-16, License - CC BY-SA 4.0
    """
    size_list = [f"{int(size):,} B"] + [
        f"{int(size) / 1024 ** (i + 1):.1f} {u}" for i, u in enumerate(byte_units)
    ]
    return [size for size in size_list if not size.startswith("0.")][-1]
