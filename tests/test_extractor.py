"""
Tests for src/extractor.py: one test per Task 1 function.

The real Gemma model is never loaded here. Tests pass in `fake_llm`, which
returns a fixed answer instantly, so the tests run in seconds (locally and
in GitHub Actions) and always give the same result.

Run with:  python -m pytest -v
"""

from pathlib import Path

import pytest
import yaml

from src import extractor

PDF_V0 = Path("inputs/docker-cis-v0.pdf")
PDF_V1 = Path("inputs/docker-cis-v1.pdf")


def fake_llm(prompt):
    """Stand-in for Gemma: always gives the same element name."""
    return "Element: **The test element.**"


# Test 1: load_documents
def test_load_documents_rejects_fake_pdf(tmp_path):
    fake = tmp_path / "not_really.pdf"
    fake.write_text("I am a text file pretending to be a PDF")
    with pytest.raises(ValueError):
        extractor.load_documents(fake, PDF_V0)


# Test 2: build_zero_shot_prompt
def test_zero_shot_prompt_has_text_and_no_example():
    prompt = extractor.build_zero_shot_prompt("4.1 Ensure a user exists")
    assert isinstance(prompt, str)
    assert "4.1 Ensure a user exists" in prompt
    assert "Example" not in prompt


# Test 3: build_few_shot_prompt
def test_few_shot_prompt_includes_example():
    prompt = extractor.build_few_shot_prompt("4.1 Ensure a user exists")
    assert isinstance(prompt, str)
    assert prompt.count("Requirement:") > 1  # examples + the real one
    assert "4.1 Ensure a user exists" in prompt


# Test 4: build_chain_of_thought_prompt
def test_chain_of_thought_prompt_asks_for_steps():
    prompt = extractor.build_chain_of_thought_prompt("4.1 Ensure a user exists")
    assert isinstance(prompt, str)
    assert "step by step" in prompt
    assert "Step 1" in prompt


# Test 5: extract_kdes
def test_extract_kdes_writes_yaml_named_after_document(tmp_path):
    text, _ = extractor.load_documents(PDF_V0, PDF_V1)
    kdes = extractor.extract_kdes(text, "docker-cis-v0.pdf",
                                  output_dir=tmp_path, llm=fake_llm)
    yaml_file = tmp_path / "docker-cis-v0-kdes.yaml"
    assert yaml_file.exists()
    saved = yaml.safe_load(yaml_file.read_text())
    assert saved == kdes
    # The fake LLM names every requirement "test element", so they all group
    # into one element, and its messy reply is cleaned up.
    assert saved["element1"]["name"] == "test element"
    assert len(saved["element1"]["requirements"]) > 100


# Test 6: dump_llm_outputs
def test_dump_llm_outputs_uses_required_format(tmp_path):
    records = [{"llm_name": extractor.LLM_NAME, "prompt": "P",
                "prompt_type": "zero-shot", "output": "O"}]
    out = extractor.dump_llm_outputs(records, tmp_path / "log.txt")
    content = Path(out).read_text()
    for header in ["*LLM Name*", "*Prompt Used*", "*Prompt Type*", "*LLM Output*"]:
        assert header in content
