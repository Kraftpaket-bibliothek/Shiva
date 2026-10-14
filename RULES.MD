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
  - `Model` (the model instantiator)
  - `TextStream` (the ingestion handler)
  - `TextProcess` (the clause and token parser)
  - `TextToMathBridge` (the intermediary symbol & AST translation engine)
  - `LogicEngine`, `DPL`, `SMT` (the formal reasoning solvers)
  - `chatInterface` (the interactive CLI/frontend)
- **Eliminate Wrapper / Fluff Classes**: Avoid creating redundant classes or manager wrappers (e.g., never create `SpacyModelManager`, `ConfigManager`, or `YuktiModelConfig` dataclasses when a plain function or dictionary suffices).
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

---

## 4. Configuration Over Hardcoding (`.config`)

- **Zero Hardcoded Constants**: Never hardcode model names, pipeline component lists, dependency label sets, aliases, or thresholds inside Python code.
- **Single Source of Truth**: All operational variables and tuning knobs must live in `.config` (`Model_Name`, `Model_Aliases`, `Disabled_Pipes`, `Relevant_Dep_Labels`, `Unused_Dep_Labels`, etc.).
- **Frictionless Model Swapping**: Swapping an underlying model (e.g., from `en_core_web_lg` to `en_core_web_trf` or `en_core_web_sm`) must only require editing `Model_Name` in `.config` without modifying any Python files.

---

## 5. File Layout: Top-to-Bottom Readability

Files must be arranged in chronological, logical order so that reading the file from top to bottom explains its entire lifecycle:
1. **Module Docstring**: Clear explanation of role, tier, and responsibilities.
2. **Global / In-Memory Cache**: Module-level caches (e.g., `cachedPipelines`) to avoid redundant reloads.
3. **Configuration & Data Ingestion**: Functions that locate, read, and parse settings (`readConfig`).
4. **Environment / Pre-requisite Helpers**: Dependency installers or setup functions (`downloadModel`).
5. **Core Class & Operations**: The primary class containing operational methods in execution order (`loadModel` $\to$ `pruneDependencies` $\to$ `warmup`).
6. **Top-Level Functional Handles**: Clean functional aliases exported for direct import.

---

## 6. Architecture & Inter-Tier Contracts

- **3-Field Input Contract**: Standardize user and UI inputs into three distinct fields:
  1. `Rules` (policy constraints and conditionals)
  2. `Facts` (case observations)
  3. `Target` (goal variable or `"ALL_RULES"`)
- **JSON Intermediate Payloads**: The Perception tier (`TextProcess`) must serialize parsed spans and tokens into a clean, decoupled JSON payload before passing it to the Translation tier (`TextToMathBridge`).
- **Dynamic Symbol Table**: Never hardcode domain lexicons. Ground symbols dynamically by traversing spaCy dependency arcs (`nsubj`, `amod`, `compound`, `advcl`) around operators to support Finance, Aerospace, Robotics, and Healthcare out of the box.
- **Mathematical Adjudication**: All reasoning must be purely deterministic, using automated theorem proving via pure NumPy linear arithmetic (`SMT`) and CDCL SAT (`DPL`). No probabilistic generative guessing in the decision loop.

---

## 7. Workflow & Learning Protocol

- **Continuous Rule Logging**: Whenever the user provides feedback, refactors an approach, or establishes new conventions, immediately update this document (`RULES.MD`) with detailed explanations.
- **Prioritize Speed & Brevity**: Do not verify or write excessive boilerplate tests unless explicitly instructed. Keep solutions minimal, performant, and directly aligned with the architecture diagram.
