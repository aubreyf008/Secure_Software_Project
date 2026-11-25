"""
Task 3: Executor

Maps the Task 2 differences to Hadolint rules, runs Hadolint on the course
Dockerfiles, and saves a CSV summary.
"""

import json
import re
import shutil
import subprocess
from pathlib import Path

import pandas as pd

from src.comparator import NO_NAME_DIFFS, NO_REQ_DIFFS

NO_DIFFERENCES = "NO DIFFERENCES FOUND"
NO_MAPPING = "NO MAPPING FOUND"
CSV_COLUMNS = ["FilePath", "DefaultSeverity", "RULEID", "COUNT"]

# CIS recommendations that apply to Dockerfiles (mostly CIS section 4,
# "Container Images and Build File"), each matched by a phrase from its title,
# paired with the Hadolint rules that check the same thing.
CIS_TO_HADOLINT = [
    ("user for the container", ["DL3002"]),          # 4.1  last USER not root
    ("trusted base images", ["DL3006", "DL3026"]),    # 4.2  tagged, allowed registry
    ("unnecessary packages", ["DL3015"]),             # 4.3  --no-install-recommends
    ("healthcheck", ["DL3057", "DL3012"]),            # 4.6  HEALTHCHECK present, once
    ("update instructions", ["DL3009"]),              # 4.7  apt-get update cleanup
    ("instead of add", ["DL3020"]),                   # 4.9  COPY instead of ADD
    ("secrets are not stored", ["DL3064"]),           # 4.10 no secrets in ARG/ENV
    ("verified packages", ["DL3008", "DL3013"]),      # 4.11 pinned package versions
    ("sshd", ["DL3001"]),                             # 5.7  no ssh in containers
    ("latest version of their image", ["DL3007"]),    # 5.28 don't use :latest
]


def _read_text_file(path):
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"No file found at: {p}")
    if p.suffix.lower() != ".txt":
        raise ValueError(f"Expected a .txt file, got: {p.name}")
    return p.read_text()


def load_text_files(text_path_1, text_path_2):
    """Return the contents of the two Task 2 TEXT files (names, requirements)."""
    return _read_text_file(text_path_1), _read_text_file(text_path_2)


def map_differences_to_rules(names_text, requirements_text, output_path):
    """
    Write a TEXT file with exactly one of:
      NO DIFFERENCES FOUND, NO MAPPING FOUND, or the matched rule IDs (one per line).
    Returns the path of the file written.
    """
    no_name_diffs = names_text.strip() == NO_NAME_DIFFS
    no_req_diffs = requirements_text.strip() == NO_REQ_DIFFS

    if no_name_diffs and no_req_diffs:
        content = NO_DIFFERENCES
    else:
        diff_text = ""
        if not no_name_diffs:
            diff_text += names_text
        if not no_req_diffs:
            diff_text += requirements_text
        diff_text = diff_text.lower()

        rules = set()
        for phrase, rule_ids in CIS_TO_HADOLINT:
            if phrase in diff_text:
                rules.update(rule_ids)
        content = "\n".join(sorted(rules)) if rules else NO_MAPPING

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content + "\n")
    return output_path


def _find_dockerfiles(dockerfiles_dir):
    """Files whose name mentions 'dockerfile'; if none, every regular file."""
    root = Path(dockerfiles_dir)
    if not root.is_dir():
        raise FileNotFoundError(f"No Dockerfile folder at: {root}")
    files = [p for p in root.rglob("*")
             if p.is_file() and not p.name.startswith(".")]
    named = [p for p in files if "dockerfile" in p.name.lower()]
    return sorted(named or files)


def run_hadolint(rules_file_path, dockerfiles_dir):
    """
    Run Hadolint on every Dockerfile. If the rules file says NO DIFFERENCES
    FOUND or NO MAPPING FOUND, keep all rules; otherwise keep only the listed ones.
    Returns a DataFrame with one row per finding.
    """
    if shutil.which("hadolint") is None:
        raise RuntimeError("hadolint is not installed or not on PATH.")

    rules_text = Path(rules_file_path).read_text().strip()
    if rules_text in (NO_DIFFERENCES, NO_MAPPING):
        selected_rules = None  # None means "all rules"
    else:
        selected_rules = set(re.findall(r"\bDL\d{4}\b", rules_text))

    dockerfiles = _find_dockerfiles(dockerfiles_dir)
    findings = []
    # Scan in batches so a large dataset doesn't exceed the command-line length.
    for start in range(0, len(dockerfiles), 200):
        batch = [str(p) for p in dockerfiles[start:start + 200]]
        # Passing a list (not one string) means file names are never run by a
        # shell, so a weird file name can't inject a command.
        result = subprocess.run(
            ["hadolint", "--format", "json", "--no-fail", *batch],
            capture_output=True, text=True,
        )
        if result.stdout.strip():
            findings.extend(json.loads(result.stdout))

    df = pd.DataFrame(findings, columns=["file", "code", "level", "line", "message"])
    df = df.rename(columns={"file": "FilePath", "code": "RULEID",
                            "level": "DefaultSeverity", "line": "Line",
                            "message": "Message"})
    if selected_rules is not None:
        df = df[df["RULEID"].isin(selected_rules)]
    return df.reset_index(drop=True)


def write_results_csv(results_df, output_path):
    """
    Count findings per file, severity and rule, and save them as a CSV with
    the headers FilePath, DefaultSeverity, RULEID, COUNT.
    Returns the path of the CSV written.
    """
    summary = (results_df.groupby(["FilePath", "DefaultSeverity", "RULEID"])
               .size().reset_index(name="COUNT"))
    summary = summary.reindex(columns=CSV_COLUMNS)  # keeps headers even if empty

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(output_path, index=False)
    return output_path
