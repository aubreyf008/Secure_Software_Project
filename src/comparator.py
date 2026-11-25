"""
Task 2: Comparator

Compares the two KDE YAML files from Task 1 and writes two TEXT files:
one for element names that differ, one for requirements that differ.
"""

from pathlib import Path

import yaml

NO_NAME_DIFFS = "NO DIFFERENCES IN REGARDS TO ELEMENT NAMES"
NO_REQ_DIFFS = "NO DIFFERENCES IN REGARDS TO ELEMENT REQUIREMENTS"


def _read_kde_yaml(path):
    """Load and validate one KDE YAML file."""
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"No file found at: {p}")
    if p.suffix.lower() not in (".yaml", ".yml"):
        raise ValueError(f"Expected a .yaml file, got: {p.name}")

    # safe_load only builds plain data (dicts, lists, strings), never Python
    # objects, so a malicious YAML file can't run code.
    data = yaml.safe_load(p.read_text())

    if not isinstance(data, dict):
        raise ValueError(f"{p.name} is not a KDE mapping.")
    for key, element in data.items():
        if not isinstance(element, dict) or "name" not in element \
                or not isinstance(element.get("requirements"), list):
            raise ValueError(f"{p.name}: '{key}' needs a name and a requirements list.")
    return data


def load_yaml_files(yaml_path_1, yaml_path_2):
    """Return the two validated KDE dictionaries as (data_1, data_2)."""
    return _read_kde_yaml(yaml_path_1), _read_kde_yaml(yaml_path_2)


def _by_name(data):
    """{"element1": {"name": n, "requirements": [...]}} -> {n: {req, ...}}"""
    return {str(e["name"]): set(e["requirements"]) for e in data.values()}


def _write_lines(lines, empty_message, output_path):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n" if lines else empty_message + "\n")
    return output_path


def compare_element_names(data_1, data_2, output_path):
    """
    Write the element names that appear in only one of the two files.
    Returns the path of the TEXT file written.
    """
    names_1, names_2 = set(_by_name(data_1)), set(_by_name(data_2))
    # ^ is symmetric difference: names in one set but not both
    different = sorted(names_1 ^ names_2)
    return _write_lines(different, NO_NAME_DIFFS, output_path)


def compare_element_requirements(data_1, data_2, output_path):
    """
    Write one NAME,REQU line for every requirement that is not shared by the
    same element in both files. An element found in only one file counts too,
    so all of its requirements are listed.
    Returns the path of the TEXT file written.
    """
    elements_1, elements_2 = _by_name(data_1), _by_name(data_2)
    lines = []
    for name in sorted(set(elements_1) | set(elements_2)):
        reqs_1 = elements_1.get(name, set())
        reqs_2 = elements_2.get(name, set())
        for req in sorted(reqs_1 ^ reqs_2):
            lines.append(f"{name},{req}")
    return _write_lines(lines, NO_REQ_DIFFS, output_path)
