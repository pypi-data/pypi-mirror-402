"""
Absfuyu: Core
-------------
Dummy functions when other libraries are unvailable

Version: 6.3.0
Date updated: 22/01/2026 (dd/mm/yyyy)
"""

# Module Package
# ---------------------------------------------------------------------------
__all__ = [
    "tqdm",
    "tqdm2",
    "unidecode",
    "dummy_function",
]


# Library
# ---------------------------------------------------------------------------
from functools import partial
from importlib import import_module

# Wrapper
# ---------------------------------------------------------------------------
# tqdm wrapper
try:
    _tqdm = import_module("tqdm")
    tqdm = getattr(_tqdm, "tqdm")  # noqa
    tqdm2 = partial(tqdm, unit_scale=True, dynamic_ncols=True)
except (ImportError, AttributeError):

    def tqdm(iterable, *args, **kwargs):
        """
        Dummy tqdm function,
        install package ``tqdm`` to fully use this feature
        """
        return iterable

    tqdm2 = tqdm

# unidecode wrapper
try:
    _unidecode = import_module("unidecode")
    unidecode = getattr(_unidecode, "unidecode")  # noqa
except (ImportError, AttributeError):

    def unidecode(*args, **kwargs):
        """
        Dummy unidecode function,
        install package ``unidecode`` to fully use this feature
        """
        return args[0]


# dummy
def dummy_function(*args, **kwargs):
    """This is a dummy function"""
    if args:
        return args[0]
    if kwargs:
        return kwargs[list(kwargs)[0]]
    return None
