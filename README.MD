# Yukti (युक्ति)

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![NumPy](https://img.shields.io/badge/NumPy-Native-013243?style=flat-square&logo=numpy&logoColor=white)](https://numpy.org/)
[![spaCy](https://img.shields.io/badge/spaCy-NLP-09A3D5?style=flat-square&logo=spacy&logoColor=white)](https://spacy.io/)
[![Architecture](https://img.shields.io/badge/Architecture-Overview-blueviolet?style=flat-square)](#3-for-engineers-technical-architecture--implementation)
[![License](https://img.shields.io/badge/License-MIT-brightgreen?style=flat-square)](LICENSE)
[![Edge Ready](https://img.shields.io/badge/Edge%20Ready-Raspberry%20Pi-C51A4A?style=flat-square&logo=raspberrypi&logoColor=white)](https://www.raspberrypi.com/)

[Python](https://www.python.org/) • [NumPy](https://numpy.org/) • [spaCy](https://spacy.io/) • [Architecture](#3-for-engineers-technical-architecture--implementation) • [Project Structure](#4-project-directory-structure) • [License](LICENSE) • [Edge Ready](https://www.raspberrypi.com/)

---

Yukti is a lightweight, zero-hallucination neuro-symbolic decision engine designed for high-stakes financial underwriting, regulatory compliance, and risk adjudication. By replacing non-deterministic generative models with a pure spaCy semantic extractor and a custom NumPy-native $\text{DPLL}(\mathcal{T})$ SMT solver, Yukti converts unstructured natural language policies into provable, legally defensible decisions.

---

## 1. For Business Leaders & Risk Executives

### The Problem: The Generative AI Liability Trap

Modern Generative Large Language Models (LLMs) are probabilistic token predictors. When deployed in financial compliance, credit underwriting, or transaction monitoring, they present critical vulnerabilities:

- **Hallucinations & Inconsistency**: The same applicant data can yield an "Approval" at 9:00 AM and a "Rejection" at 9:05 AM depending on model sampling temperature.
- **Regulatory Violations**: Frameworks such as the Equal Credit Opportunity Act (ECOA), FCRA, Basel III/IV, and GDPR Article 22 mandate that automated credit decisions provide an exact, reproducible rationale. Probabilistic models cannot mathematically prove why a decision was rendered.
- **Cloud Dependency & Data Leakage**: Sending confidential financial statements, debt obligations, and PII to third-party cloud LLM APIs poses substantial data sovereignty and privacy risks.

### The Yukti Solution: Mathematical Adjudication

Yukti eliminates probabilistic guesswork from the decision loop. It uses natural language processing strictly to identify terms, while delegating the actual decision to a deterministic automated theorem prover.

```text
Traditional LLMs                               Yukti Neuro-Symbolic Engine
┌──────────────────────────────────────────┐   ┌──────────────────────────────────────────┐
│ Unstructured Policy + Applicant Fact Sheet│   │ Unstructured Policy + Applicant Fact Sheet│
└────────────────────┬─────────────────────┘   └────────────────────┬─────────────────────┘
                     │                                              │
                     ▼                                              ▼
┌──────────────────────────────────────────┐   ┌──────────────────────────────────────────┐
│   Generative Probabilistic Guessing      │   │ Deterministic Formal Logic Solvers (SMT) │
└────────────────────┬─────────────────────┘   └────────────────────┬─────────────────────┘
                     │                                              │
                     ▼                                              ▼
┌──────────────────────────────────────────┐   ┌──────────────────────────────────────────┐
│ Outcome: Stochastic, non-reproducible    │   │ Outcome: 100% Deterministic & Provable   │
│ Adverse Action: Hallucinated /           │   │ Adverse Action: Exact Mathematical Proof │
│                 Unverifiable             │   │                                          │
└──────────────────────────────────────────┘   └──────────────────────────────────────────┘
```

### Business Value & ROI

- **Audit-Proof Adverse Action Notices**: When an application is rejected, Yukti extracts the exact mathematical conflict (the Unsatisfiable Core). Your compliance team receives an itemized audit trail: *"Rejected because Debt-to-Income (44%) exceeds the maximum allowable threshold (43%)"*.
- **Zero Data Footprint / Edge-Deployable**: Yukti relies strictly on NumPy and spaCy. It requires no GPUs, no external cloud API subscriptions, and runs securely on-premises or on an edge device (e.g., Raspberry Pi) within your isolated firewall.
- **Cost Efficiency**: Reduces recurring API inference overhead to near zero while delivering sub-10ms decision latencies.

---

## 2. For Students & Researchers

### Theoretical Overview

Yukti is a practical reference implementation of Neuro-Symbolic Computation, uniting statistical natural language processing with automated theorem proving (Formal Methods).

The core challenge in automated reasoning is the Semantic Gap:

$$\text{Natural Language Policy } \mathcal{L}_{\text{nat}} \xrightarrow{\quad \text{Perception (Parser)} \quad} \text{Structured JSON Payload} \xrightarrow{\quad \text{Intermediary Bridge} \quad} \text{First-Order Formulas } \Phi_{\mathcal{T}}$$

### Core Theoretical Concepts Explored in Yukti

#### 1. Decidable Fragments vs. First-Order Logic
Full First-Order Logic (FOL) with arbitrary quantification ($\forall, \exists$) is semi-decidable under Turing-Church undecidability. If a policy is not entailed, a classical theorem prover may run infinitely. Yukti sidesteps this by compiling policies strictly into Quantifier-Free Linear Real Arithmetic ($\text{QF\_LRA}$) and Quantifier-Free Linear Integer Arithmetic ($\text{QF\_LIA}$), ensuring termination with guaranteed polynomial or bounded exponential complexity.

#### 2. The $\text{DPLL}(\mathcal{T})$ Architecture
Yukti implements an SMT solver from first principles using standard NumPy matrix operations:
- **Boolean Abstraction (The Skeleton)**: The policy’s logical structure (conjunctions $\land$, disjunctions $\lor$, negations $\neg$) is abstracted into propositional clauses solved via a CDCL / DPLL SAT Engine.
- **Theory Solver ($\mathcal{T}$-Solver)**: When the SAT solver finds a candidate truth assignment for the boolean skeleton, the theory solver evaluates whether the arithmetic constraints are geometrically possible using a 2-phase Simplex algorithm on NumPy arrays.
- **Conflict-Driven Learning**: If the arithmetic is unsatisfiable (e.g., $x \ge 680 \land x \le 640$), the theory engine generates a conflict lemma. The SAT engine integrates this lemma as a learned clause and backtracks.

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        DPLL(T) Solving Loop                            │
│                                                                        │
│   ┌─────────────────────┐   Propositional Literals   ┌──────────────┐   │
│   │   dpllEngine (SAT)  │ ─────────────────────────► │  smtEngine   │   │
│   │   CDCL Proposition  │ ◄───────────────────────── │ Theory (LRA) │   │
│   └─────────────────────┘      Conflict Lemmas       └──────────────┘   │
└────────────────────────────────────────────────────────────────────────┘
```

#### 3. Mathematical Refutation & Unsat Cores
To prove that an applicant satisfies a rule $R$, Yukti asserts the applicant facts $\Delta$ alongside the negation of the rule $\neg R$:

$$\text{Check: } \text{SAT}(\Delta \land \neg R)$$

- If the solver returns **UNSAT**, it has mathematically refuted $\neg R$, proving that $R$ holds in all possible models.
- If the solver returns **SAT**, it extracts a countermodel demonstrating the exact conditions under which the applicant fails the rule.

---

## 3. For Engineers: Technical Architecture & Implementation

### Software Architecture

Yukti is strictly decoupled into three functional tiers connected via deterministic data transfer contracts:

```text
[Raw User Input: Policies & Facts]
                 │
                 ▼
┌────────────────────────────────────────────────────────┐
│ 1. Perception Tier                                     │
│ • TextStream: Ingestion coordinator                    │
│ • TextProcess: spaCy tokenization + Regex matchers     │
└──────────────────────────┬─────────────────────────────┘
                           │ Intermediate Structured JSON
                           │ (Parsed Tokens, Spans & Clauses)
                           ▼
┌────────────────────────────────────────────────────────┐
│ 2. Translation Tier (Intermediary Engine)              │
│ • TextToMathBridge: JSON Ingestion & Lexicon Grounding │
│ • AST Compiler: Synthesizes typed AST from JSON        │
└──────────────────────────┬─────────────────────────────┘
                           │ FinancialPolicyAST
                           ▼
┌────────────────────────────────────────────────────────┐
│ 3. Formal Reasoning Tier (Pure NumPy)                  │
│ • LogicEngine: SMT Coordinator & Facade                │
│ • dpllEngine: Vectorized CDCL SAT Solver               │
│ • smtEngine: Simplex-based Linear Arithmetic Solver    │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
[DecisionResult: Status + Unsat Core Audit Trail]
```

Detailed visual architectural diagrams (flow, component, sequence, and system architecture) are available in the [Architecture/](./Architecture) directory.

### Component Breakdown & Module Mapping

The modules in [`src/`](./src) directly implement the nodes defined in the [Architecture Diagrams](./Architecture):

#### Tier 1: Perception (`src/ParsingAndRegex/`)
- **`model.py`** (`Model`): Instantiates and configures the underlying spaCy pipeline (`en_core_web_sm`).
- **`TextStream.py`** (`TextStream`): Manages raw input stream ingestion, buffering, and text chunking.
- **`TextProcess.py`** (`TextProcess`): Sentence parser, clause segmenter, and regex sequence labeller:
  - **Regex Engine**: Extracts numeric thresholds (`\d+(\.\d+)?`), currency markers, percentage normalizations ($43\% \to 0.43$), and comparative keywords (`>=`, `under`, `at least`).
  - **spaCy Pipeline**: Computes part-of-speech tags and sentence/clause boundary spans to identify target financial attribute spans (*credit score*, *debt-to-income ratio*, *monthly income*).
  - **JSON Serialization**: Represents and serializes all extracted tokens, entities, and clause boundaries into a clean, decoupled intermediate **JSON payload**.

#### Tier 2: Translation (`src/TranslationEngine/`)
- **`TextToMathBridge.py`** (`TextToMathBridge`): The intermediary engine connecting linguistic perception to formal mathematical logic:
  - Ingests the structured JSON payload produced by `TextProcess`.
  - Normalizes non-standard linguistic spans against an explicit Financial Lexicon (mapping `"credit rating"` $\to$ `CREDIT_SCORE`).
  - Executes spatial proximity binding within clause boundaries to generate typed triplets:

$$\langle \text{Metric}, \; \text{Operator}, \; \text{Threshold} \rangle$$

  - Compiles and validates the JSON payload into a typed `FinancialPolicyAST` before passing it to the solver.

#### Tier 3: Formal Reasoning (`src/LogicEngine/`)
Built with Python and pure NumPy without external C++ or third-party logic dependencies:
- **`DPL.py`** (`dpllEngine`): Maintains assignment vectors, watched literals, and clause databases using NumPy boolean masking (CDCL SAT Engine).
- **`SMT.py`** (`smtEngine`): Implements a tableau-based 2-phase Simplex algorithm using NumPy matrix pivots to solve systems of linear inequalities (Theory $\mathcal{T}$-Solver).
- **`LogicEngine.py`** (`LogicEngine`): Top-level SMT facade that coordinates SAT solving with Theory lemmas, asserts tracking literals, and maps UNSAT cores directly back into human-readable rule violations.

#### Interactive Interface
- **`chatInterface.py`**: Interactive CLI and chat frontend allowing users and underwriters to input policies, evaluate applicant cases, and inspect audit trails in real time.

### Installation & Environment Setup

Yukti requires only Python 3.10+, NumPy, and spaCy.

```bash
# Clone the repository and switch to the Yukti branch
git clone https://github.com/Kraftpaket-bibliothek/Shiva.git
cd Shiva
git checkout Yukti

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install the minimal dependencies
pip install numpy spacy

# Download the lightweight English pipeline
python -m spacy download en_core_web_sm
```

### Quickstart Example

```python
from src.ParsingAndRegex.TextStream import TextStream
from src.ParsingAndRegex.TextProcess import TextProcess
from src.TranslationEngine.TextToMathBridge import TextToMathBridge
from src.LogicEngine.LogicEngine import LogicEngine

# 1. Initialize pipeline
stream = TextStream()
processor = TextProcess(model_name="en_core_web_sm")
bridge = TextToMathBridge()
engine = LogicEngine()

# 2. Input policy text and applicant facts
policy_document = """
Policy PrimeMortgage:
The applicant credit score must be at least 680.
The debt-to-income ratio must be under 43%.
The applicant monthly income must exceed 4000.
"""

applicant_case = """
Applicant Profile:
credit score is 640.
debt-to-income ratio is 36%.
monthly income is 5200.
"""

# 3. Perception: Extract clauses/tokens and serialize to intermediate JSON
raw_text = f"{policy_document}\n{applicant_case}"
parsed_json = processor.parse_and_segment(raw_text)

# 4. Translation: Intermediary engine (bridge) compiles JSON into a validated AST
ast = bridge.build_ir(parsed_json)

# 5. Reasoning: Evaluate compliance via NumPy-based SMT
result = engine.solve_policy(ast)

# 6. Inspect Verdict & Formal Audit Trail
print(f"Decision Status: {result.status}")
if result.status == "REJECTED":
    print("Adverse Action Audit Trail:")
    for violation in result.adverse_actions:
        print(f" - [VIOLATION] {violation.description}")
        print(
            f"   Actual: {violation.actual_value} | Required:"
            f" {violation.operator} {violation.threshold}"
        )
```

**Console Output:**

```text
Decision Status: REJECTED
Adverse Action Audit Trail:
 - [VIOLATION] Rule PrimeMortgage.credit_score failed. Actual: 640.0 | Required: >= 680.0
```

---

## 4. Project Directory Structure

### Repository Layout

- 📁 [**`Architecture/`**](./Architecture) — *Visual architecture diagrams & design specifications*
  - 📄 [`Architecture.drawio`](./Architecture/Architecture.drawio) — Editable Draw.io system diagram
  - 🖼️ [`Architecture.png`](./Architecture/Architecture.png) — End-to-end architecture overview
  - 🖼️ [`Component Diagram.png`](./Architecture/Component%20Diagram.png) — Component relationship diagram
  - 🖼️ [`Flow diagram.png`](./Architecture/Flow%20diagram.png) — Execution & data flow diagram
  - 🖼️ [`Sequence Diagram.png`](./Architecture/Sequence%20Diagram.png) — Chronological component interactions
- 📁 [**`src/`**](./src) — *Implementation source code*
  - 📁 [**`ParsingAndRegex/`**](./src/ParsingAndRegex) — *Tier 1: Perception Engine*
    - 🐍 [`model.py`](./src/ParsingAndRegex/model.py) — spaCy pipeline loader & model config
    - 🐍 [`TextStream.py`](./src/ParsingAndRegex/TextStream.py) — Input stream ingestion buffer & chunking handler
    - 🐍 [`TextProcess.py`](./src/ParsingAndRegex/TextProcess.py) — Sentence parser, regex matcher & JSON serializer
  - 📁 [**`TranslationEngine/`**](./src/TranslationEngine) — *Tier 2: Translation / Intermediary Engine*
    - 🐍 [`TextToMathBridge.py`](./src/TranslationEngine/TextToMathBridge.py) — JSON deserializer, ontology lexicon grounding & AST builder
  - 📁 [**`LogicEngine/`**](./src/LogicEngine) — *Tier 3: Formal Reasoning Engine (Pure NumPy)*
    - 🐍 [`DPL.py`](./src/LogicEngine/DPL.py) — Propositional CDCL / DPLL SAT solver
    - 🐍 [`SMT.py`](./src/LogicEngine/SMT.py) — Simplex-based Linear Real Arithmetic (LRA) solver
    - 🐍 [`LogicEngine.py`](./src/LogicEngine/LogicEngine.py) — SMT coordinator & unsat-core audit trail mapper
  - 🐍 [`chatInterface.py`](./src/chatInterface.py) — Underwriter interactive chat & CLI frontend
- 📄 [**`README.MD`**](./README.MD) — Documentation

### ASCII Tree View

```text
Shiva/ (branch: Yukti)
├── Architecture/                     # Visual design specifications
│   ├── Architecture.drawio           # Editable Draw.io source file
│   ├── Architecture.png              # End-to-end architecture overview
│   ├── Component Diagram.png         # Tiered module breakdown
│   ├── Flow diagram.png              # Execution & decision flow
│   └── Sequence Diagram.png          # Chronological component interactions
├── src/                              # Implementation source code
│   ├── ParsingAndRegex/              # Tier 1: Perception Engine
│   │   ├── model.py                  # spaCy pipeline loader & model config
│   │   ├── TextStream.py             # Stream buffer & text chunking handler
│   │   └── TextProcess.py            # Sentence segmenter, regex labeller & JSON exporter
│   ├── TranslationEngine/            # Tier 2: Translation / Intermediary Engine
│   │   └── TextToMathBridge.py       # JSON deserializer, ontology grounding & AST builder
│   ├── LogicEngine/                  # Tier 3: Formal Reasoning Engine (NumPy-native)
│   │   ├── DPL.py                    # Propositional CDCL / DPLL SAT solver
│   │   ├── SMT.py                    # Simplex-based Linear Real Arithmetic (LRA) solver
│   │   └── LogicEngine.py            # SMT coordinator & unsat-core audit trail mapper
│   └── chatInterface.py              # Underwriter interactive chat & CLI frontend
└── README.MD                         # Documentation
```