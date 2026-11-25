"""
Runs the full pipeline on two CIS Docker Benchmark PDFs:

    python main.py inputs/docker-cis-v0.pdf inputs/docker-cis-v1.pdf

Results go in outputs/<doc1>_vs_<doc2>/ :
    <doc>-kdes.yaml          Task 1  KDEs per document
    llm-outputs.txt          Task 1  every prompt and LLM answer
    name-diffs.txt           Task 2  element name differences
    requirement-diffs.txt    Task 2  element requirement differences
    hadolint-rules.txt       Task 3  mapped rules / NO DIFFERENCES / NO MAPPING
    hadolint-results.csv     Task 3  scan summary
"""

import argparse
import sys
from pathlib import Path

from src import comparator, executor, extractor


def main(argv=None):
    parser = argparse.ArgumentParser(description="CIS Docker Benchmark change detector")
    parser.add_argument("pdf_1", help="first CIS Docker Benchmark PDF")
    parser.add_argument("pdf_2", help="second CIS Docker Benchmark PDF")
    parser.add_argument("--dockerfiles", default="dockerfiles",
                        help="folder of Dockerfiles to scan (default: dockerfiles)")
    parser.add_argument("--output", default="outputs",
                        help="where results are written (default: outputs)")
    args = parser.parse_args(argv)

    name_1, name_2 = Path(args.pdf_1).stem, Path(args.pdf_2).stem
    out_dir = Path(args.output) / f"{name_1}_vs_{name_2}"

    try:
        # Task 1: Extractor
        print("[1/3] Extracting KDEs with Gemma-3-1B (this can take several minutes)...")
        text_1, text_2 = extractor.load_documents(args.pdf_1, args.pdf_2)
        records = []
        extractor.extract_kdes(text_1, name_1, out_dir, records=records)
        if name_2 != name_1:  # same PDF twice -> one YAML is enough
            extractor.extract_kdes(text_2, name_2, out_dir, records=records)
        extractor.dump_llm_outputs(records, out_dir / "llm-outputs.txt")

        # Task 2: Comparator
        print("[2/3] Comparing KDEs...")
        data_1, data_2 = comparator.load_yaml_files(out_dir / f"{name_1}-kdes.yaml",
                                                    out_dir / f"{name_2}-kdes.yaml")
        names_file = comparator.compare_element_names(
            data_1, data_2, out_dir / "name-diffs.txt")
        reqs_file = comparator.compare_element_requirements(
            data_1, data_2, out_dir / "requirement-diffs.txt")

        # Task 3: Executor
        print("[3/3] Mapping differences and running Hadolint...")
        names_text, reqs_text = executor.load_text_files(names_file, reqs_file)
        rules_file = executor.map_differences_to_rules(
            names_text, reqs_text, out_dir / "hadolint-rules.txt")
        results = executor.run_hadolint(rules_file, args.dockerfiles)
        csv_file = executor.write_results_csv(results, out_dir / "hadolint-results.csv")

    except (FileNotFoundError, ValueError, RuntimeError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    print(f"Done. Rules: {rules_file.read_text().strip().splitlines()}")
    print(f"Results in {out_dir}/ (CSV: {csv_file.name}, {len(results)} findings)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
