# Shiva / Yukti: Engineering & Architectural Rules

This document records the foundational coding style, architectural philosophies, memory-efficiency principles, and design conventions established for the Shiva / Yukti repository. Every component and contribution must adhere to these rules.

---

## 1. Method & Function Naming Rules

- **Active Verb Requirement**: Every method and function name must be an active verb (or verb phrase) that states exactly what the function accomplishes (e.g., `readConfig`, `downloadModel`, `loadModel`, `pruneDependencies`, `warmup`).
- **No Underscores (camelCase)**: Method and function names must **never** contain underscores. Use strict camelCase (e.g., `readConfig`, not `read_config` or `_read_config`).
- **No Vague or Generic Verbs**: Avoid ambiguous names like `process`, `handle`, `run`, or `manage`. Prefer precise actions like `parseAndSegment`, `buildIr`, `solvePolicy`.

---

## 2. Class Naming & Object Design

- **Self-Descriptive Names**: Class names must state exactly what the entity is, mirroring the components defined in the architecture diagrams (`Architecture/Architecture.drawio`):
  - `Model` (the model instantiator within `textProcessor.py`)
  - `TextProcess` (the pipeline harness within `textProcessor.py`)
  - `DataInput`, `ParsedRuleDTO`, `ParsedFactDTO`, `ParsedOutputDTO` (Pydantic DTOs within `textProcessor.py`)
  - `LogicEngine`, `DPL`, `SMT` (the formal reasoning solvers)
  - `chatInterface` (the interactive CLI/frontend)
- **Eliminate Wrapper / Fluff Classes**: Avoid creating redundant classes or manager wrappers (e.g., never create `SpacyModelManager`, `ConfigManager`, or `YuktiModelConfig` dataclasses when a plain function or dictionary suffices).
- **Consolidated Perception Module (`textProcessor.py`)**: Tier 1 Perception encapsulates `Model`, Pydantic DTOs, and `TextProcess` inside a single unified `textProcessor.py` file, cleanly partitioned by section comment ribbons.
- **Match Architecture Diagram Nodes**: Every class and file must have a 1:1 direct correspondence with an entity in the architecture diagram.
- **Single Exposed Entry Point Pattern**: Classes that manage complex multi-step lifecycles (like `Model`) must encapsulate their individual operations (`_loadModel`, `_warmup`, `_pruneDependencies`) as **internal methods**. The class must expose **exactly one public coordinator method** (e.g., `loadModelToMemory`) that orchestrates all internal steps and returns the ready-to-use artifact. The module should only export this single entry point.

---

## 3. Memory & Performance: Edge-First Philosophy

- **Functions Over Classes for Pure Utilities**: In Python, defining and instantiating classes incurs memory and allocation overhead. If a task is a pure transformation or data-fetching task (like reading a config file), implement it as a standalone function rather than a class.
- **Lightweight Primitives**: Prefer standard Python primitives (`dict`, `set`, `list`, `str`) for intermediate representations and config payloads rather than heavyweight object hierarchies.
- **Aggressive Pipeline Pruning**: 
  - When loading NLP pipelines (e.g., spaCy `en_core_web_lg`), explicitly disable unnecessary components (`ner`, `textcat`) to minimize memory footprint and execution latency.
  - Prune non-semantic dependency branches (`det`, `punct`, `aux`, `auxpass`, `expl`, `intj`, `meta`) so downstream engines receive only semantically meaningful tokens.
- **Edge Deployment Target**: Every module must be optimized for sub-10ms execution on CPU/edge devices (such as a Raspberry Pi) without GPU or cloud API dependencies.
- **Declarative Design over If-Else Branching**: Avoid writing procedural cascading `if-elif-else` chains and nested conditional trees. Replace branching logic with declarative, data-driven patterns:
  - **Dictionary Dispatch Tables**: Map types or keys to handler lambdas/functions (e.g., `PAYLOAD_PARSERS = {DataInput: ..., dict: ..., str: ...}`).
  - **Lookup Tables**: Replace boolean and operator if-checks with static lookup dictionaries (`BOOLEAN_LOOKUP`, `OPERATOR_LOOKUP`).
  - **Regex Named Groups**: Extract multiple fields (`symbol`, `op`, `val`) simultaneously via compiled patterns and `.groupdict()` rather than multiple conditional regex passes.
  - **Flat Linear Pipelines**: Keep processing stages flat and linear without deeply indented decision trees.

---

## 4. Configuration Over Hardcoding (`.config`)

- **Zero Hardcoded Constants**: Never hardcode model names, pipeline component lists, dependency label sets, aliases, or thresholds inside Python code.
- **Single Source of Truth**: All operational variables and tuning knobs must live in `.config` (`Model_Name`, `Model_Aliases`, `Disabled_Pipes`, `Relevant_Dep_Labels`, `Unused_Dep_Labels`, etc.).
- **Frictionless Model Swapping**: Swapping an underlying model (e.g., from `en_core_web_lg` to `en_core_web_trf` or `en_core_web_sm`) must only require editing `Model_Name` in `.config` without modifying any Python files.

---

## 5. File Layout, Function Brevity & Comment Ribbons

- **Function Brevity**: Keep individual functions short (typically 4–8 lines). Every function must do exactly one thing.
- **No Inner or Top Comments**: Avoid comments inside functions and avoid long paragraph/docstring commentary at the top of files. The code must be clean, declarative, and self-explanatory.
- **Section Comment Ribbons**: Cleanly separate distinct functional layers and modules using standard comment ribbons (e.g., `# ======================================================================`) so readers can immediately understand boundaries.
- **Top-to-Bottom Readability**: Arrange files in chronological, logical order so reading top-to-bottom explains the entire execution lifecycle.

---

## 6. Architecture & Inter-Tier Contracts

- **3-Field Input Contract**: Standardize user and UI inputs into three distinct fields:
  1. `Rules` (policy constraints and conditionals)
  2. `Facts` (case observations)
  3. `Target` (goal variable or `"ALL_RULES"`)
- **Unified DTOs & Perception (`textProcessor.py`)**: All Pydantic DTO definitions (`DataInput`, `ParsedRuleDTO`, `ParsedFactDTO`, `ParsedOutputDTO`) and perception components (`Model`, `TextProcess`) live in `textProcessor.py`.
- **The Recipe / Pipeline Pattern for Processors**: Processor classes (`TextProcess`) must only act as lightweight stage runners. The actual processing logic must be written as separate, standalone functions (`parsePayload`, `extractRules`, `extractFacts`, `assembleDto`, `exportJson`). The processor class provides extensibility hooks (`addStep`, `executePipeline`) so callers can assemble custom processing recipes. A single `addStep` method handles either a single step function or a list of steps.
- **JSON Intermediate Payloads**: The Perception tier (`textProcessor.py`) must serialize parsed spans and tokens into a clean, decoupled JSON payload constructed strictly via Pydantic DTOs before passing it to downstream engines.
- **Dynamic Symbol Table**: Never hardcode domain lexicons. Ground symbols dynamically by traversing spaCy dependency arcs (`nsubj`, `amod`, `compound`, `advcl`) around operators to support Finance, Aerospace, Robotics, and Healthcare out of the box.
- **Mathematical Adjudication**: All reasoning must be purely deterministic, using automated theorem proving via pure NumPy linear arithmetic (`SMT`) and CDCL SAT (`DPL`). No probabilistic generative guessing in the decision loop.

---

## 7. Workflow & Learning Protocol

- **Continuous Rule Logging**: Whenever the user provides feedback, refactors an approach, or establishes new conventions, immediately update this document (`RULES.MD`) with detailed explanations.
- **Prioritize Speed & Brevity**: Do not verify or write excessive boilerplate tests unless explicitly instructed. Keep solutions minimal, performant, and directly aligned with the architecture diagram.
