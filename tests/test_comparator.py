"""Tests for src/comparator.py: one test per Task 2 function."""

import pytest
import yaml

from src import comparator

FILE_A = {
    "element1": {"name": "docker daemon", "requirements": ["1.1.3 Audit daemon"]},
    "element2": {"name": "container user", "requirements": ["4.1 Create a user"]},
}
FILE_B = {
    "element1": {"name": "docker daemon",
                 "requirements": ["1.1.3 Audit daemon", "2.1 Run rootless"]},
    "element2": {"name": "swarm mode", "requirements": ["5.1 Disable swarm"]},
}


# Test 1: load_yaml_files
def test_load_yaml_files_rejects_bad_structure(tmp_path):
    good = tmp_path / "good.yaml"
    good.write_text(yaml.safe_dump(FILE_A))
    bad = tmp_path / "bad.yaml"
    bad.write_text("just a string")
    with pytest.raises(ValueError):
        comparator.load_yaml_files(good, bad)


# Test 2: compare_element_names
def test_compare_element_names(tmp_path):
    out = comparator.compare_element_names(FILE_A, FILE_B, tmp_path / "names.txt")
    assert out.read_text().splitlines() == ["container user", "swarm mode"]

    same = comparator.compare_element_names(FILE_A, FILE_A, tmp_path / "same.txt")
    assert same.read_text().strip() == comparator.NO_NAME_DIFFS


# Test 3: compare_element_requirements
def test_compare_element_requirements(tmp_path):
    out = comparator.compare_element_requirements(FILE_A, FILE_B, tmp_path / "reqs.txt")
    assert out.read_text().splitlines() == [
        "container user,4.1 Create a user",
        "docker daemon,2.1 Run rootless",
        "swarm mode,5.1 Disable swarm",
    ]

    same = comparator.compare_element_requirements(FILE_A, FILE_A, tmp_path / "same.txt")
    assert same.read_text().strip() == comparator.NO_REQ_DIFFS
