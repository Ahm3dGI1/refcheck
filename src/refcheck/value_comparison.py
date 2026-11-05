"""Value equality rules shared by return and argument-state comparisons."""

import math
from typing import Any


def values_differ(original: Any, migrated: Any) -> bool:
    """Use Python equality, treating two scalar float NaNs as equivalent."""
    if (
        isinstance(original, float)
        and isinstance(migrated, float)
        and math.isnan(original)
        and math.isnan(migrated)
    ):
        return False
    return original != migrated
