from pathlib import Path
from typing import Dict, Callable

# ======================================================================
# PATH AND CONFIGURATION CONSTANTS
# ======================================================================

BASE_DIR = Path(__file__).resolve().parent
SYSTEM_OVERVIEW_PATH = BASE_DIR / "SystemOverview.md"
COMPONENT_DIAGRAM_PATH = BASE_DIR / "ComponentDiagram.md"
FLOW_DIAGRAM_PATH = BASE_DIR / "FlowDiagram.md"
SEQUENCE_DIAGRAM_PATH = BASE_DIR / "SequenceDiagram.md"
README_PATH = BASE_DIR / "README.MD"

# ======================================================================
# DIAGRAM CONTENT BUILDERS
# ======================================================================

def buildSystemOverviewContent() -> str:
    return """# System Overview Architecture

This document describes the high-level end-to-end data processing and reasoning flow of the Shiva / Yukti decision engine.

```mermaid
graph TD
    classDef inputStyle fill:#e1f5fe,stroke:#0288d1,stroke-width:2px,color:#01579b;
    classDef perceptionStyle fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px,color:#4a148c;
    classDef dtoArray fill:#fff3e0,stroke:#e65100,stroke-width:2px,color:#bf360c;
    classDef reasoningStyle fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px,color:#1b5e20;
    classDef outputStyle fill:#ede7f6,stroke:#512da8,stroke-width:2px,color:#311b92;

    subgraph UserTier["1. Ingestion Interface"]
        Input["3-Field Ingestion Contract<br/>(Rules, Facts, RequiredOutcome)"]:::inputStyle
    end

    subgraph PerceptionTier["2. Perception Engine (src/textProcessor.py)"]
        Config[".config<br/>(Model, Disabled Pipes, Labels)"]
        Model["Model Class<br/>(_loadModel, _warmup, _pruneDependencies)"]
        Harness["TextProcess Recipe Harness"]
        Recipe["Pluggable Recipe Steps<br/>(parsePayload, extractRules, extractFacts, assembleDto, exportJson)"]
        Config --> Model
        Model --> Harness
        Harness --> Recipe
    end

    subgraph DataTier["3. Validated Intermediate Representation"]
        DTO["Pydantic DTO Serialization<br/>(ParsedOutputDTO -> Validated JSON)"]:::dtoArray
    end

    subgraph ReasoningTier["4. Formal Reasoning Engine (src/logicEngine.py)"]
        Logic["LogicEngine SMT Coordinator"]
        DPLL["dpllEngine<br/>(NumPy Boolean CDCL SAT)"]
        SMT["smtEngine<br/>(NumPy 2-Phase Simplex LRA)"]
        Logic --> DPLL
        Logic --> SMT
    end

    subgraph OutputTier["5. Audit Trail & Decision Output"]
        Decision["Formal Decision Result<br/>(Status, Certified Model, UNSAT Core Audit Trail)"]:::outputStyle
    end

    Input --> Harness
    Recipe --> DTO
    DTO --> Logic
    Logic --> Decision
```
"""

def buildComponentDiagramContent() -> str:
    return """# Component Diagram

This document describes the modular component architecture, classes, and Pydantic DTO contracts across Yukti.

```mermaid
classDiagram
    direction TB

    class Model {
        +Path configPath
        +Dict config
        +Language nlp
        +loadModelToMemory() Language
        -_readConfig() Dict
        -_loadModel() Language
        -_warmup() None
        -_pruneDependencies() None
    }

    class DataInput {
        +List~str~ Rules
        +List~str~ Facts
        +List~str~ RequiredOutcome
    }

    class ParsedRuleDTO {
        +str ruleId
        +str originalText
        +str antecedent
        +str consequent
        +List~str~ extractedVariables
    }

    class ParsedFactDTO {
        +str symbol
        +str operator
        +Any value
    }

    class ParsedOutputDTO {
        +List~ParsedRuleDTO~ rules
        +List~ParsedFactDTO~ facts
        +List~str~ requiredOutcome
        +toJson() str
    }

    class TextProcess {
        +Language model
        +List steps
        +addStep(stepFunction) TextProcess
        +clearSteps() None
        +listSteps() List~str~
        +executePipeline(inputData) str
    }

    class Equation {
        +str symbol
        +str operator
        +Any value
        +bool isFact
        +str sourceId
        +str rawText
    }

    class LogicNode {
        +str nodeId
        +str nodeType
        +Equation equation
        +List~LogicNode~ children
        +Dict metadata
    }

    class AndOrGraph {
        +LogicNode root
        +Dict ruleNodes
        +Dict factNodes
        +List~Equation~ equations
        +Set~str~ symbols
        +collectLeaves() List~LogicNode~
        +summarizeGraph() Dict
    }

    class CnfFormula {
        +List~List~int~~ clauses
        +int numVariables
        +List~int~ trackingLiterals
        +LiteralMapping mapping
        +summarize() Dict
    }

    class LiteralMapping {
        +Dict literalToEquation
        +Dict equationToLiteral
        +Dict ruleToTrackingLiteral
        +Dict trackingLiteralToRule
    }

    class BaseEngine {
        +str engineName
        +str status
        +solve(payload) Any
        +explainConflict() List
        +resetEngine() None
    }

    class DpllEngine {
        +solveSat(cnf, assumptions) Dict
        +learnConflictClause(clause) None
    }

    class SmtEngine {
        +solveTheory(activeEquations) Dict
        +explainConflict() List
    }

    class AlgebraicEngine {
        <<Future Extension>>
        +solveAlgebraic(equations) Dict
    }

    class LogicEngine {
        +DpllEngine satSolver
        +List~BaseEngine~ theorySolvers
        +solvePolicy(payload) DecisionResult
        +extractUnsatCore(conflicts, mapping) List~str~
    }

    class chatInterface {
        +createFastApiApp() FastAPI
        +adjudicatePayload(inputData) Dict
        +openDefaultBrowser(host, port) None
        +startWebServer(host, port) None
    }

    DataInput --> TextProcess : Ingested By
    Model --> TextProcess : Injected Into
    TextProcess --> ParsedOutputDTO : Assembles
    ParsedOutputDTO --> AndOrGraph : Assembled By
    AndOrGraph --> LogicNode : Composed Of
    LogicNode --> Equation : Leaves
    AndOrGraph --> CnfFormula : Compiled Via Tseitin
    CnfFormula --> LiteralMapping : Indexed In
    BaseEngine <|-- DpllEngine : Extends
    BaseEngine <|-- SmtEngine : Extends
    BaseEngine <|-- AlgebraicEngine : Extends
    LogicEngine *-- DpllEngine : Wraps
    LogicEngine *-- SmtEngine : Wraps Theory
    chatInterface --> TextProcess : Submits Input
    chatInterface <-- LogicEngine : Displays Result
```
"""

def buildFlowDiagramContent() -> str:
    return """# Execution & Decision Flow Diagram

This document illustrates the execution lifecycle from input ingestion to certified SMT verification.

```mermaid
flowchart TD
    Start(["Input: Rules, Facts, Target"]) --> Parse["parsePayload<br/>(Normalize dict, str, or DataInput)"]
    Parse --> RuleExtract["extractRules<br/>(Regex Clause Segmenter & Variable Extraction)"]
    RuleExtract --> FactExtract["extractFacts<br/>(Single-Pass Regex Matching & Type Cast)"]
    FactExtract --> DepPrune["Prune Non-Semantic Dependency Tokens<br/>(det, punct, aux, meta)"]
    DepPrune --> DTOAssemble["assembleDto<br/>(Construct ParsedRuleDTO & ParsedFactDTO)"]
    DTOAssemble --> JSONExport["exportJson<br/>(Validate & Serialize via ParsedOutputDTO)"]
    
    JSONExport --> AOG["assembleAndOrGraph<br/>(Convert Rules & Facts to Logic Equations & AND-OR Graph)"]
    AOG --> SATInit["Initialize Boolean Abstraction & Tracking Literals"]
    SATInit --> CDCL["CDCL SAT Solver (dpllEngine)<br/>(Unit Propagation & Watched Literals)"]
    
    CDCL --> SATCheck{"Boolean SAT<br/>Consistent?"}
    SATCheck -- No --> SATUnsat["Extract Propositional UNSAT Core"]
    SATCheck -- Yes --> Simplex["Simplex LRA Solver (smtEngine)<br/>(Tableau Matrix Pivots & Bounds Check)"]
    
    Simplex --> TheoryCheck{"Linear Real<br/>Feasible?"}
    TheoryCheck -- No --> LearnConflict["Learn Theory Lemma Clause<br/>& Backjump"]
    LearnConflict --> CDCL
    TheoryCheck -- Yes --> SatSatisfied["Satisfied: Certified Assignment Model"]
    
    SATUnsat --> FormatResult["Map Conflict Literals to Rule Text"]
    SatSatisfied --> FormatResult
    FormatResult --> Verdict(["Decision: ACCEPTED / REJECTED + Audit Trail"])
```
"""

def buildSequenceDiagramContent() -> str:
    return """# Runtime Sequence Diagram

This document illustrates the runtime interactions between the user, chat interface, perception engine, and formal reasoning solvers.

```mermaid
sequenceDiagram
    autonumber
    actor User as User / Calling System
    participant UI as chatInterface
    participant TP as textProcessor (TextProcess)
    participant DTO as ParsedOutputDTO
    participant LE as logicEngine (LogicEngine)
    participant DPLL as dpllEngine (CDCL SAT)
    participant SMT as smtEngine (Simplex LRA)

    User->>UI: Submit Rules, Facts, and Required Outcome
    UI->>TP: executePipeline(DataInput)
    activate TP
    TP->>TP: parsePayload() & extractRules()
    TP->>TP: extractFacts() & pruneDependencies()
    TP->>DTO: assembleDto() & toJson()
    activate DTO
    DTO-->>TP: Validated JSON String
    deactivate DTO
    TP-->>UI: Return JSON Payload
    deactivate TP

    UI->>LE: solvePolicy(jsonPayload)
    activate LE
    LE->>DPLL: solveSat(booleanClauses)
    activate DPLL
    DPLL-->>LE: Propositional Assignment Model
    deactivate DPLL

    LE->>SMT: checkTheory(linearInequalities)
    activate SMT
    SMT-->>LE: Feasible / Infeasible (Theory Conflict Lemma)
    deactivate SMT

    opt On Theory Infeasibility
        LE->>DPLL: Add Conflict Clause & Re-solve
        DPLL-->>LE: Updated Assignment or Propositional UNSAT
    end

    LE->>LE: extractUnsatCore(conflicts)
    LE-->>UI: Return DecisionResult (Status, Audit Trail)
    deactivate LE

    UI-->>User: Display Formatted Verdict & Adverse Action Report
```
"""

def buildReadmeContent() -> str:
    return """# Architecture Specifications

This folder contains the authoritative architecture diagrams and code-driven specifications for **Yukti**.

## Available Diagrams

- 📋 [**System Overview**](./SystemOverview.md) — High-level end-to-end data processing and reasoning flow
- 🧩 [**Component Diagram**](./ComponentDiagram.md) — Modular classes, DTOs, and component boundaries
- 🔄 [**Execution Flow Diagram**](./FlowDiagram.md) — Execution step lifecycle from ingestion to SMT verdict
- ⏱️ [**Sequence Diagram**](./SequenceDiagram.md) — Chronological runtime interactions between components

## Synchronizing Architecture

To regenerate or verify the architecture documentation from code, run:

```bash
python3 Architecture/architectureSync.py
```
"""

# ======================================================================
# FILE WRITERS AND ORCHESTRATION
# ======================================================================

def writeDiagram(targetPath: Path, content: str) -> None:
    targetPath.write_text(content.strip() + "\n", encoding="utf-8")

def getDiagramBuilders() -> Dict[Path, Callable[[], str]]:
    return {
        SYSTEM_OVERVIEW_PATH: buildSystemOverviewContent,
        COMPONENT_DIAGRAM_PATH: buildComponentDiagramContent,
        FLOW_DIAGRAM_PATH: buildFlowDiagramContent,
        SEQUENCE_DIAGRAM_PATH: buildSequenceDiagramContent,
        README_PATH: buildReadmeContent,
    }

def synchronizeArchitecture() -> None:
    builders = getDiagramBuilders()
    for path, builder in builders.items():
        writeDiagram(path, builder())

if __name__ == "__main__":
    synchronizeArchitecture()
