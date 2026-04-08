"""Property tests for batch pipeline engine.

Property 8: Pipeline format compatibility validation
Property 9: Pipeline failure preserves completed step outputs
Property 10: Pipeline definition round-trip

Validates: Requirements 4.1, 4.4, 4.5
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import tempfile
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from app.pipeline import (
    PipelineStep, PipelineDefinition, PipelineStore,
    PipelineValidationError, PipelineExecutionError,
    validate_pipeline, execute_pipeline, FORMAT_MAP,
)

# Build valid chains: sequences where output of step N feeds input of step N+1
_VALID_CHAINS = [
    ("pdf", [PipelineStep("pdf_ocr"), PipelineStep("pdf_compress")]),
    ("pdf", [PipelineStep("pdf_ocr"), PipelineStep("pdf_compress"), PipelineStep("pdf_to_png")]),
    ("pdf", [PipelineStep("pdf_split"), PipelineStep("pdf_compress")]),
    ("png", [PipelineStep("png_to_jpeg")]),
    ("jpeg", [PipelineStep("jpeg_to_png")]),
    ("png", [PipelineStep("images_to_pdf"), PipelineStep("pdf_compress")]),
]

_INVALID_CHAINS = [
    ("png", [PipelineStep("pdf_merge")]),  # png can't go into pdf_merge
    ("pdf", [PipelineStep("pdf_to_png"), PipelineStep("pdf_compress")]),  # png can't go into pdf_compress
    ("jpeg", [PipelineStep("pdf_ocr")]),  # jpeg can't go into pdf_ocr
]


# ---------------------------------------------------------------------------
# Property 8: Pipeline format compatibility validation
# Feature: hestia, Property 8: Pipeline format compatibility validation
# ---------------------------------------------------------------------------

@given(chain=st.sampled_from(_VALID_CHAINS))
@settings(max_examples=50)
def test_valid_chains_accepted(chain):
    input_fmt, steps = chain
    assert validate_pipeline(steps, input_fmt) is True


@given(chain=st.sampled_from(_INVALID_CHAINS))
@settings(max_examples=50)
def test_invalid_chains_rejected(chain):
    input_fmt, steps = chain
    with pytest.raises(PipelineValidationError):
        validate_pipeline(steps, input_fmt)


# ---------------------------------------------------------------------------
# Property 9: Pipeline failure preserves completed step outputs
# Feature: hestia, Property 9: Pipeline failure preserves completed step outputs
# ---------------------------------------------------------------------------

@given(fail_at=st.integers(min_value=1, max_value=2))
@settings(max_examples=50)
def test_failure_preserves_completed_outputs(fail_at: int):
    steps = [PipelineStep("pdf_ocr"), PipelineStep("pdf_compress"), PipelineStep("pdf_to_png")]
    call_count = 0

    def executor(op, data, params):
        nonlocal call_count
        if call_count == fail_at:
            raise RuntimeError("simulated failure")
        call_count += 1
        return b"output_" + str(call_count).encode()

    with pytest.raises(PipelineExecutionError) as exc_info:
        execute_pipeline(steps, b"input", "pdf", executor)

    assert exc_info.value.step_index == fail_at
    assert len(exc_info.value.completed_outputs) == fail_at


# ---------------------------------------------------------------------------
# Property 10: Pipeline definition round-trip
# Feature: hestia, Property 10: Pipeline definition round-trip
# ---------------------------------------------------------------------------

_op_names = st.sampled_from(list(FORMAT_MAP.keys()))
_steps_st = st.lists(
    st.builds(PipelineStep, operation=_op_names, parameters=st.just({})),
    min_size=1, max_size=5,
)
_names = st.text(
    alphabet=st.characters(min_codepoint=48, max_codepoint=122),
    min_size=1, max_size=20,
)


@given(name=_names, steps=_steps_st)
@settings(max_examples=100)
def test_pipeline_definition_roundtrip(name: str, steps: list[PipelineStep]):
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = f.name

    store = PipelineStore(path)
    defn = PipelineDefinition(name=name, steps=steps)
    store.save(defn)

    # Reload from disk
    store2 = PipelineStore(path)
    loaded = store2.load(name)

    assert loaded is not None
    assert loaded.name == name
    assert len(loaded.steps) == len(steps)
    for orig, got in zip(steps, loaded.steps):
        assert orig.operation == got.operation
        assert orig.parameters == got.parameters

    os.unlink(path)
