"""Expose the Netrias client facade and package metadata."""

from __future__ import annotations

from ._client import NetriasClient
from ._errors import DataModelStoreError
from ._models import CDE, DataModel, PermissibleValue

__all__ = [
    "NetriasClient",
    "DataModel",
    "CDE",
    "PermissibleValue",
    "DataModelStoreError",
    "__version__",
]

__version__ = "0.1.0"
