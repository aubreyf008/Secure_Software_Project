# Prompts

All prompts are sent to Gemma-3-1B (`google/gemma-3-1b-it`) once per CIS recommendation. The placeholder in angle brackets is replaced with that recommendation's title. The three answers vote on the final element name.

## zero-shot

```text
You are a security analyst reading the CIS Docker Benchmark. A key data element is the thing a security requirement protects or configures, such as a file, a directory, a user, a network setting, a daemon, an image, or a log. Name the key data element in the requirement below using 2 to 4 words.
Reply with only the element name.

Requirement: <one CIS recommendation, e.g. "Ensure that a user for the container has been created">
Element:
```

## few-shot

```text
You are a security analyst reading the CIS Docker Benchmark. A key data element is the thing a security requirement protects or configures, such as a file, a directory, a user, a network setting, a daemon, an image, or a log. Name the key data element in the requirement below using 2 to 4 words.
Reply with only the element name, like the examples.

Requirement: Ensure that the docker.service file ownership is set to root:root
Element: docker.service file

Requirement: Ensure that a user for the container has been created
Element: container user

Requirement: Ensure auditing is configured for the Docker daemon
Element: docker daemon

Requirement: Ensure that privileged ports are not mapped within containers
Element: container ports

Requirement: <one CIS recommendation, e.g. "Ensure that a user for the container has been created">
Element:
```

## chain-of-thought

```text
You are a security analyst reading the CIS Docker Benchmark. A key data element is the thing a security requirement protects or configures, such as a file, a directory, a user, a network setting, a daemon, an image, or a log. Name the key data element in the requirement below using 2 to 4 words.
Think step by step:
Step 1: What action does the requirement ask for?
Step 2: What file, setting, or component does that action apply to?
Step 3: Name that component in 2 to 4 words.
Write one or two short sentences of reasoning, then a final line that starts with 'Element:'.

Requirement: <one CIS recommendation, e.g. "Ensure that a user for the container has been created">
```
