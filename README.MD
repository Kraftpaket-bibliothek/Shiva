# Yukti (युक्ति)

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![NumPy](https://img.shields.io/badge/NumPy-Native-013243?style=flat-square&logo=numpy&logoColor=white)](https://numpy.org/)
[![spaCy](https://img.shields.io/badge/spaCy-NLP-09A3D5?style=flat-square&logo=spacy&logoColor=white)](https://spacy.io/)
[![Domain](https://img.shields.io/badge/Domain-Agnostic-ff9800?style=flat-square)](#3-for-engineers-technical-architecture--implementation)
[![Architecture](https://img.shields.io/badge/Architecture-Overview-blueviolet?style=flat-square)](#3-for-engineers-technical-architecture--implementation)
[![License](https://img.shields.io/badge/License-MIT-brightgreen?style=flat-square)](LICENSE)
[![Edge Ready](https://img.shields.io/badge/Edge%20Ready-Raspberry%20Pi-C51A4A?style=flat-square&logo=raspberrypi&logoColor=white)](https://www.raspberrypi.com/)

[Python](https://www.python.org/) • [NumPy](https://numpy.org/) • [spaCy](https://spacy.io/) • [Architecture](#3-for-engineers-technical-architecture--implementation) • [Project Structure](#4-project-directory-structure) • [License](LICENSE) • [Edge Ready](https://www.raspberrypi.com/)

---

Yukti is a lightweight, domain-agnostic, zero-hallucination neuro-symbolic decision engine designed for high-stakes decision adjudication across finance, aerospace, autonomous robotics, healthcare, and regulatory compliance. By replacing non-deterministic generative models with a structured **3-field input contract** (`Rules`, `Facts`, `Target`), a **spaCy + Regex** semantic extractor, and a custom **NumPy-native $\text{DPLL}(\mathcal{T})$ SMT solver**, Yukti converts natural language policies into provable, mathematically verifiable decisions.
To note, this is a proof of concept. The real core engine would be developed in a seperate repo.
---

## 1. For Business Leaders & Risk Executives

### The Problem: The Generative AI Liability Trap

Modern Generative Large Language Models (LLMs) are probabilistic token predictors. When deployed in mission-critical environments—such as credit underwriting, aviation safety checks, clinical triage, or regulatory compliance—they present severe operational vulnerabilities:

- **Hallucinations & Inconsistency**: The same input data can yield an "Approval" at 9:00 AM and a "Rejection" at 9:05 AM depending on model sampling temperature.
- **Regulatory & Safety Violations**: Frameworks such as the Equal Credit Opportunity Act (ECOA), Basel III/IV, GDPR Article 22, and DO-178C (airborne systems) mandate that automated decisions provide an exact, reproducible rationale. Probabilistic models cannot mathematically prove why a decision was rendered.
- **Cloud Dependency & Data Leakage**: Sending confidential records, telemetry, or PII to third-party cloud LLM APIs poses substantial data sovereignty and privacy risks.

### The Yukti Solution: Mathematical Adjudication

Yukti eliminates probabilistic guesswork from the decision loop. Users provide inputs through three clear fields (**Policy Rules**, **Case Facts**, and **Target**). Yukti uses natural language processing strictly to identify variables and thresholds, while delegating the actual reasoning to a deterministic automated theorem prover.

```text
Traditional LLMs                               Yukti Neuro-Symbolic Engine
+------------------------------------------+   +------------------------------------------+
| Unstructured Prompt (Rules + Facts Mixed)|   | Structured 3-Field Input (Rules / Facts) |
+--------------------┬---------------------+   +--------------------┬---------------------+
                     │                                              │
                     v                                              v
+------------------------------------------+   +------------------------------------------+
|   Generative Probabilistic Guessing      |   | Deterministic Formal Logic Solvers (SMT) |
+--------------------┬---------------------+   +--------------------┬---------------------+
                     │                                              │
                     v                                              v
+------------------------------------------+   +------------------------------------------+
| Outcome: Stochastic, non-reproducible    |   | Outcome: 100% Deterministic & Provable   |
| Audit Trail: Hallucinated / Unverifiable |   | Audit Trail: Exact Mathematical Proof    |
+------------------------------------------+   +------------------------------------------+
```

### Business Value & ROI

- **Universal Domain Agnosticism**: Works out of the box across Finance (underwriting, AML), Aerospace & Robotics (flight envelope verification, battery/thermal interlocks), and Healthcare (clinical protocol compliance) without retraining models.
- **Audit-Proof Explanations**: When a policy or safety check fails, Yukti extracts the exact mathematical conflict (the Unsatisfiable Core). Your team receives an itemized audit trail: *"Rejected because Debt-to-Income (44%) exceeds the maximum allowable threshold (43%)"* or *"Abort Landing: Battery Voltage (21.5V) is below required minimum (22.2V)"*.
- **Zero Data Footprint / Edge-Deployable**: Yukti relies strictly on NumPy and spaCy. It requires no GPUs, no external cloud API subscriptions, and runs securely on-premises or on an edge device (e.g., Raspberry Pi) in under 10ms.

---

## 2. For Students & Researchers

### Theoretical Overview

Yukti is a practical reference implementation of Neuro-Symbolic Computation, uniting linguistic dependency parsing with automated theorem proving (Formal Methods). Inspired by verification frameworks like RWTH Aachen's AProVE, Yukti decouples front-end natural language perception from a domain-agnostic mathematical back-end.

The core challenge in automated reasoning is bridging the Semantic Gap:

$$\text{Controlled Input DTO } (\mathcal{R}, \mathcal{F}, \mathcal{T}) \xrightarrow{\quad \text{Perception (spaCy + Regex)} \quad} \text{Structured JSON Payload} \xrightarrow{\quad \text{Dynamic Symbol Bridge} \quad} \text{First-Order Formulas } \Phi_{\mathcal{T}}$$

### Core Theoretical Concepts Explored in Yukti

#### 1. Decidable Fragments vs. Unrestricted First-Order Logic
Full First-Order Logic (FOL) with arbitrary quantification ($\forall, \exists$) is semi-decidable under Turing-Church undecidability. If a policy is not entailed, a classical theorem prover may run infinitely. Yukti sidesteps this by compiling policies strictly into Quantifier-Free Linear Real Arithmetic (`QF_LRA`) and Quantifier-Free Linear Integer Arithmetic (`QF_LIA`), ensuring termination with guaranteed polynomial or bounded exponential complexity.

#### 2. Dynamic Symbol Table & Dependency-Driven Extraction
Instead of relying on brittle templates (like forcing users to type *"must be"*) or hardcoded domain dictionaries, Yukti anchors on mathematical operators via Regex and traverses spaCy's syntactic dependency tree (`nsubj`, `amod`, `compound`, `advcl`) to extract noun-chunk subjects dynamically. Extracted noun phrases are lemmatized and normalized into a session-scoped Dynamic Symbol Table, allowing arbitrary domains to be modeled without pre-existing ontologies.

#### 3. The $\text{DPLL}(\mathcal{T})$ Architecture
Yukti implements an SMT solver from first principles using standard NumPy matrix operations:
- **Boolean Abstraction (The Skeleton)**: The policy's logical structure (conjunctions $\land$, disjunctions $\lor$, conditional implications $\implies$, and negations $\neg$) is abstracted into propositional clauses solved via a CDCL / DPLL SAT Engine.
- **Theory Solver ($\mathcal{T}$-Solver)**: When the SAT solver finds a candidate truth assignment for the boolean skeleton, the theory solver evaluates whether the arithmetic constraints are geometrically possible using a 2-phase Simplex algorithm on NumPy arrays.
- **Conflict-Driven Learning**: If the arithmetic is unsatisfiable (e.g., $x \ge 680 \land x \le 640$), the theory engine generates a conflict lemma. The SAT engine integrates this lemma as a learned clause and backtracks.

```text
+------------------------------------------------------------------------+
|                        DPLL(T) Solving Loop                            |
|                                                                        |
|   +---------------------+   Propositional Literals   +--------------+   |
|   |   dpllEngine (SAT)  | -------------------------> |  smtEngine   |   |
|   |   CDCL Proposition  | <------------------------- | Theory (LRA) │   |
|   +---------------------+      Conflict Lemmas       +--------------+   |
+------------------------------------------------------------------------+
```

#### 4. Mathematical Refutation & Unsat Cores
To prove that a set of case facts $\Delta$ satisfies a target rule or goal $G$, Yukti asserts the facts alongside the negation of the goal $\neg G$ (or tracks all policy assertions $R_i$ via boolean indicator variables):

$$\text{Check: } \text{SAT}(\Delta \land \neg G)$$

- If the solver returns **UNSAT**, it has mathematically refuted $\neg G$, proving that $G$ holds in all possible models.
- When policy constraints conflict with facts, the solver extracts the minimal **Unsatisfiable Core**, isolating the exact violated clauses.

---

## 3. For Engineers: Technical Architecture & Implementation

### Software Architecture

Yukti is decoupled into an interactive 3-field UI contract and two streamlined, high-performance tiers connected via deterministic Pydantic JSON payloads:

```text
[Interactive UI / CLI: 3 Structured Input Fields]
 1. Rules (Multiple Policy Constraints & Conditionals)
 2. Facts (Case Observations)
 3. Target (Goal Variable or "ALL_RULES")
                 │
                 v
+--------------------------------------------------------+
| 1. Perception Tier (src/textProcessor.py)              |
| • Model: In-memory spaCy loader & .config manager      |
| • DataInput DTO: Ingestion & 3-field validation        |
| • TextProcess: Recipe pipeline & JSON generator        |
+--------------------------┬-----------------------------+
                           │ Intermediate Structured JSON
                           │ (ParsedRuleDTO & ParsedFactDTO)
                           v
+--------------------------------------------------------+
| 2. Formal Reasoning Tier (src/logicEngine.py - NumPy)  |
| • LogicEngine: SMT Coordinator & Facade                |
| • dpllEngine: Vectorized CDCL SAT Solver               |
| • smtEngine: Simplex-based Linear Arithmetic Solver    |
+--------------------------┬-----------------------------+
                           │
                           v
[DecisionResult: Status + Unsat Core Audit Trail]
```

Detailed visual architectural diagrams (flow, component, sequence, and system architecture) are available in the [Architecture/](./Architecture) directory.

### Component Breakdown & Module Mapping

The consolidated modules in [`src/`](./src) directly implement the pipeline defined in the system architecture:

#### Perception Tier ([`src/textProcessor.py`](./src/textProcessor.py))
- **`Model`**: Instantiates and configures the underlying spaCy pipeline (`en_core_web_lg` by default), reading from `.config` for easy model swapping, and prunes non-semantic dependency branches.
- **Pydantic DTOs**:
  - `DataInput`: Encapsulates the 3-field input contract (`Rules`, `Facts`, `RequiredOutcome`).
  - `ParsedRuleDTO`: Encapsulates extracted symbols, normalized operators (`>=`, `<=`, `<`, `>`, `==`), thresholds, and optional conditional antecedents.
  - `ParsedFactDTO`: Encapsulates observed variables and values.
  - `ParsedOutputDTO`: Root container serializing the validated intermediate payload into formatted JSON via `.toJson()`.
- **`TextProcess`**: The pipeline harness class featuring a single `addStep` method to assemble pluggable parsing recipes (`parsePayload`, `extractRules`, `extractFacts`, `assembleDto`, `exportJson`) without execution branching or nested `if-else` statements.
- **`buildDefaultRecipe`**: Assembles the pre-configured end-to-end perception pipeline.

#### Formal Reasoning Tier ([`src/logicEngine.py`](./src/logicEngine.py))
Built with Python and pure NumPy without external C++ or third-party logic dependencies:
- **`dpllEngine`**: Maintains assignment vectors, watched literals, and clause databases using NumPy boolean masking (CDCL SAT Engine).
- **`smtEngine`**: Implements a tableau-based 2-phase Simplex algorithm using NumPy matrix pivots to solve systems of linear inequalities (Theory $\mathcal{T}$-Solver).
- **`LogicEngine`**: Top-level SMT facade that coordinates SAT solving with Theory lemmas, asserts tracking literals for every rule, and maps UNSAT cores directly back into human-readable rule violations.

#### Interactive Web Interface ([`src/chatInterface.py`](./src/chatInterface.py))
- Sleek FastAPI web dashboard styled with Open Sans. Prompts users for **1. Multiple Rules**, **2. Case Facts**, and **3. Target**, and automatically launches in the default browser on startup to render certified mathematical audit reports.

### Installation & Environment Setup

Yukti requires Python 3.10+, NumPy, spaCy, Pydantic, and FastAPI:

```bash
# Clone the repository and switch to the Yukti branch
git clone https://github.com/Kraftpaket-bibliothek/Shiva.git
cd Shiva
git checkout Yukti

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install the minimal dependencies
pip install numpy spacy pydantic fastapi uvicorn

# Download the English pipeline (default: en_core_web_lg, configurable in .config)
python -m spacy download en_core_web_lg
```

### Quickstart Example (Domain-Agnostic 3-Field DTO Workflow)

```python
from src.textProcessor import DataInput, TextProcess, buildDefaultRecipe
from src.logicEngine import LogicEngine

# 1. Initialize pipeline components (loads model configured in .config, default: en_core_web_lg)
processor = buildDefaultRecipe()
engine = LogicEngine()

# 2. Provide inputs via the 3 structured fields (Finance, Aerospace, or any domain)
input_data = DataInput(
    Rules=[
        "Credit score needs to be at least 680.",
        "Debt to income ratio should stay under 43%.",
        "Tax return years must be at least 2 when self employed is true."
    ],
    Facts=[
        "Credit score: 640",
        "Debt to income ratio: 36%",
        "Self employed: true",
        "Tax return years: 1"
    ],
    RequiredOutcome=["ALL_RULES"]
)

# 3. Perception: Execute recipe pipeline and extract validated JSON payload
parsed_json = processor.executePipeline(input_data)

# 4. Reasoning: Evaluate compliance via NumPy-based SMT
result = engine.solve_policy(parsed_json)

# 5. Inspect Verdict & Formal Audit Trail
print(f"Decision Status: {result.status}")
if result.status == "REJECTED":
    print("Adverse Action / Violation Audit Trail:")
    for violation in result.adverse_actions:
        print(f" - [VIOLATION] {violation.rule_id}: {violation.symbol}")
        print(
            f"   Actual: {violation.actual_value} | Required:"
            f" {violation.operator} {violation.threshold}"
        )
```

**Console Output:**

```text
Decision Status: REJECTED
Adverse Action / Violation Audit Trail:
 - [VIOLATION] Rule_1: credit_score
   Actual: 640.0 | Required: >= 680.0
 - [VIOLATION] Rule_3: tax_return_years (Triggered by: self_employed == True)
   Actual: 1.0 | Required: >= 2.0
```

---

## 4. Project Directory Structure

### Repository Layout

- 📁 [**`Architecture/`**](./Architecture) — *Code-driven architecture specifications & diagrams*
  - 📋 [`SystemOverview.md`](./Architecture/SystemOverview.md) — High-level end-to-end processing & reasoning flow
  - 🧩 [`ComponentDiagram.md`](./Architecture/ComponentDiagram.md) — Modular classes, DTOs & component boundaries
  - 🔄 [`FlowDiagram.md`](./Architecture/FlowDiagram.md) — Execution step lifecycle from ingestion to SMT verdict
  - ⏱️ [`SequenceDiagram.md`](./Architecture/SequenceDiagram.md) — Chronological runtime interactions between components
  - 🐍 [`architectureSync.py`](./Architecture/architectureSync.py) — Architecture diagram generator & AST parity validator
  - 📄 [`README.MD`](./Architecture/README.MD) — Architecture index & usage guide
- 📁 [**`src/`**](./src) — *Consolidated implementation source code*
  - 🐍 [**`textProcessor.py`**](./src/textProcessor.py) — *Perception Tier: Model loading, Pydantic DTOs & Recipe pipeline*
  - 🐍 [**`logicEngine.py`**](./src/logicEngine.py) — *Formal Reasoning Tier: Pure NumPy CDCL SAT and Simplex SMT solver*
  - 🐍 [**`chatInterface.py`**](./src/chatInterface.py) — *Interactive 3-field chat & CLI frontend*
- 📄 [**`RULES.MD`**](./RULES.MD) — *Architectural, memory-efficiency & clean code rules*
- 📄 [**`README.MD`**](./README.MD) — *Documentation*

### ASCII Tree View

```text
Shiva/ (branch: Yukti)
├── Architecture/                     # Architecture specifications & diagrams
│   ├── SystemOverview.md             # High-level end-to-end system flow
│   ├── ComponentDiagram.md           # Modular classes, DTOs & boundaries
│   ├── FlowDiagram.md                # Ingestion-to-SMT execution lifecycle
│   ├── SequenceDiagram.md            # Chronological runtime interactions
│   ├── architectureSync.py           # Architecture generator & parity sync
│   └── README.MD                     # Architecture directory guide
├── src/                              # Consolidated implementation source code
│   ├── textProcessor.py              # Perception Tier: Model, Pydantic DTOs & Recipe pipeline
│   ├── logicEngine.py                # Formal Reasoning Tier: Pure NumPy SMT/SAT solver
│   └── chatInterface.py              # Interactive 3-field chat & CLI frontend
├── RULES.MD                          # Architectural & coding rules
└── README.MD                         # Documentation
```
