"""
Task 1: Extractor  (40% of the grade)

Reads two CIS Docker Benchmark PDFs, asks the Gemma-3-1B LLM to find the
"key data elements" (KDEs) in each one, and saves the results as YAML.

How it works, start to finish:
  1. load_documents()          -> validate both PDFs and pull out their text
  2. extract_requirements()    -> keep only the numbered recommendations
                                  (e.g. "4.1 Ensure that a user ... created").
                                  The PDFs are ~290 pages, but the actual
                                  requirements are only ~118 lines.
  3. build_*_prompt()          -> wrap ONE requirement in a zero-shot,
                                  few-shot, or chain-of-thought prompt that
                                  asks "what data element is this about?"
  4. extract_kdes()            -> ask Gemma with all three prompt styles,
                                  let the three answers vote on a name, group
                                  requirements that share a name, and save
                                  <document>-kdes.yaml
  5. dump_llm_outputs()        -> write every prompt + answer to a TEXT log

Why one requirement per prompt? A 1B-parameter model is small. When it was
given 20 requirements at once and asked to group them, it mostly echoed the
ID numbers back. Asking one short question at a time gives real answers.
"""

import json
import logging
import re
from collections import Counter
from pathlib import Path

import yaml
from pypdf import PdfReader

# pypdf prints harmless "Ignoring wrong pointing object" warnings for these
# PDFs. Silence them so real errors are easier to spot.
logging.getLogger("pypdf").setLevel(logging.ERROR)

LLM_NAME = "google/gemma-3-1b-it"

# Saved LLM answers, so a requirement that appears in several PDFs is only
# sent to the model once. Same prompt in -> same answer out.
CACHE_PATH = Path("outputs/llm-cache.json")


# ===========================================================================
# Function 1: input validation
# ===========================================================================
def _read_pdf(path):
    """Validate ONE file and return its text. Raises an error on bad input."""
    if not isinstance(path, (str, Path)) or str(path).strip() == "":
        raise ValueError("A file path (string) is required.")

    p = Path(path)

    # Check 1: the file must exist
    if not p.is_file():
        raise FileNotFoundError(f"No file found at: {p}")

    # Check 2: the name must end in .pdf
    if p.suffix.lower() != ".pdf":
        raise ValueError(f"Expected a .pdf file, got: {p.name}")

    # Check 3: it must REALLY be a PDF. Every PDF starts with the bytes %PDF
    # (its "magic bytes"), so a renamed .exe or .txt file is caught here.
    with open(p, "rb") as f:
        if f.read(4) != b"%PDF":
            raise ValueError(f"{p.name} is not a valid PDF (bad file header).")

    # Check 4: it must contain text (a scanned image PDF would have none)
    reader = PdfReader(p)
    text = "\n".join((page.extract_text() or "") for page in reader.pages)
    if not text.strip():
        raise ValueError(f"{p.name} has no extractable text.")

    return text


def load_documents(path_1, path_2):
    """
    Take the two input PDF paths, validate them, and return their text.
    Returns: (text_1, text_2)
    """
    return _read_pdf(path_1), _read_pdf(path_2)


# ---------------------------------------------------------------------------
# Helper: keep only the numbered recommendations from a document's text
# ---------------------------------------------------------------------------
def extract_requirements(document_text):
    """
    Find every recommendation title, such as
        "4.1 Ensure that a user for the container has been created (Automated)"
    Titles can wrap onto a second or third line, so the pattern allows that.
    Each title appears twice (table of contents + body); the first copy wins.

    Returns: {"4.1": "Ensure that a user for the container has been created", ...}
    """
    pattern = re.compile(
        r"^\s*(\d+\.\d+(?:\.\d+)?)"           # the ID, e.g. 4.1 or 1.1.3
        r"\s+([A-Z][^\n]*(?:\n(?!\s*\d+\.\d)[^\n]*){0,2}?)"  # title (1-3 lines)
        r"\s*\((?:Automated|Manual)\)",        # every title ends like this
        re.MULTILINE,
    )
    requirements = {}
    for match in pattern.finditer(document_text):
        req_id = match.group(1)
        title = " ".join(match.group(2).split())       # join wrapped lines
        # A word split at a hyphen across lines ("shim-\nrunc") must not gain
        # a space, or the same title looks different between PDF versions.
        title = re.sub(r"(\w)- (\w)", r"\1-\2", title)
        title = re.sub(r"\s*\.{3,}.*", "", title)      # drop TOC dot leaders
        requirements.setdefault(req_id, title.rstrip(" ."))
    return requirements


# ===========================================================================
# Functions 2-4: prompt builders (each returns a STRING)
# ===========================================================================
# Each prompt is about ONE requirement. The model must answer with a short
# name for the data element that requirement protects or configures.
_TASK = (
    "You are a security analyst reading the CIS Docker Benchmark. "
    "A key data element is the thing a security requirement protects or "
    "configures, such as a file, a directory, a user, a network setting, "
    "a daemon, an image, or a log. "
    "Name the key data element in the requirement below using 2 to 4 words."
)

_EXAMPLES = [
    ("Ensure that the docker.service file ownership is set to root:root",
     "docker.service file"),
    ("Ensure that a user for the container has been created",
     "container user"),
    ("Ensure auditing is configured for the Docker daemon",
     "docker daemon"),
    ("Ensure that privileged ports are not mapped within containers",
     "container ports"),
]


def build_zero_shot_prompt(document_text):
    """Zero-shot: instructions only, no examples."""
    return (
        f"{_TASK}\n"
        "Reply with only the element name.\n\n"
        f"Requirement: {document_text}\n"
        "Element:"
    )


def build_few_shot_prompt(document_text):
    """Few-shot: the same instructions plus worked examples to imitate."""
    examples = "\n\n".join(f"Requirement: {req}\nElement: {element}"
                           for req, element in _EXAMPLES)
    return (
        f"{_TASK}\n"
        "Reply with only the element name, like the examples.\n\n"
        f"{examples}\n\n"
        f"Requirement: {document_text}\n"
        "Element:"
    )


def build_chain_of_thought_prompt(document_text):
    """Chain-of-thought: ask the model to reason briefly before answering."""
    return (
        f"{_TASK}\n"
        "Think step by step:\n"
        "Step 1: What action does the requirement ask for?\n"
        "Step 2: What file, setting, or component does that action apply to?\n"
        "Step 3: Name that component in 2 to 4 words.\n"
        "Write one or two short sentences of reasoning, then a final line "
        "that starts with 'Element:'.\n\n"
        f"Requirement: {document_text}"
    )


PROMPT_BUILDERS = {
    "zero-shot": build_zero_shot_prompt,
    "few-shot": build_few_shot_prompt,
    "chain-of-thought": build_chain_of_thought_prompt,
}

# Chain-of-thought needs room to reason; the others only need a few words.
MAX_NEW_TOKENS = {"zero-shot": 16, "few-shot": 16, "chain-of-thought": 120}


# ---------------------------------------------------------------------------
# The LLM itself (loaded once, only when first needed)
# ---------------------------------------------------------------------------
_generator = None


def gemma_generate(prompt, max_new_tokens=32):
    """
    Send one prompt to Gemma-3-1B and return its reply as a string.
    do_sample=False means "always pick the most likely next word", so the
    same prompt gives the same answer every run. That matters: comparing
    v1 against v1 must show NO differences.
    """
    global _generator
    if _generator is None:
        from transformers import pipeline  # imported here so tests stay fast
        _generator = pipeline("text-generation", model=LLM_NAME, dtype="auto")
    messages = [{"role": "user", "content": prompt}]
    result = _generator(messages, max_new_tokens=max_new_tokens, do_sample=False)
    return result[0]["generated_text"][-1]["content"]


def _clean_element_name(llm_output):
    """
    Turn the model's reply into a tidy element name.
      "Element: **The Docker daemon.**"  ->  "docker daemon"
    Returns "" if nothing usable is left.
    """
    text = llm_output
    # Chain-of-thought: use only what comes after the LAST "Element:"
    if re.search(r"(?i)element\s*:", text):
        text = re.split(r"(?i)element\s*:", text)[-1]
    text = text.strip().splitlines()[0] if text.strip() else ""
    text = re.sub(r"[*`\"'#]", "", text)          # markdown and quotes
    text = re.sub(r"(?i)^(the|a|an)\s+", "", text.strip())
    text = text.strip(" .:-,;").lower()
    words = text.split()
    return " ".join(words[:6])                     # keep names short


def _load_cache():
    if CACHE_PATH.exists():
        try:
            return json.loads(CACHE_PATH.read_text())
        except json.JSONDecodeError:
            return {}  # a damaged cache is ignored, not trusted
    return {}


# ===========================================================================
# Function 5: run the LLM with every prompt and save a YAML file
# ===========================================================================
def extract_kdes(document_text, document_name, output_dir="outputs",
                 llm=None, records=None):
    """
    Use each of the three prompts with Gemma-3-1B to identify KDEs, then save
    them as YAML in this shape:

        element1:
          name: container user
          requirements:
            - 4.1 Ensure that a user for the container has been created

    For every requirement, all three prompt styles name its element and the
    names VOTE: the most common name wins (few-shot breaks a three-way tie).
    Requirements with the same winning name are grouped into one element.

    The YAML file name includes the document name, e.g.
    outputs/docker-cis-v0-kdes.yaml

    llm:     the function that answers a prompt. Defaults to Gemma.
             Tests pass a fake one (and then the cache is not used).
    records: a list; every prompt and answer is appended to it so
             dump_llm_outputs() can write the log afterwards.

    Returns: the nested dictionary that was saved.
    """
    requirements = extract_requirements(document_text)
    if not requirements:
        raise ValueError(f"No CIS recommendations found in {document_name}.")

    use_real_model = llm is None
    cache = _load_cache() if use_real_model else {}

    groups = {}  # element name -> list of requirement IDs
    for req_id, title in requirements.items():
        votes = {}
        for prompt_type, build_prompt in PROMPT_BUILDERS.items():
            prompt = build_prompt(title)
            if prompt in cache:
                answer = cache[prompt]
            elif use_real_model:
                answer = gemma_generate(prompt, MAX_NEW_TOKENS[prompt_type])
                cache[prompt] = answer
            else:
                answer = llm(prompt)

            if records is not None:
                records.append({"llm_name": LLM_NAME, "prompt": prompt,
                                "prompt_type": prompt_type, "output": answer})
            votes[prompt_type] = _clean_element_name(answer)

        counts = Counter(name for name in votes.values() if name)
        if not counts:
            continue  # the model gave nothing usable for this requirement
        best, best_count = counts.most_common(1)[0]
        if best_count == 1 and votes["few-shot"]:
            best = votes["few-shot"]  # all three disagree: trust few-shot
        groups.setdefault(best, []).append(req_id)

    if use_real_model:
        CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        CACHE_PATH.write_text(json.dumps(cache, indent=1))

    # Build the required element1 / element2 / ... structure.
    kdes = {}
    for number, name in enumerate(sorted(groups), start=1):
        kdes[f"element{number}"] = {
            "name": name,
            "requirements": [f"{i} {requirements[i]}" for i in groups[name]],
        }

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    yaml_path = out_dir / f"{Path(document_name).stem}-kdes.yaml"
    with open(yaml_path, "w") as f:
        yaml.safe_dump(kdes, f, sort_keys=False, allow_unicode=True)

    return kdes


# ===========================================================================
# Function 6: log every LLM run to a text file
# ===========================================================================
def dump_llm_outputs(records, output_path):
    """
    Write every LLM run to a TEXT file in the required format:
        *LLM Name*, *Prompt Used*, *Prompt Type*, *LLM Output*
    Returns: the path of the file written.
    """
    if not records:
        raise ValueError("No LLM records to write.")

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        for record in records:
            f.write("*LLM Name*\n" + record["llm_name"] + "\n")
            f.write("*Prompt Used*\n" + record["prompt"] + "\n")
            f.write("*Prompt Type*\n" + record["prompt_type"] + "\n")
            f.write("*LLM Output*\n" + record["output"] + "\n")
            f.write("\n" + "=" * 60 + "\n\n")
    return output_path
