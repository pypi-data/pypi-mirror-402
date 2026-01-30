"""Type hints imported from suitable modules depending on the Python version."""

import sys

if sys.version_info < (3, 11):
    from typing_extensions import NotRequired, Self, Unpack, assert_never
else:
    from typing import NotRequired, Self, Unpack, assert_never

if sys.version_info < (3, 12):
    from typing_extensions import TypeAliasType, override
else:
    from typing import TypeAliasType, override

if sys.version_info < (3, 13):
    from typing_extensions import TypeIs
else:
    from typing import TypeIs

if sys.version_info < (3, 14):
    from typing_extensions import Writer
else:
    from io import Writer

__all__ = [
    "NotRequired",
    "Self",
    "TypeAliasType",
    "TypeIs",
    "Unpack",
    "Writer",
    "assert_never",
    "override",
]
