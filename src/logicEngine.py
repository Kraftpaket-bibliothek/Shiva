import sys
from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

import numpy as np
from pydantic import BaseModel, Field

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.textProcessor import ParsedFactDTO, ParsedOutputDTO, ParsedRuleDTO


# ======================================================================
# ======================================================================
# PHASE 1: INGESTION & AND-OR GRAPH REPRESENTATION
# ======================================================================
# ======================================================================

# ======================================================================
# SECTION 1.1: GRAPH AND EQUATION DATA STRUCTURES
# ======================================================================

def _traverseLeaves(node: Optional["LogicNode"], sink: List["LogicNode"]) -> None:
    targets = [node] if node and not node.children else []
    sink.extend(targets)
    for child in node.children if node else []:
        _traverseLeaves(child, sink)


class NodeType(str, Enum):
    AND = "AND"
    OR = "OR"
    NOT = "NOT"
    EQUATION = "EQUATION"


class Equation(BaseModel):
    symbol: str = Field(description="Variable symbol name e.g. monthly_income")
    operator: str = Field(description="Comparison operator e.g. >=, <=, ==")
    value: Union[float, int, bool] = Field(description="Numeric or boolean bound")
    isFact: bool = Field(default=False, description="True if observed ground fact")
    sourceId: str = Field(default="", description="Rule or fact identifier")
    rawText: str = Field(default="", description="Original natural text span")


class LogicNode(BaseModel):
    nodeId: str = Field(description="Unique node identifier")
    nodeType: NodeType = Field(description="AND, OR, NOT, or EQUATION")
    equation: Optional[Equation] = Field(default=None, description="Theory equation if leaf")
    children: List["LogicNode"] = Field(default_factory=list, description="Sub-clauses")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Diagnostic payload")


class AndOrGraph(BaseModel):
    root: LogicNode = Field(description="Master policy root node")
    ruleNodes: Dict[str, LogicNode] = Field(default_factory=dict, description="Rule subtrees")
    factNodes: Dict[str, LogicNode] = Field(default_factory=dict, description="Fact leaves")
    equations: List[Equation] = Field(default_factory=list, description="Extracted theory equations")
    symbols: Set[str] = Field(default_factory=set, description="Distinct symbols present")

    def summarize(self) -> Dict[str, Any]:
        return {
            "ruleCount": len(self.ruleNodes),
            "factCount": len(self.factNodes),
            "equationCount": len(self.equations),
            "symbols": sorted(list(self.symbols)),
        }


# ======================================================================
# SECTION 1.2: GRAPH CONSTRUCTION & EQUATION GROUNDING
# ======================================================================
#---> Question we have to ask is wherever we are typing out ignore, why is that the errors are coming. Could it be that we are passing the wrong data type ?
class GraphBuilder:
    def _createEquationNode(self, equation: Equation, nodeId: str) -> LogicNode:
        return LogicNode(
            nodeId=nodeId,
            nodeType=NodeType.EQUATION,
            equation=equation,
            metadata={"sourceId": equation.sourceId, "rawText": equation.rawText},
        )

    def _convertFact(self, factDto: ParsedFactDTO) -> Equation:
        return Equation(
            symbol=factDto.symbol,
            operator="==",
            value=factDto.value, # type: ignore
            isFact=True,
            sourceId=factDto.factId,
            rawText=factDto.rawText,
        )

    def _buildConsequent(self, ruleDto: ParsedRuleDTO) -> Equation:
        return Equation(
            symbol=ruleDto.symbol,
            operator=ruleDto.operator,
            value=ruleDto.threshold, # type: ignore
            isFact=False,
            sourceId=ruleDto.ruleId,
            rawText=ruleDto.rawText,
        )

    def _buildAntecedent(self, ruleDto: ParsedRuleDTO) -> Optional[Equation]:
        hasAntecedent = bool(ruleDto.conditionSymbol)
        return Equation(
            symbol=str(ruleDto.conditionSymbol),
            operator=str(ruleDto.conditionOperator or "=="),
            value=ruleDto.conditionValue if ruleDto.conditionValue is not None else True, # type: ignore
            isFact=False,
            sourceId=ruleDto.ruleId,
            rawText=ruleDto.rawText,
        ) if hasAntecedent else None

    def _buildRuleBranch(self, ruleDto: ParsedRuleDTO) -> LogicNode:
        if not ruleDto.conditionSymbol:
            conseq = self._buildConsequent(ruleDto)
            return self._createEquationNode(conseq, ruleDto.ruleId)
        antecedent = self._buildAntecedent(ruleDto)
        consequent = self._buildConsequent(ruleDto)
        condLeaf = self._createEquationNode(antecedent, f"{ruleDto.ruleId}_COND")  # type: ignore
        notCond = LogicNode(nodeId=f"{ruleDto.ruleId}_NOT_COND", nodeType=NodeType.NOT, children=[condLeaf])
        conseqLeaf = self._createEquationNode(consequent, f"{ruleDto.ruleId}_REQ")
        return LogicNode(nodeId=ruleDto.ruleId, nodeType=NodeType.OR, children=[notCond, conseqLeaf])

    def _buildFactBranch(self, factDto: ParsedFactDTO) -> LogicNode:
        eq = self._convertFact(factDto)
        return self._createEquationNode(eq, factDto.factId)

    def buildGraph(self, dto: ParsedOutputDTO) -> AndOrGraph:
        rulesMap = {r.ruleId: self._buildRuleBranch(r) for r in dto.rules}
        factsMap = {f.factId: self._buildFactBranch(f) for f in dto.facts}
        root = LogicNode(
            nodeId="POLICY_ROOT",
            nodeType=NodeType.AND,
            children=list(rulesMap.values()) + list(factsMap.values()),
        )
        leaves: List[LogicNode] = []
        _traverseLeaves(root, leaves)
        eqs = [leaf.equation for leaf in leaves if leaf.equation is not None]
        return AndOrGraph(root=root, ruleNodes=rulesMap, factNodes=factsMap, equations=eqs, symbols={e.symbol for e in eqs})


# ======================================================================
# SECTION 1.3: PAYLOAD INGESTION & PARSER
# ======================================================================

class PayloadParser:
    parsers: Dict[Any, Callable[[Any], ParsedOutputDTO]] = {
        ParsedOutputDTO: lambda p: p,
        dict: lambda p: ParsedOutputDTO.model_validate(p),
        str: lambda p: ParsedOutputDTO.model_validate_json(p),
    }

    def parsePayload(self, payload: Union[str, Dict[str, Any], ParsedOutputDTO]) -> ParsedOutputDTO:
        parser = self.parsers.get(type(payload), lambda p: ParsedOutputDTO.model_validate_json(str(p)))
        return parser(payload)


# ======================================================================
# ======================================================================
# PHASE 2: BOOLEAN ABSTRACTION & TSEITIN CNF TRANSFORMATION
# ======================================================================
# ======================================================================

# ======================================================================
# SECTION 2.1: PROPOSITIONAL ABSTRACTION & CNF DATA MODELS
# ======================================================================

class PropositionalAbstractionTable(BaseModel):
    literalToEquation: Dict[int, Equation] = Field(default_factory=dict)
    equationToLiteral: Dict[str, int] = Field(default_factory=dict)
    ruleToTrackingLiteral: Dict[str, int] = Field(default_factory=dict)
    trackingLiteralToRule: Dict[int, str] = Field(default_factory=dict)


class CnfFormula(BaseModel):
    clauses: List[List[int]] = Field(default_factory=list)
    numVariables: int = 0
    numClauses: int = 0
    trackingLiterals: List[int] = Field(default_factory=list)
    abstractionTable: PropositionalAbstractionTable = Field(default_factory=PropositionalAbstractionTable)

    def summarize(self) -> Dict[str, Any]:
        return {
            "numVariables": self.numVariables,
            "numClauses": len(self.clauses),
            "trackingCount": len(self.trackingLiterals),
            "equationCount": len(self.abstractionTable.literalToEquation),
        }


# ======================================================================
# SECTION 2.2: CNF COMPILER INTERFACE & TSEITIN IMPLEMENTATION
# ======================================================================

class CnfCompilerInterface(ABC):
    @abstractmethod
    def compileToCnf(self, graph: AndOrGraph) -> CnfFormula:
        pass


class TseitinCnfCompiler(CnfCompilerInterface):
    def _buildEquationKey(self, eq: Equation) -> str:
        return f"{eq.symbol}:{eq.operator}:{eq.value}:{eq.isFact}"

    def _allocateEquationLiteral(self, table: PropositionalAbstractionTable, eq: Equation, counter: List[int]) -> int:
        key = self._buildEquationKey(eq)
        if key in table.equationToLiteral:
            return table.equationToLiteral[key]
        counter[0] += 1
        newLit = counter[0]
        table.equationToLiteral[key] = newLit
        table.literalToEquation[newLit] = eq
        return newLit

    def _allocateTrackingLiteral(self, table: PropositionalAbstractionTable, ruleId: str, counter: List[int]) -> int:
        counter[0] += 1
        trackingLit = counter[0]
        table.ruleToTrackingLiteral[ruleId] = trackingLit
        table.trackingLiteralToRule[trackingLit] = ruleId
        return trackingLit

    def _encodeAndClauses(self, parentVar: int, childVars: List[int]) -> List[List[int]]:
        parentImpliesChildren = [[-parentVar, c] for c in childVars]
        childrenImplyParent = [[parentVar] + [-c for c in childVars]]
        return parentImpliesChildren + childrenImplyParent

    def _encodeOrClauses(self, parentVar: int, childVars: List[int]) -> List[List[int]]:
        childrenImplyParent = [[parentVar, -c] for c in childVars]
        parentImpliesChildren = [[-parentVar] + childVars]
        return childrenImplyParent + parentImpliesChildren

    def _encodeNotClauses(self, parentVar: int, childVar: int) -> List[List[int]]:
        return [[-parentVar, -childVar], [parentVar, childVar]]

    def _dispatchTseitinEncoding(self, nodeType: str, parentVar: int, childVars: List[int]) -> List[List[int]]:
        encoders: Dict[str, Callable[[], List[List[int]]]] = {
            NodeType.AND: lambda: self._encodeAndClauses(parentVar, childVars),
            NodeType.OR: lambda: self._encodeOrClauses(parentVar, childVars),
            NodeType.NOT: lambda: self._encodeNotClauses(parentVar, childVars[0]),
        }
        return encoders.get(nodeType, lambda: [])()

    def _tseitinTraverse(
        self,
        node: LogicNode,
        table: PropositionalAbstractionTable,
        clauses: List[List[int]],
        counter: List[int],
    ) -> int:
        if node.nodeType == NodeType.EQUATION and node.equation:
            return self._allocateEquationLiteral(table, node.equation, counter)
        childVars = [self._tseitinTraverse(child, table, clauses, counter) for child in node.children]
        counter[0] += 1
        parentVar = counter[0]
        clauses.extend(self._dispatchTseitinEncoding(node.nodeType, parentVar, childVars))
        return parentVar

    def compileToCnf(self, graph: AndOrGraph) -> CnfFormula:
        table = PropositionalAbstractionTable()
        clauses: List[List[int]] = []
        counter = [0]
        trackingLits: List[int] = []
        for ruleId, ruleNode in graph.ruleNodes.items():
            ruleVar = self._tseitinTraverse(ruleNode, table, clauses, counter)
            trackLit = self._allocateTrackingLiteral(table, ruleId, counter)
            trackingLits.append(trackLit)
            clauses.append([-trackLit, ruleVar])
        for factNode in graph.factNodes.values():
            factVar = self._tseitinTraverse(factNode, table, clauses, counter)
            clauses.append([factVar])
        return CnfFormula(
            clauses=clauses,
            numVariables=counter[0],
            numClauses=len(clauses),
            trackingLiterals=trackingLits,
            abstractionTable=table,
        )


# ======================================================================
# ======================================================================
# PHASE 3: BASE ENGINE & EXTENSIBLE REASONING SOLVERS
# ======================================================================
# ======================================================================

# ======================================================================
# SECTION 3.1: DECISION RESULT & BASE ENGINE HIERARCHY
# ======================================================================

class EngineStatus(str, Enum):
    INITIALIZED = "INITIALIZED"
    SATISFIABLE = "SATISFIABLE"
    UNSATISFIABLE = "UNSATISFIABLE"
    FEASIBLE = "FEASIBLE"
    INFEASIBLE = "INFEASIBLE"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    UNKNOWN = "UNKNOWN"


class DecisionResult(BaseModel):
    status: str = Field(description="Adjudication verdict: ACCEPTED, REJECTED, or UNKNOWN")
    certifiedModel: Dict[str, Any] = Field(default_factory=dict, description="Satisfying model assignment if feasible")
    unsatCore: List[str] = Field(default_factory=list, description="Violated rule IDs or descriptions on conflict")
    details: Dict[str, Any] = Field(default_factory=dict, description="Solver diagnostic metrics and lemma statistics")


class BaseEngine:
    def __init__(self, engineName: str = "BaseEngine") -> None:
        self.engineName: str = engineName
        self.status: EngineStatus = EngineStatus.INITIALIZED

    def solve(self, payload: Any) -> Any:
        raise NotImplementedError

    def explainConflict(self) -> List[Any]:
        return []


# ======================================================================
# SECTION 3.2: PROPOSITIONAL CDCL SAT SOLVER (DPLL ENGINE)
# ======================================================================

class DpllEngine(BaseEngine):
    def __init__(self) -> None:
        super().__init__(engineName="DpllEngine")
        self.learnedClauses: List[List[int]] = []

    def _initWatchedLiterals(self, clauses: List[List[int]], numVars: int) -> Dict[int, List[int]]:
        watches: Dict[int, List[int]] = {lit: [] for var in range(1, numVars + 1) for lit in (var, -var)}
        for idx, clause in enumerate(clauses):
            targets = clause[:2] if len(clause) >= 2 else clause[:1]
            for lit in targets:
                watches[lit].append(idx)
        return watches

    def _assignLiteral(
        self,
        lit: int,
        level: int,
        antecedent: int,
        assignments: np.ndarray,
        trailLevels: np.ndarray,
        antecedents: np.ndarray,
        trail: List[int],
    ) -> None:
        var = abs(lit)
        assignments[var] = np.int8(1 if lit > 0 else 0)
        trailLevels[var] = level
        antecedents[var] = antecedent
        trail.append(lit)

    def _isLiteralSatisfied(self, lit: int, assignments: np.ndarray) -> bool:
        val = assignments[abs(lit)]
        return bool(val == 1 if lit > 0 else val == 0)

    def _isLiteralFalsified(self, lit: int, assignments: np.ndarray) -> bool:
        val = assignments[abs(lit)]
        return bool(val == 0 if lit > 0 else val == 1)

    def _findAlternativeWatch(
        self,
        clause: List[int],
        falsifiedLit: int,
        otherWatch: int,
        assignments: np.ndarray,
    ) -> Optional[int]:
        for lit in clause:
            if lit != otherWatch and not self._isLiteralFalsified(lit, assignments):
                return lit
        return None

    def _propagateTwoWatchedLiterals(
        self,
        falsifiedLit: int,
        clauses: List[List[int]],
        assignments: np.ndarray,
        watches: Dict[int, List[int]],
        trailLevels: np.ndarray,
        antecedents: np.ndarray,
        trail: List[int],
        currentLevel: int,
    ) -> Optional[int]:
        watchingClauses = list(watches.get(falsifiedLit, []))
        for cIdx in watchingClauses:
            clause = clauses[cIdx]
            otherWatch = clause[1] if clause[0] == falsifiedLit else clause[0]
            if self._isLiteralSatisfied(otherWatch, assignments):
                continue
            altLit = self._findAlternativeWatch(clause, falsifiedLit, otherWatch, assignments)
            if altLit:
                watches[falsifiedLit].remove(cIdx)
                watches[altLit].append(cIdx)
                continue
            if assignments[abs(otherWatch)] == -1:
                self._assignLiteral(otherWatch, currentLevel, cIdx, assignments, trailLevels, antecedents, trail)
            elif self._isLiteralFalsified(otherWatch, assignments):
                return cIdx
        return None

    def _analyzeConflict1UIP(
        self,
        conflictIdx: int,
        clauses: List[List[int]],
        trail: List[int],
        trailLevels: np.ndarray,
        antecedents: np.ndarray,
        currentLevel: int,
    ) -> Tuple[List[int], int]:
        learned = set(clauses[conflictIdx])
        currentLevelLiterals = [lit for lit in learned if trailLevels[abs(lit)] == currentLevel]
        trailIdx = len(trail) - 1
        while len(currentLevelLiterals) > 1 and trailIdx >= 0:
            trailLit = trail[trailIdx]
            trailIdx -= 1
            if -trailLit in learned and antecedents[abs(trailLit)] >= 0:
                learned.remove(-trailLit)
                learned.update(clauses[antecedents[abs(trailLit)]])
                currentLevelLiterals = [lit for lit in learned if trailLevels[abs(lit)] == currentLevel]
        learnedList = list(learned)
        levels = [trailLevels[abs(lit)] for lit in learnedList if trailLevels[abs(lit)] < currentLevel]
        backjumpLevel = max(levels) if levels else 0
        return learnedList, backjumpLevel

    def _backjumpToLevel(
        self,
        targetLevel: int,
        trail: List[int],
        assignments: np.ndarray,
        trailLevels: np.ndarray,
        antecedents: np.ndarray,
    ) -> None:
        while trail and trailLevels[abs(trail[-1])] > targetLevel:
            poppedLit = trail.pop()
            var = abs(poppedLit)
            assignments[var] = np.int8(-1)
            trailLevels[var] = -1
            antecedents[var] = -1

    def _pickBranchingLiteral(self, assignments: np.ndarray, activityScores: np.ndarray) -> Optional[int]:
        unassigned = np.where(assignments[1:] == -1)[0] + 1
        if len(unassigned) == 0:
            return None
        scores = activityScores[unassigned]
        bestVar = int(unassigned[np.argmax(scores)])
        return bestVar

    def solveSat(self, cnf: CnfFormula, assumptions: Optional[List[int]] = None) -> Dict[str, Any]:
        numVars = cnf.numVariables
        clauses = [list(c) for c in cnf.clauses]
        assignments = np.full(numVars + 1, -1, dtype=np.int8)
        trailLevels = np.full(numVars + 1, -1, dtype=np.int32)
        antecedents = np.full(numVars + 1, -1, dtype=np.int32)
        activityScores = np.ones(numVars + 1, dtype=np.float64)
        trail: List[int] = []
        watches = self._initWatchedLiterals(clauses, numVars)
        currentLevel = 0
        for unitClause in [c for c in clauses if len(c) == 1]:
            self._assignLiteral(unitClause[0], 0, -1, assignments, trailLevels, antecedents, trail)
        activeAssumptions = list(assumptions or [])
        for aLit in activeAssumptions:
            currentLevel += 1
            self._assignLiteral(aLit, currentLevel, -1, assignments, trailLevels, antecedents, trail)
            conflictIdx = self._propagateTwoWatchedLiterals(
                -aLit, clauses, assignments, watches, trailLevels, antecedents, trail, currentLevel
            )
            if conflictIdx is not None:
                self.status = EngineStatus.UNSATISFIABLE
                return {"status": EngineStatus.UNSATISFIABLE.value, "assignments": {}, "conflict": [aLit]}
        while True:
            branchLit = self._pickBranchingLiteral(assignments, activityScores)
            if branchLit is None:
                self.status = EngineStatus.SATISFIABLE
                resModel = {v: bool(assignments[v] == 1) for v in range(1, numVars + 1)}
                return {"status": EngineStatus.SATISFIABLE.value, "assignments": resModel, "conflict": []}
            currentLevel += 1
            self._assignLiteral(branchLit, currentLevel, -1, assignments, trailLevels, antecedents, trail)
            conflictIdx = self._propagateTwoWatchedLiterals(
                -branchLit, clauses, assignments, watches, trailLevels, antecedents, trail, currentLevel
            )
            while conflictIdx is not None:
                if currentLevel == 0:
                    self.status = EngineStatus.UNSATISFIABLE
                    return {"status": EngineStatus.UNSATISFIABLE.value, "assignments": {}, "conflict": []}
                learnedClause, backjumpLevel = self._analyzeConflict1UIP(
                    conflictIdx, clauses, trail, trailLevels, antecedents, currentLevel
                )
                clauses.append(learnedClause)
                self.learnedClauses.append(learnedClause)
                self._backjumpToLevel(backjumpLevel, trail, assignments, trailLevels, antecedents)
                currentLevel = backjumpLevel
                if len(learnedClause) > 0:
                    self._assignLiteral(learnedClause[0], currentLevel, len(clauses) - 1, assignments, trailLevels, antecedents, trail)
                conflictIdx = None

    def solve(self, payload: Any) -> Any:
        return self.solveSat(payload)


# ======================================================================
# SECTION 3.3: LINEAR REAL ARITHMETIC THEORY SOLVER (SMT ENGINE)
# ======================================================================

class SmtEngine(BaseEngine):
    def __init__(self) -> None:
        super().__init__(engineName="SmtEngine")
        self.conflictLemmas: List[List[Equation]] = []

    def _buildSymbolIndex(self, equations: List[Equation]) -> Dict[str, int]:
        uniqueSymbols = sorted(list({eq.symbol for eq in equations}))
        return {sym: idx for idx, sym in enumerate(uniqueSymbols)}

    def _assignEquationBounds(
        self,
        operator: str,
        val: float,
        rowIdx: int,
        lowerBounds: np.ndarray,
        upperBounds: np.ndarray,
    ) -> None:
        if operator in (">=", ">"):
            lowerBounds[rowIdx] = val
        elif operator in ("<=", "<"):
            upperBounds[rowIdx] = val
        elif operator == "==":
            lowerBounds[rowIdx] = val
            upperBounds[rowIdx] = val

    def _buildSimplexTableau(
        self,
        equations: List[Equation],
        symbolMap: Dict[str, int],
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        numRows = len(equations)
        numCols = len(symbolMap)
        tableau = np.zeros((numRows, numCols), dtype=np.float64)
        lowerBounds = np.full(numRows, -np.inf, dtype=np.float64)
        upperBounds = np.full(numRows, np.inf, dtype=np.float64)
        colValues = np.zeros(numCols, dtype=np.float64)
        colFrozen = np.zeros(numCols, dtype=bool)
        for rowIdx, eq in enumerate(equations):
            colIdx = symbolMap[eq.symbol]
            tableau[rowIdx, colIdx] = 1.0
            val = float(eq.value) if isinstance(eq.value, (int, float)) else (1.0 if eq.value is True else 0.0)
            self._assignEquationBounds(eq.operator, val, rowIdx, lowerBounds, upperBounds)
            if eq.isFact:
                colValues[colIdx] = val
                colFrozen[colIdx] = True
        rowValues = tableau @ colValues
        return tableau, lowerBounds, upperBounds, rowValues, colFrozen

    def _findViolatedBasicRow(
        self,
        values: np.ndarray,
        lowerBounds: np.ndarray,
        upperBounds: np.ndarray,
    ) -> Optional[int]:
        violations = np.where((values < lowerBounds) | (values > upperBounds))[0]
        return int(violations[0]) if len(violations) > 0 else None

    def _findEligiblePivotCol(
        self,
        rowIdx: int,
        tableau: np.ndarray,
        values: np.ndarray,
        lowerBounds: np.ndarray,
        upperBounds: np.ndarray,
        colFrozen: np.ndarray,
    ) -> Optional[int]:
        rowCoeffs = tableau[rowIdx]
        isBelow = values[rowIdx] < lowerBounds[rowIdx]
        for colIdx, coeff in enumerate(rowCoeffs):
            if not colFrozen[colIdx]:
                if isBelow and coeff > 0:
                    return colIdx
                if not isBelow and coeff < 0:
                    return colIdx
        return None

    def _pivotSimplexTableau(
        self,
        tableau: np.ndarray,
        values: np.ndarray,
        rowIdx: int,
        colIdx: int,
    ) -> None:
        pivotVal = tableau[rowIdx, colIdx]
        tableau[rowIdx] /= pivotVal
        for otherRow in range(tableau.shape[0]):
            if otherRow != rowIdx and tableau[otherRow, colIdx] != 0:
                factor = tableau[otherRow, colIdx]
                tableau[otherRow] -= factor * tableau[rowIdx]
                values[otherRow] -= factor * values[rowIdx]

    def solveTheory(self, activeEquations: List[Equation]) -> Dict[str, Any]:
        if not activeEquations:
            self.status = EngineStatus.FEASIBLE
            return {"status": EngineStatus.FEASIBLE.value, "conflicts": []}
        symbolMap = self._buildSymbolIndex(activeEquations)
        tableau, lowerBounds, upperBounds, rowValues, colFrozen = self._buildSimplexTableau(activeEquations, symbolMap)
        maxPivots = max(500, len(activeEquations) * 5)
        for _ in range(maxPivots):
            violatedRow = self._findViolatedBasicRow(rowValues, lowerBounds, upperBounds)
            if violatedRow is None:
                self.status = EngineStatus.FEASIBLE
                return {"status": EngineStatus.FEASIBLE.value, "conflicts": []}
            pivotCol = self._findEligiblePivotCol(violatedRow, tableau, rowValues, lowerBounds, upperBounds, colFrozen)
            if pivotCol is None:
                self.status = EngineStatus.INFEASIBLE
                allViolations = [
                    activeEquations[r]
                    for r in range(len(activeEquations))
                    if (rowValues[r] < lowerBounds[r] or rowValues[r] > upperBounds[r])
                    and self._findEligiblePivotCol(r, tableau, rowValues, lowerBounds, upperBounds, colFrozen) is None
                ]
                conflict = allViolations if allViolations else [activeEquations[violatedRow]]
                self.conflictLemmas.append(conflict)
                return {"status": EngineStatus.INFEASIBLE.value, "conflicts": conflict}
            self._pivotSimplexTableau(tableau, rowValues, violatedRow, pivotCol)
        self.status = EngineStatus.INFEASIBLE
        return {"status": EngineStatus.INFEASIBLE.value, "conflicts": activeEquations}

    def solve(self, payload: Any) -> Any:
        return self.solveTheory(payload)

    def explainConflict(self) -> List[Equation]:
        return self.conflictLemmas[-1] if self.conflictLemmas else []


# ======================================================================
# SECTION 3.4: LOGIC ENGINE MASTER COORDINATOR WRAPPER
# ======================================================================

class LogicEngine:
    def __init__(
        self,
        satSolver: Optional[DpllEngine] = None,
        theorySolvers: Optional[List[BaseEngine]] = None,
        cnfCompiler: Optional[CnfCompilerInterface] = None,
        payloadParser: Optional[PayloadParser] = None,
        graphBuilder: Optional[GraphBuilder] = None,
    ) -> None:
        self.satSolver: DpllEngine = satSolver or DpllEngine()
        self.theorySolvers: List[BaseEngine] = theorySolvers or [SmtEngine()]
        self.cnfCompiler: CnfCompilerInterface = cnfCompiler or TseitinCnfCompiler()
        self.payloadParser: PayloadParser = payloadParser or PayloadParser()
        self.graphBuilder: GraphBuilder = graphBuilder or GraphBuilder()

    def _resolveGraph(self, payload: Union[str, Dict[str, Any], ParsedOutputDTO, AndOrGraph]) -> AndOrGraph:
        if isinstance(payload, AndOrGraph):
            return payload
        dto = self.payloadParser.parsePayload(payload)
        return self.graphBuilder.buildGraph(dto)

    def _extractActiveEquations(self, cnf: CnfFormula, satResult: Dict[str, Any], graph: AndOrGraph) -> List[Equation]:
        satAssignments = satResult.get("assignments", {})
        activeRuleEqs = [
            eq for lit, eq in cnf.abstractionTable.literalToEquation.items()
            if not eq.isFact and satAssignments.get(lit, False)
        ]
        activeFactEqs = [eq for eq in graph.equations if eq.isFact]
        return activeRuleEqs + activeFactEqs

    def solvePolicy(
        self,
        payload: Union[str, Dict[str, Any], ParsedOutputDTO, AndOrGraph],
    ) -> DecisionResult:
        graph = self._resolveGraph(payload)
        cnf = self.cnfCompiler.compileToCnf(graph)
        satResult = self.satSolver.solveSat(cnf, assumptions=cnf.trackingLiterals)
        smtSolver = next((s for s in self.theorySolvers if isinstance(s, SmtEngine)), SmtEngine())
        activeEquations = self._extractActiveEquations(cnf, satResult, graph)
        theoryResult = smtSolver.solveTheory(activeEquations)
        isAccepted = satResult["status"] == EngineStatus.SATISFIABLE.value and theoryResult["status"] == EngineStatus.FEASIBLE.value
        status = EngineStatus.ACCEPTED.value if isAccepted else EngineStatus.REJECTED.value
        unsatRules = [eq.sourceId for eq in theoryResult.get("conflicts", []) if not eq.isFact]
        modelDict = {str(k): v for k, v in satResult.get("assignments", {}).items()}
        return DecisionResult(
            status=status,
            certifiedModel=modelDict if isAccepted else {},
            unsatCore=unsatRules,
            details={
                "numClauses": len(cnf.clauses),
                "numVariables": cnf.numVariables,
                "satStatus": satResult["status"],
                "theoryStatus": theoryResult["status"],
            },
        )
