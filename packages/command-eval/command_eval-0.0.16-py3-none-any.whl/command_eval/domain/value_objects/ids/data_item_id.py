"""DataItemId value object.

Unique identifier for data items.
"""

from dataclasses import dataclass

from command_eval.domain.value_objects.ids.base_id import BaseId


@dataclass(frozen=True)
class DataItemId(BaseId):
    """Unique identifier for a data item (UUIDv4)."""

    pass
