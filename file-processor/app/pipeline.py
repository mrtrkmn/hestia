"""Batch pipeline engine.

Validates pipeline definitions, executes steps sequentially,
preserves completed outputs on failure, and supports named save/load.

Requirements: 4.1, 4.2, 4.3, 4.4, 4.5
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

# Format compatibility: operation -> (accepted_inputs, output_format)
FORMAT_MAP: dict[str, tuple[set[str], str]] = {
    "pdf_merge": ({"pdf"}, "pdf"),
    "pdf_split": ({"pdf"}, "pdf"),
    "pdf_ocr": ({"pdf"}, "pdf"),
    "pdf_compress": ({"pdf"}, "pdf"),
    "pdf_to_png": ({"pdf"}, "png"),
    "pdf_to_jpeg": ({"pdf"}, "jpeg"),
    "images_to_pdf": ({"png", "jpeg"}, "pdf"),
    "png_to_jpeg": ({"png"}, "jpeg"),
    "jpeg_to_png": ({"jpeg"}, "png"),
    "video_transcode": ({"mp4", "mkv", "avi", "webm"}, "mp4"),
    "audio_transcode": ({"mp3", "flac", "wav", "aac", "ogg"}, "mp3"),
}


@dataclass
class PipelineStep:
    operation: str
    parameters: dict = field(default_factory=dict)


@dataclass
class PipelineDefinition:
    name: str
    steps: list[PipelineStep]


class PipelineValidationError(Exception):
    def __init__(self, step_index: int, reason: str) -> None:
        self.step_index = step_index
        self.reason = reason
        super().__init__(f"Step {step_index}: {reason}")


class PipelineExecutionError(Exception):
    def __init__(self, step_index: int, reason: str, completed_outputs: list[bytes]) -> None:
        self.step_index = step_index
        self.reason = reason
        self.completed_outputs = completed_outputs
        super().__init__(f"Step {step_index} failed: {reason}")


def validate_pipeline(steps: list[PipelineStep], input_format: str) -> bool:
    """Validate that each step's output is compatible with the next step's input.

    Returns True if valid, raises PipelineValidationError otherwise.
    """
    current_format = input_format
    for i, step in enumerate(steps):
        info = FORMAT_MAP.get(step.operation)
        if info is None:
            raise PipelineValidationError(i, f"Unknown operation: {step.operation}")
        accepted_inputs, output_format = info
        if current_format not in accepted_inputs:
            raise PipelineValidationError(
                i, f"Format {current_format} not accepted by {step.operation} (needs {accepted_inputs})"
            )
        current_format = output_format
    return True


def execute_pipeline(
    steps: list[PipelineStep],
    input_data: bytes,
    input_format: str,
    step_executor,
    progress_callback=None,
) -> list[bytes]:
    """Execute pipeline steps sequentially. Returns list of outputs per step.

    On failure, raises PipelineExecutionError with completed outputs preserved.
    """
    validate_pipeline(steps, input_format)
    outputs: list[bytes] = []
    current_data = input_data

    for i, step in enumerate(steps):
        try:
            result = step_executor(step.operation, current_data, step.parameters)
            outputs.append(result)
            current_data = result
            if progress_callback:
                progress_callback(i, len(steps))
        except Exception as e:
            raise PipelineExecutionError(i, str(e), outputs)

    return outputs


class PipelineStore:
    """Save/load named pipeline definitions to a JSON file."""

    def __init__(self, path: str = "/tmp/hub-pipelines.json") -> None:
        self._path = Path(path)
        self._data: dict[str, dict] = {}
        if self._path.exists():
            text = self._path.read_text().strip()
            if text:
                self._data = json.loads(text)

    def _flush(self) -> None:
        self._path.write_text(json.dumps(self._data))

    def save(self, definition: PipelineDefinition) -> None:
        self._data[definition.name] = {
            "name": definition.name,
            "steps": [{"operation": s.operation, "parameters": s.parameters} for s in definition.steps],
        }
        self._flush()

    def load(self, name: str) -> PipelineDefinition | None:
        raw = self._data.get(name)
        if raw is None:
            return None
        return PipelineDefinition(
            name=raw["name"],
            steps=[PipelineStep(operation=s["operation"], parameters=s["parameters"]) for s in raw["steps"]],
        )

    def delete(self, name: str) -> bool:
        if name in self._data:
            del self._data[name]
            self._flush()
            return True
        return False

    def list_names(self) -> list[str]:
        return list(self._data.keys())
