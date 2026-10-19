# Component Diagram

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
