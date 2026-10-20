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
        Parser["PayloadParser<br/>(Concrete Ingestion Parser)"]
        GB["GraphBuilder<br/>(AST Grounding & Equation Nodes)"]
        Compiler["CnfCompilerInterface<br/>(TseitinCnfCompiler Implementation)"]
        Logic["LogicEngine SMT Coordinator"]
        DPLL["DpllEngine<br/>(NumPy Boolean CDCL SAT)"]
        SMT["SmtEngine<br/>(NumPy 2-Phase Simplex LRA)"]
        Parser --> GB
        GB --> Compiler
        Compiler --> Logic
        Logic --> DPLL
        Logic --> SMT
    end

    subgraph OutputTier["5. Audit Trail & Decision Output"]
        Decision["Formal Decision Result<br/>(Status, Certified Model, UNSAT Core Audit Trail)"]:::outputStyle
    end

    Input --> Harness
    Recipe --> DTO
    DTO --> Parser
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
        +str symbol
        +str operator
        +Any threshold
        +str conditionSymbol
        +str conditionOperator
        +Any conditionValue
        +str rawText
    }

    class ParsedFactDTO {
        +str factId
        +str symbol
        +Any value
        +str rawText
    }

    class ParsedOutputDTO {
        +List~ParsedRuleDTO~ rules
        +List~ParsedFactDTO~ facts
        +str requiredOutcome
        +str parsingStatus
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

    class PayloadParser {
        +parsePayload(payload) ParsedOutputDTO
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
        +NodeType nodeType
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
        +summarize() Dict
    }

    class GraphBuilder {
        +buildGraph(dto) AndOrGraph
        -_createEquationNode(equation, nodeId) LogicNode
        -_convertFact(factDto) Equation
        -_buildConsequent(ruleDto) Equation
        -_buildAntecedent(ruleDto) Equation
        -_buildRuleBranch(ruleDto) LogicNode
        -_buildFactBranch(factDto) LogicNode
    }

    class PropositionalAbstractionTable {
        +Dict literalToEquation
        +Dict equationToLiteral
        +Dict ruleToTrackingLiteral
        +Dict trackingLiteralToRule
    }

    class CnfFormula {
        +List~List~int~~ clauses
        +int numVariables
        +int numClauses
        +List~int~ trackingLiterals
        +PropositionalAbstractionTable abstractionTable
        +summarize() Dict
    }

    class CnfCompilerInterface {
        <<interface>>
        +compileToCnf(graph) CnfFormula*
    }

    class TseitinCnfCompiler {
        +compileToCnf(graph) CnfFormula
        -_buildEquationKey(eq) str
        -_allocateEquationLiteral(table, eq, counter) int
        -_allocateTrackingLiteral(table, ruleId, counter) int
        -_encodeAndClauses(parentVar, childVars) List
        -_encodeOrClauses(parentVar, childVars) List
        -_encodeNotClauses(parentVar, childVar) List
        -_dispatchTseitinEncoding(nodeType, parentVar, childVars) List
        -_tseitinTraverse(node, table, clauses, counter) int
    }

    class EngineStatus {
        <<enumeration>>
        INITIALIZED
        SATISFIABLE
        UNSATISFIABLE
        FEASIBLE
        INFEASIBLE
        ACCEPTED
        REJECTED
        UNKNOWN
    }

    class BaseEngine {
        +str engineName
        +EngineStatus status
        +solve(payload) Any
        +explainConflict() List
    }

    class DpllEngine {
        +List learnedClauses
        +solveSat(cnf, assumptions) Dict
        +solve(payload) Any
        -_initWatchedLiterals(clauses, numVars) Dict
        -_assignLiteral(lit, level, antecedent, assignments, trailLevels, antecedents, trail) None
        -_isLiteralSatisfied(lit, assignments) bool
        -_isLiteralFalsified(lit, assignments) bool
        -_findAlternativeWatch(clause, falsifiedLit, otherWatch, assignments) int
        -_propagateTwoWatchedLiterals(falsifiedLit, clauses, assignments, watches, trailLevels, antecedents, trail, currentLevel) int
        -_analyzeConflict1UIP(conflictIdx, clauses, trail, trailLevels, antecedents, currentLevel) Tuple
        -_backjumpToLevel(targetLevel, trail, assignments, trailLevels, antecedents) None
        -_pickBranchingLiteral(assignments, activityScores) int
    }

    class SmtEngine {
        +List conflictLemmas
        +solveTheory(activeEquations) Dict
        +solve(payload) Any
        +explainConflict() List
        -_buildSymbolIndex(equations) Dict
        -_assignEquationBounds(operator, val, rowIdx, lowerBounds, upperBounds) None
        -_buildSimplexTableau(equations, symbolMap) Tuple
        -_findViolatedBasicRow(values, lowerBounds, upperBounds) int
        -_findEligiblePivotCol(rowIdx, tableau, values, lowerBounds, upperBounds, colFrozen) int
        -_pivotSimplexTableau(tableau, values, rowIdx, colIdx) None
    }

    class LogicEngine {
        +DpllEngine satSolver
        +List~BaseEngine~ theorySolvers
        +CnfCompilerInterface cnfCompiler
        +PayloadParser payloadParser
        +GraphBuilder graphBuilder
        +solvePolicy(payload) DecisionResult
        -_resolveGraph(payload) AndOrGraph
        -_extractActiveEquations(cnf, satResult, graph) List
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
    ParsedOutputDTO --> PayloadParser : Ingested By
    PayloadParser --> GraphBuilder : Ingested By
    GraphBuilder --> AndOrGraph : Constructs
    AndOrGraph --> LogicNode : Composed Of
    LogicNode --> Equation : Leaves
    CnfCompilerInterface <|.. TseitinCnfCompiler : Implements
    GraphBuilder --> CnfCompilerInterface : Transformed By
    CnfCompilerInterface --> CnfFormula : Generates
    CnfFormula --> PropositionalAbstractionTable : Registers In
    BaseEngine <|-- DpllEngine : Extends
    BaseEngine <|-- SmtEngine : Extends
    LogicEngine *-- DpllEngine : Coordinates SAT
    LogicEngine *-- SmtEngine : Coordinates SMT
    LogicEngine *-- CnfCompilerInterface : Uses
    LogicEngine *-- PayloadParser : Uses
    LogicEngine *-- GraphBuilder : Uses
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
    
    JSONExport --> PP["PayloadParser<br/>(Validate & Hydrate ParsedOutputDTO)"]
    PP --> GB["GraphBuilder<br/>(Ground Equations & Assemble AndOrGraph)"]
    GB --> Tseitin["TseitinCnfCompiler<br/>(Encode AST & Populate PropositionalAbstractionTable)"]
    
    Tseitin --> CDCL["DpllEngine (CDCL SAT)<br/>(2WL Propagation, VSIDS, 1UIP Conflict Analysis)"]
    
    CDCL --> SATCheck{"Boolean SAT<br/>Consistent?"}
    SATCheck -- No --> SATUnsat["Extract Propositional UNSAT Core"]
    SATCheck -- Yes --> Simplex["SmtEngine (Simplex LRA)<br/>(Tableau Matrix Pivots & Bounds Check)"]
    
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
    participant GB as GraphBuilder
    participant TC as TseitinCnfCompiler
    participant DPLL as DpllEngine (CDCL SAT)
    participant SMT as SmtEngine (Simplex LRA)

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
    LE->>GB: buildGraph(parsedDto)
    activate GB
    GB-->>LE: AndOrGraph
    deactivate GB

    LE->>TC: compileToCnf(graph)
    activate TC
    TC-->>LE: CnfFormula (with PropositionalAbstractionTable)
    deactivate TC

    LE->>DPLL: solveSat(cnf, assumptions)
    activate DPLL
    DPLL-->>LE: Propositional Assignment Model
    deactivate DPLL

    LE->>SMT: solveTheory(activeEquations)
    activate SMT
    SMT-->>LE: Feasible / Infeasible (Theory Conflict Lemma)
    deactivate SMT

    opt On Theory Infeasibility
        LE->>DPLL: Add Conflict Clause & Re-solve
        DPLL-->>LE: Updated Assignment or Propositional UNSAT
    end

    LE->>LE: Formulate DecisionResult (Status, UNSAT Core)
    LE-->>UI: Return DecisionResult
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
