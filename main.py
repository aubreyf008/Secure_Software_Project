"""
Entry point: runs the whole pipeline on two PDFs.

    python main.py inputs/docker-cis-v0.pdf inputs/docker-cis-v1.pdf

This is also the file PyInstaller will turn into the binary in Task 4.

TODO (you):
  1. Read the two PDF paths from the command line (look up `argparse`).
  2. Task 1: load_documents -> build prompts -> extract_kdes -> dump_llm_outputs
  3. Task 2: load_yaml_files -> compare_element_names / compare_element_requirements
  4. Task 3: load_text_files -> map_differences_to_rules -> run_hadolint -> write_results_csv
"""


def main():
    raise NotImplementedError


if __name__ == "__main__":
    main()
