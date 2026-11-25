# COMP 5700 Secure Software Process: Course Project (Fall 2026)

Detects changes between two versions of the CIS Docker Benchmark and runs
Hadolint on a set of Dockerfiles based on what changed.

## Team

| Name | BannerID | Auburn email |
|---|---|---|
| Aubrey Foote | 904289502 | caf0074@auburn.edu |

## LLM used (Task 1)

**Gemma-3-1B** (`google/gemma-3-1b-it`). It is a gated model: accept its license
at https://huggingface.co/google/gemma-3-1b-it and run `hf auth login` before the first run.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
brew install hadolint          # macOS; on Linux, download the binary from the Hadolint releases page
```

Put the Dockerfile dataset in a folder named `dockerfiles/` (it is not stored in this repo).

## How to run

```bash
python main.py inputs/docker-cis-v0.pdf inputs/docker-cis-v1.pdf
```

Options: `--dockerfiles <folder>` (default `dockerfiles`) and `--output <folder>` (default `outputs`).

Results are written to `outputs/<doc1>_vs_<doc2>/`:

| File | Task | Contents |
|---|---|---|
| `<doc>-kdes.yaml` | 1 | Key data elements and their requirements |
| `llm-outputs.txt` | 1 | Every prompt, prompt type and LLM answer |
| `name-diffs.txt` | 2 | Element names that differ |
| `requirement-diffs.txt` | 2 | `NAME,REQU` lines for requirements that differ |
| `hadolint-rules.txt` | 3 | Mapped rules, `NO DIFFERENCES FOUND`, or `NO MAPPING FOUND` |
| `hadolint-results.csv` | 3 | `FilePath, DefaultSeverity, RULEID, COUNT` |

### Binary

```bash
pyinstaller --onefile --name ssp-project --collect-all transformers main.py
./dist/ssp-project inputs/docker-cis-v1.pdf inputs/docker-cis-v2.pdf
```

## Tests

```bash
python -m pytest -v
```

13 tests, one per function. They use a stand-in for the LLM so they run in
seconds without downloading Gemma. GitHub Actions (`.github/workflows/tests.yml`)
runs them on every push and pull request; the log is saved as the `test-log` artifact.

## Design notes

- **Only the recommendation titles go to the LLM.** Each PDF is ~290 pages, but its
  ~118 numbered recommendations (e.g. `4.1 Ensure that a user for the container has
  been created`) are the requirements. They are extracted with a regex first.
- **One requirement per prompt, three prompts vote.** Gemma-3-1B could not reliably
  group many requirements at once, so each prompt names the data element for a single
  requirement. The zero-shot, few-shot and chain-of-thought answers vote on the name,
  and requirements with the same name form one element.
- **Deterministic output.** Greedy decoding (`do_sample=False`) and an answer cache
  (`outputs/llm-cache.json`) mean the same PDF always produces the same KDEs, so
  comparing a document with itself reports no differences.
- **Only Dockerfile-related CIS checks are mapped** to Hadolint (mostly CIS section 4,
  such as 4.9 "COPY instead of ADD" → DL3020). Host and daemon settings have no Dockerfile rule.

## Limitations

- A 1B model sometimes picks vague element names (e.g. `permissions`), which can group
  unrelated requirements together.
- Requirement-to-rule mapping uses phrases from the CIS titles, so a reworded title
  in a future benchmark version may need a new phrase.
