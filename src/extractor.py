"""
Task 1: Extractor  (40% of the grade)

Goal: read two CIS Docker Benchmark PDFs, ask the Gemma-3-1B LLM to find the
"key data elements" (KDEs) in each one, and save the results.

You write all six functions below. Each one has a docstring that says what
the assignment requires. Replace each `raise NotImplementedError` with
your code.

Tips:
- Each PDF is about 290 pages (around 65k tokens). Gemma-3-1B can only read
  about 32k tokens at once, so you need to split the text into chunks.
- Keep the code that calls the model separate from the rest. Then your tests
  can swap in a fake model and run in seconds.
"""


# ---------------------------------------------------------------------------
# Function 1: input validation
# ---------------------------------------------------------------------------
def load_documents(path_1, path_2):
    """
    Take the two input PDF paths, validate them, and return their text.

    What "adequate input validation" could include (you decide):
      - the path exists and is a file
      - the file ends in .pdf AND really is a PDF (first bytes are b"%PDF")
      - the PDF has extractable text (not empty)

    Returns: a tuple (text_1, text_2)
    Raises:  a clear error (e.g. ValueError / FileNotFoundError) on bad input
    """
    raise NotImplementedError


# ---------------------------------------------------------------------------
# Functions 2-4: prompt builders (each returns a STRING)
# ---------------------------------------------------------------------------
def build_zero_shot_prompt(document_text):
    """
    Zero-shot: give the model instructions only, with NO examples.
    Returns: the prompt as a string.
    """
    raise NotImplementedError


def build_few_shot_prompt(document_text):
    """
    Few-shot: same instructions, plus a few worked examples of
    "requirement text -> KDE name + requirements" before the real text.
    Returns: the prompt as a string.
    """
    raise NotImplementedError


def build_chain_of_thought_prompt(document_text):
    """
    Chain-of-thought: ask the model to reason step by step
    (e.g. find each requirement, then decide which data element it is about,
    then group them) before giving the final answer.
    Returns: the prompt as a string.
    """
    raise NotImplementedError


# ---------------------------------------------------------------------------
# Function 5: run the LLM and save a YAML file per document
# ---------------------------------------------------------------------------
def extract_kdes(document_text, document_name, prompt_builder, output_dir="outputs"):
    """
    Use the prompt from `prompt_builder` with Gemma-3-1B to identify KDEs.
    One KDE can map to many requirements.

    Output shape (nested dictionary):
        element1:
          name: ...
          requirements:
            - req1
            - req2

    Save it as YAML. The file name must include the input document's name,
    e.g. "docker-cis-v0-kdes.yaml".

    Returns: the nested dictionary (and/or the YAML file path - your choice,
             just be consistent with your tests).
    """
    raise NotImplementedError


# ---------------------------------------------------------------------------
# Function 6: log every LLM run to a text file
# ---------------------------------------------------------------------------
def dump_llm_outputs(records, output_path):
    """
    Write every LLM run to a TEXT file in exactly this format:

        *LLM Name*
        ...
        *Prompt Used*
        ...
        *Prompt Type*
        ...
        *LLM Output*
        ...

    `records` is whatever you decide to collect during extract_kdes
    (for example a list of dicts with those four fields).
    """
    raise NotImplementedError
