# Runtime Sequence Diagram

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
