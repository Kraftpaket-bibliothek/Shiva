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
