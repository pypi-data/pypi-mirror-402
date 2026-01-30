"""Result output policy.

Policy that outputs evaluation results to files and stdout.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Optional

from command_eval.domain.ports.result_writer_port import (
    ResultWriteRequest,
    ResultWriteResponse,
    ResultWriterPort,
)
from command_eval.domain.value_objects.output_config import OutputConfig

if TYPE_CHECKING:
    from command_eval.domain.aggregates.data_file import DataFile
    from command_eval.domain.aggregates.evaluation import Evaluation
    from command_eval.domain.aggregates.execution import Execution
    from command_eval.domain.aggregates.test_case import TestCase
    from command_eval.domain.aggregates.test_input import TestInput


def _to_template_dict(obj: Any) -> Any:
    """Convert any object to a template-friendly dictionary recursively.

    Handles:
    - dataclasses: Converts to dict with all fields
    - Enums: Returns the value
    - datetime: Returns ISO format string
    - Value objects with 'value' attribute: Returns the value
    - tuples/lists: Converts each element
    - dicts: Converts each value
    - set/frozenset: Converts to list
    - Other: Returns string representation if not JSON serializable
    """
    import json

    if obj is None:
        return None

    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        result = {}
        for f in dataclasses.fields(obj):
            value = getattr(obj, f.name)
            result[f.name] = _to_template_dict(value)
        # Also include properties (non-field attributes that are properties)
        for name in dir(obj):
            if not name.startswith("_") and name not in result:
                try:
                    attr = getattr(type(obj), name, None)
                    if isinstance(attr, property):
                        result[name] = _to_template_dict(getattr(obj, name))
                except Exception:
                    pass
        return result

    if isinstance(obj, Enum):
        return obj.value

    if isinstance(obj, datetime):
        return obj.isoformat()

    if hasattr(obj, "value") and not isinstance(obj, (str, bytes, dict)):
        # Handle value objects like FilePath, IDs, etc.
        return obj.value

    # Primitive types - return as-is
    if isinstance(obj, (str, int, float, bool)):
        return obj

    if isinstance(obj, (list, tuple)):
        return [_to_template_dict(item) for item in obj]

    if isinstance(obj, dict):
        return {k: _to_template_dict(v) for k, v in obj.items()}

    # Set/frozenset - convert to list
    if isinstance(obj, (set, frozenset)):
        return [_to_template_dict(item) for item in obj]

    # Try direct JSON serialization for other types
    try:
        json.dumps(obj)
        return obj
    except (TypeError, ValueError):
        # Convert to string as fallback
        return str(obj)


@dataclass(frozen=True)
class OutputResultRequest:
    """Request to output a single evaluation result.

    Attributes:
        output_config: Configuration for output format and location.
        item_id: Unique identifier for the result item.
        result_data: The evaluation result data to write.
        timestamp_dir: Optional timestamp directory name.
    """

    output_config: OutputConfig
    item_id: str
    result_data: dict[str, Any]
    timestamp_dir: Optional[str] = None

    def get_timestamp_dir(self) -> str:
        """Get the timestamp directory name."""
        if self.timestamp_dir:
            return self.timestamp_dir
        return datetime.now().strftime("%Y-%m-%d_%H%M%S")


@dataclass(frozen=True)
class BatchOutputResultRequest:
    """Request to output batch evaluation results.

    Attributes:
        data_file: The data file with output config and items.
        test_inputs: All test inputs.
        test_cases: All test cases.
        executions: All command executions.
        evaluation: The evaluation result.
    """

    data_file: "DataFile"
    test_inputs: tuple["TestInput", ...]
    test_cases: tuple["TestCase", ...]
    executions: tuple["Execution", ...]
    evaluation: "Evaluation"


@dataclass(frozen=True)
class BatchOutputResultResult:
    """Result of batch output operation.

    Attributes:
        success_count: Number of successfully written items.
        failure_count: Number of failed items.
        outputs: List of (item_id, output_path or error) tuples.
    """

    success_count: int
    failure_count: int
    outputs: tuple[tuple[str, str], ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class OutputResultResult:
    """Result of outputting evaluation results.

    Attributes:
        write_response: Response from the result writer.
        stdout_output: The content that was written to stdout.
    """

    write_response: ResultWriteResponse
    stdout_output: str


class ResultOutputPolicy:
    """Policy for outputting evaluation results.

    This policy is responsible for:
    - Writing evaluation results to files using templates
    - Printing results to stdout
    - Building result data from domain aggregates
    """

    def __init__(self, result_writer: ResultWriterPort) -> None:
        """Initialize the policy."""
        self._result_writer = result_writer

    def execute(self, request: OutputResultRequest) -> OutputResultResult:
        """Execute single result output."""
        timestamp_dir = request.get_timestamp_dir()
        write_request = ResultWriteRequest(
            output_config=request.output_config,
            item_id=request.item_id,
            result_data=request.result_data,
            timestamp_dir=timestamp_dir,
        )
        write_response = self._result_writer.write(write_request)
        stdout_output = self._generate_stdout_output(request, write_response)
        return OutputResultResult(
            write_response=write_response,
            stdout_output=stdout_output,
        )

    def execute_batch(self, request: BatchOutputResultRequest) -> BatchOutputResultResult:
        """Execute batch result output.

        Transforms domain aggregates into result data and outputs each item.
        Template can access all fields via 'result' object:
        - {{ result.data_file.items[current_index].version }}
        - {{ result.test_inputs[current_index].scenario_id }}
        - {{ result.test_cases[0].evaluation_specs }}
        - {{ result.evaluation.result.details }}
        """
        data_file = request.data_file
        if not data_file.output_config:
            return BatchOutputResultResult(success_count=0, failure_count=0)

        timestamp_dir = datetime.now().strftime("%Y-%m-%d_%H%M%S")

        # Convert entire request to template-friendly dict once
        result_dict = _to_template_dict(request)

        success_count = 0
        failure_count = 0
        outputs: list[tuple[str, str]] = []

        for i, test_input in enumerate(request.test_inputs):
            item_id = (
                data_file.items[i].scenario_id
                if i < len(data_file.items)
                else f"item_{i}"
            )

            result_data: dict[str, Any] = {
                "result": result_dict,
                "current_index": i,
                "item_id": item_id,
            }

            output_result = self.execute(
                OutputResultRequest(
                    output_config=data_file.output_config,
                    item_id=item_id,
                    result_data=result_data,
                    timestamp_dir=timestamp_dir,
                )
            )

            if output_result.write_response.success:
                success_count += 1
                path = output_result.write_response.output_path
                outputs.append((item_id, path.value if path else ""))
            else:
                failure_count += 1
                outputs.append((item_id, output_result.write_response.error_message or ""))

            print(output_result.stdout_output)

        return BatchOutputResultResult(
            success_count=success_count,
            failure_count=failure_count,
            outputs=tuple(outputs),
        )

    def _generate_stdout_output(
        self,
        request: OutputResultRequest,
        write_response: ResultWriteResponse,
    ) -> str:
        """Generate the stdout output."""
        lines = [f"Item: {request.item_id}"]

        if write_response.success and write_response.output_path:
            lines.append(f"Output: {write_response.output_path.value}")
        elif not write_response.success:
            lines.append(f"Error: {write_response.error_message}")

        # Extract evaluation results from result.evaluation.result.details
        result_data = request.result_data
        if "result" in result_data:
            result = result_data["result"]
            current_index = result_data.get("current_index", 0)
            evaluation = result.get("evaluation")
            if evaluation and evaluation.get("result"):
                details = evaluation["result"].get("details", [])
                # Find the detail for current test case
                test_cases = result.get("test_cases", [])
                if current_index < len(test_cases):
                    tc_id = test_cases[current_index].get("id")
                    for detail in details:
                        if detail.get("test_case_id") == tc_id:
                            for mr in detail.get("metric_results", []):
                                sdk = mr.get("sdk", "unknown")
                                metric = mr.get("metric", "unknown")
                                score = mr.get("score", "N/A")
                                lines.append(f"  - {sdk}:{metric} = {score}")
                            break

        return "\n".join(lines)
