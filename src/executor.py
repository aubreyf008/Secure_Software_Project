"""
Task 3: Executor  (20% of the grade)

Goal: turn the Task 2 differences into Hadolint rules, run Hadolint on the
course Dockerfiles, and save the results to a CSV.

Hadolint rule list: https://github.com/hadolint/hadolint#rules
Map only CIS rules that relate to Dockerfiles.
"""


def load_text_files(text_path_1, text_path_2):
    """
    Take the two TEXT files from Task 2 as input (validate them).
    Returns: their contents.
    """
    raise NotImplementedError


def map_differences_to_rules(names_text, requirements_text, output_path):
    """
    Decide whether there is at least one difference, then write a TEXT file
    containing exactly ONE of:
      - NO DIFFERENCES FOUND
      - NO MAPPING FOUND          (differences exist, but no rule matches)
      - the Hadolint rule IDs that map to the differences (e.g. one per line)
    """
    raise NotImplementedError


def run_hadolint(rules_file_path, dockerfiles_dir):
    """
    Run the Hadolint command-line tool on every Dockerfile in dockerfiles_dir.
      - If the rules file says NO DIFFERENCES FOUND or NO MAPPING FOUND,
        run with ALL rules.
      - Otherwise, run ONLY the rules listed in the file.
    Hint: look up `subprocess.run` and Hadolint's `--format json` option.

    Returns: a pandas DataFrame of the scan results.
    """
    raise NotImplementedError


def write_results_csv(results_df, output_path):
    """
    Write a CSV with exactly these headers:
        FilePath, DefaultSeverity, RULEID, COUNT
    built from the DataFrame returned by run_hadolint.
    """
    raise NotImplementedError
