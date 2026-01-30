"""TestInputBuilt domain event.

Indicates that a test input has been built and is ready for command execution.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from command_eval.domain.events.base_event import DomainEvent
from command_eval.domain.value_objects.file_path import FilePath
from command_eval.domain.value_objects.ids.data_item_id import DataItemId
from command_eval.domain.value_objects.ids.test_input_id import TestInputId


@dataclass(frozen=True)
class TestInputBuilt(DomainEvent):
    """Event indicating a test input has been built.

    Attributes:
        test_input_id: The ID of the built test input.
        data_item_id: The ID of the source data item.
        command: The command to execute.
        actual_output_file: The actual output file path (renamed from output_file).
    """

    EVENT_TYPE: ClassVar[str] = "TestInputBuilt"

    test_input_id: TestInputId
    data_item_id: DataItemId
    command: str
    actual_output_file: FilePath

    def __post_init__(self) -> None:
        """Validate event data."""
        if not self.command:
            raise ValueError("Command cannot be empty")
