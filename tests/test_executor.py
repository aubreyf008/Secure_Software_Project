"""Tests for src/executor.py: one test per Task 3 function."""

import shutil

import pandas as pd
import pytest

from src import executor
from src.comparator import NO_NAME_DIFFS, NO_REQ_DIFFS

needs_hadolint = pytest.mark.skipif(shutil.which("hadolint") is None,
                                    reason="hadolint is not installed")

SAMPLE_DOCKERFILE = (
    "FROM ubuntu:latest\n"
    "ADD app.py /app/\n"
    "USER root\n"
)


# Test 1: load_text_files
def test_load_text_files_rejects_missing_file(tmp_path):
    good = tmp_path / "names.txt"
    good.write_text(NO_NAME_DIFFS)
    with pytest.raises(FileNotFoundError):
        executor.load_text_files(good, tmp_path / "missing.txt")


# Test 2: map_differences_to_rules (all three possible outcomes)
def test_map_differences_to_rules(tmp_path):
    out = tmp_path / "rules.txt"

    executor.map_differences_to_rules(NO_NAME_DIFFS, NO_REQ_DIFFS, out)
    assert out.read_text().strip() == executor.NO_DIFFERENCES

    executor.map_differences_to_rules(
        NO_NAME_DIFFS, "docker socket,1.1.9 Ensure auditing is configured\n", out)
    assert out.read_text().strip() == executor.NO_MAPPING

    executor.map_differences_to_rules(
        NO_NAME_DIFFS,
        "copy,4.9 Ensure that COPY is used instead of ADD in Dockerfiles\n", out)
    assert out.read_text().strip() == "DL3020"


# Test 3: run_hadolint
@needs_hadolint
def test_run_hadolint_keeps_only_listed_rules(tmp_path):
    (tmp_path / "files").mkdir()
    (tmp_path / "files" / "Dockerfile").write_text(SAMPLE_DOCKERFILE)
    rules = tmp_path / "rules.txt"
    rules.write_text("DL3020\n")

    df = executor.run_hadolint(rules, tmp_path / "files")
    assert isinstance(df, pd.DataFrame)
    assert list(df["RULEID"].unique()) == ["DL3020"]


# Test 4: write_results_csv
def test_write_results_csv_counts_findings(tmp_path):
    df = pd.DataFrame({
        "FilePath": ["a/Dockerfile", "a/Dockerfile", "b/Dockerfile"],
        "DefaultSeverity": ["error", "error", "warning"],
        "RULEID": ["DL3020", "DL3020", "DL3007"],
    })
    out = executor.write_results_csv(df, tmp_path / "results.csv")
    csv = pd.read_csv(out)
    assert list(csv.columns) == executor.CSV_COLUMNS
    assert csv.loc[csv["RULEID"] == "DL3020", "COUNT"].item() == 2
