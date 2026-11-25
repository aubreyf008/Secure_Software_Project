"""
Task 2: Comparator  (30% of the grade)

Goal: compare the two YAML files that Task 1 produced.
This part is plain Python (dictionaries and sets), so no LLM is needed.
"""


def load_yaml_files(yaml_path_1, yaml_path_2):
    """
    Take the two YAML files from Task 1 as input (validate them too).
    Returns: a tuple (data_1, data_2) of dictionaries.
    """
    raise NotImplementedError


def compare_element_names(data_1, data_2, output_path):
    """
    Find KDE *names* that are in one file but not the other.
    Write them to a TEXT file.
    If there are none, write exactly:
        NO DIFFERENCES IN REGARDS TO ELEMENT NAMES
    """
    raise NotImplementedError


def compare_element_requirements(data_1, data_2, output_path):
    """
    Find differences in *requirements* for each KDE.
    Write each one as a tuple line:  NAME,REQU
    If there are none, write exactly:
        NO DIFFERENCES IN REGARDS TO ELEMENT REQUIREMENTS
    """
    raise NotImplementedError
