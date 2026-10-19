from __future__ import annotations

from pathlib import Path
import sys
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
import numpy as np
from pydantic import BaseModel, Field

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.textProcessor import ParsedFactDTO, ParsedOutputDTO, ParsedRuleDTO


# ======================================================================
# ======================================================================
# PHASE 1: INGESTION, LOGIC EQUATIONS & AND-OR GRAPH
# ======================================================================
# ======================================================================

# ======================================================================
# SECTION 1.1: GRAPH AND EQUATION DATA STRUCTURES
# ======================================================================

def _traverseLeaves(node: Optional[LogicNode], sink: List[LogicNode]) -> None:
    targets = [node] if node and not node.children else []
    sink.extend(targets)
    for child in (node.children if node else []):
        _traverseLeaves(child, sink)


class NodeType:
    AND: str = "AND"
    OR: str = "OR"
    NOT: str = "NOT"
    EQUATION: str = "EQUATION"


class Equation(BaseModel):
    symbol: str = Field(description="Normalized variable identifier")
    operator: str = Field(description="Mathematical or equality operator")
    value: Union[float, int, bool, str] = Field(description="Target threshold or observed value")
    isFact: bool = Field(default=False, description="Flag indicating if equation is an observed case fact")
    sourceId: str = Field(default="", description="Identifier of source rule or fact")
    rawText: str = Field(default="", description="Original natural language text")


class LogicNode(BaseModel):
    nodeId: str = Field(description="Unique identifier for graph node")
    nodeType: str = Field(description="Logical node type: AND, OR, NOT, EQUATION")
    equation: Optional[Equation] = Field(default=None, description="Equation payload for leaf nodes")
    children: List[LogicNode] = Field(default_factory=list, description="Subtree child nodes")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Auxiliary node metadata")


class AndOrGraph(BaseModel):
    root: Optional[LogicNode] = Field(default=None, description="Top-level master policy conjunction node")
    ruleNodes: Dict[str, LogicNode] = Field(default_factory=dict, description="Registry of rule subtrees")
    factNodes: Dict[str, LogicNode] = Field(default_factory=dict, description="Registry of fact subtrees")
    equations: List[Equation] = Field(default_factory=list, description="Collection of all graph equations")
    symbols: Set[str] = Field(default_factory=set, description="Distinct symbols present across equations")

    def collectLeaves(self) -> List[LogicNode]:
        collector: List[LogicNode] = []
        _traverseLeaves(self.root, collector)
        return collector

    def summarizeGraph(self) -> Dict[str, Any]:
        return {
            "rootId": self.root.nodeId if self.root else None,
            "ruleCount": len(self.ruleNodes),
            "factCount": len(self.factNodes),
            "equationCount": len(self.equations),
            "symbols": sorted(list(self.symbols)),
        }


# ======================================================================
# SECTION 1.2: EQUATION FACTORIES AND BUILDERS
# ======================================================================

def createEquationNode(equation: Equation, nodeId: str) -> LogicNode:
    return LogicNode(
        nodeId=nodeId,
        nodeType=NodeType.EQUATION,
        equation=equation,
        metadata={"sourceId": equation.sourceId, "rawText": equation.rawText},
    )


def convertFactToEquation(factDto: ParsedFactDTO) -> Equation:
    return Equation(
        symbol=factDto.symbol,
        operator="==",
        value=factDto.value,
        isFact=True,
        sourceId=factDto.factId,
        rawText=factDto.rawText,
    )


def buildConsequentEquation(ruleDto: ParsedRuleDTO) -> Equation:
    return Equation(
        symbol=ruleDto.symbol,
        operator=ruleDto.operator,
        value=ruleDto.threshold,
        isFact=False,
        sourceId=ruleDto.ruleId,
        rawText=ruleDto.rawText,
    )


def buildAntecedentEquation(ruleDto: ParsedRuleDTO) -> Optional[Equation]:
    hasAntecedent = bool(ruleDto.conditionSymbol)
    return Equation(
        symbol=str(ruleDto.conditionSymbol),
        operator=str(ruleDto.conditionOperator or "=="),
        value=ruleDto.conditionValue if ruleDto.conditionValue is not None else True,
        isFact=False,
        sourceId=ruleDto.ruleId,
        rawText=ruleDto.rawText,
    ) if hasAntecedent else None


# ======================================================================
# SECTION 1.3: AND-OR BRANCH DISPATCHERS
# ======================================================================

def buildUnconditionalBranch(ruleDto: ParsedRuleDTO) -> LogicNode:
    consequentEq = buildConsequentEquation(ruleDto)
    return createEquationNode(consequentEq, ruleDto.ruleId)


def buildConditionalBranch(ruleDto: ParsedRuleDTO) -> LogicNode:
    antecedentEq = buildAntecedentEquation(ruleDto)
    consequentEq = buildConsequentEquation(ruleDto)
    condLeaf = createEquationNode(antecedentEq, f"{ruleDto.ruleId}_COND") # type: ignore
    notCondNode = LogicNode(nodeId=f"{ruleDto.ruleId}_NOT_COND", nodeType=NodeType.NOT, children=[condLeaf])
    conseqLeaf = createEquationNode(consequentEq, f"{ruleDto.ruleId}_REQ")
    return LogicNode(nodeId=ruleDto.ruleId, nodeType=NodeType.OR, children=[notCondNode, conseqLeaf])


def dispatchRuleBranch(ruleDto: ParsedRuleDTO) -> LogicNode:
    builder = buildConditionalBranch if ruleDto.conditionSymbol else buildUnconditionalBranch
    return builder(ruleDto)


def buildFactBranch(factDto: ParsedFactDTO) -> LogicNode:
    factEq = convertFactToEquation(factDto)
    return createEquationNode(factEq, factDto.factId)


# ======================================================================
# SECTION 1.4: AND-OR GRAPH PIPELINE COORDINATOR
# ======================================================================

PAYLOAD_PARSERS: Dict[Any, Callable[[Any], ParsedOutputDTO]] = {
    ParsedOutputDTO: lambda p: p,
    dict: lambda p: ParsedOutputDTO.model_validate(p),
    str: lambda p: ParsedOutputDTO.model_validate_json(p),
}


def parseJsonPayload(payload: Union[str, Dict[str, Any], ParsedOutputDTO]) -> ParsedOutputDTO:
    parser = PAYLOAD_PARSERS.get(type(payload), lambda p: ParsedOutputDTO.model_validate_json(str(p)))
    return parser(payload)


def collectSymbols(equations: List[Equation]) -> Set[str]:
    return {eq.symbol for eq in equations}


def buildRuleSubtrees(rules: List[ParsedRuleDTO]) -> Dict[str, LogicNode]:
    return {r.ruleId: dispatchRuleBranch(r) for r in rules}


def buildFactSubtrees(facts: List[ParsedFactDTO]) -> Dict[str, LogicNode]:
    return {f.factId: buildFactBranch(f) for f in facts}


def buildMasterRoot(ruleNodes: Dict[str, LogicNode], factNodes: Dict[str, LogicNode]) -> LogicNode:
    allChildren = list(ruleNodes.values()) + list(factNodes.values())
    return LogicNode(nodeId="POLICY_ROOT", nodeType=NodeType.AND, children=allChildren)


def extractAllEquations(leaves: List[LogicNode]) -> List[Equation]:
    return [leaf.equation for leaf in leaves if leaf.equation is not None]


def assembleAndOrGraph(payload: Union[str, Dict[str, Any], ParsedOutputDTO]) -> AndOrGraph:
    dto = parseJsonPayload(payload)
    rulesMap = buildRuleSubtrees(dto.rules)
    factsMap = buildFactSubtrees(dto.facts)
    masterRoot = buildMasterRoot(rulesMap, factsMap)
    leaves = []
    _traverseLeaves(masterRoot, leaves)
    eqs = extractAllEquations(leaves)
    return AndOrGraph(
        root=masterRoot,
        ruleNodes=rulesMap,
        factNodes=factsMap,
        equations=eqs,
        symbols=collectSymbols(eqs),
    )


# ======================================================================
# ======================================================================
# PHASE 2: BOOLEAN ABSTRACTION & TSEITIN CNF TRANSFORMATION
# ======================================================================
# ======================================================================

# ======================================================================
# SECTION 2.1: LITERAL MAPPING & CNF DATA MODELS
# ======================================================================

class LiteralMapping(BaseModel):
    literalToEquation: Dict[int, Equation] = Field(default_factory=dict)
    equationToLiteral: Dict[str, int] = Field(default_factory=dict)
    ruleToTrackingLiteral: Dict[str, int] = Field(default_factory=dict)
    trackingLiteralToRule: Dict[int, str] = Field(default_factory=dict)


class CnfFormula(BaseModel):
    clauses: List[List[int]] = Field(default_factory=list)
    numVariables: int = 0
    numClauses: int = 0
    trackingLiterals: List[int] = Field(default_factory=list)
    mapping: LiteralMapping = Field(default_factory=LiteralMapping)

    def summarize(self) -> Dict[str, Any]:
        return {
            "numVariables": self.numVariables,
            "numClauses": len(self.clauses),
            "trackingCount": len(self.trackingLiterals),
            "equationCount": len(self.mapping.literalToEquation),
        }


# ======================================================================
# SECTION 2.2: TSEITIN TRANSFORMATION ENCODERS
# ======================================================================

def buildEquationKey(eq: Equation) -> str:
    return f"{eq.symbol}:{eq.operator}:{eq.value}:{eq.isFact}"


def allocateEquationLiteral(mapping: LiteralMapping, eq: Equation, counter: List[int]) -> int:
    key = buildEquationKey(eq)
    if key in mapping.equationToLiteral:
        return mapping.equationToLiteral[key]
    counter[0] += 1
    newLit = counter[0]
    mapping.equationToLiteral[key] = newLit
    mapping.literalToEquation[newLit] = eq
    return newLit


def allocateTrackingLiteral(mapping: LiteralMapping, ruleId: str, counter: List[int]) -> int:
    counter[0] += 1
    trackingLit = counter[0]
    mapping.ruleToTrackingLiteral[ruleId] = trackingLit
    mapping.trackingLiteralToRule[trackingLit] = ruleId
    return trackingLit


def encodeAndClauses(parentVar: int, childVars: List[int]) -> List[List[int]]:
    parentImpliesChildren = [[-parentVar, c] for c in childVars]
    childrenImplyParent = [[parentVar] + [-c for c in childVars]]
    return parentImpliesChildren + childrenImplyParent


def encodeOrClauses(parentVar: int, childVars: List[int]) -> List[List[int]]:
    childrenImplyParent = [[parentVar, -c] for c in childVars]
    parentImpliesChildren = [[-parentVar] + childVars]
    return childrenImplyParent + parentImpliesChildren


def encodeNotClauses(parentVar: int, childVar: int) -> List[List[int]]:
    return [[-parentVar, -childVar], [parentVar, childVar]]


def _dispatchTseitinEncoding(nodeType: str, parentVar: int, childVars: List[int]) -> List[List[int]]:
    encoders: Dict[str, Callable[[], List[List[int]]]] = {
        NodeType.AND: lambda: encodeAndClauses(parentVar, childVars),
        NodeType.OR: lambda: encodeOrClauses(parentVar, childVars),
        NodeType.NOT: lambda: encodeNotClauses(parentVar, childVars[0]),
    }
    return encoders.get(nodeType, lambda: [])()


def tseitinTraverse(
    node: LogicNode,
    mapping: LiteralMapping,
    clauses: List[List[int]],
    counter: List[int],
) -> int:
    if node.nodeType == NodeType.EQUATION and node.equation:
        return allocateEquationLiteral(mapping, node.equation, counter)
    childVars = [tseitinTraverse(child, mapping, clauses, counter) for child in node.children]
    counter[0] += 1
    parentVar = counter[0]
    clauses.extend(_dispatchTseitinEncoding(node.nodeType, parentVar, childVars))
    return parentVar


def compileAndOrGraphToCnf(graph: AndOrGraph) -> CnfFormula:
    mapping = LiteralMapping()
    clauses: List[List[int]] = []
    counter = [0]
    trackingLits: List[int] = []
    for ruleId, ruleNode in graph.ruleNodes.items():
        ruleVar = tseitinTraverse(ruleNode, mapping, clauses, counter)
        trackLit = allocateTrackingLiteral(mapping, ruleId, counter)
        trackingLits.append(trackLit)
        clauses.append([-trackLit, ruleVar])
    for factNode in graph.factNodes.values():
        factVar = tseitinTraverse(factNode, mapping, clauses, counter)
        clauses.append([factVar])
    return CnfFormula(
        clauses=clauses,
        numVariables=counter[0],
        numClauses=len(clauses),
        trackingLiterals=trackingLits,
        mapping=mapping,
    )


# ======================================================================
# ======================================================================
# PHASE 3: BASE ENGINE & EXTENSIBLE REASONING SOLVERS
# ======================================================================
# ======================================================================

# ======================================================================
# SECTION 3.1: DECISION RESULT & BASE ENGINE HIERARCHY
# ======================================================================

class DecisionResult(BaseModel):
    status: str = Field(description="Adjudication verdict: ACCEPTED, REJECTED, or UNKNOWN")
    certifiedModel: Dict[str, Any] = Field(default_factory=dict, description="Satisfying model assignment if feasible")
    unsatCore: List[str] = Field(default_factory=list, description="Violated rule IDs or descriptions on conflict")
    details: Dict[str, Any] = Field(default_factory=dict, description="Solver diagnostic metrics and lemma statistics")


class BaseEngine:
    def __init__(self, engineName: str = "BaseEngine") -> None:
        self.engineName: str = engineName
        self.status: str = "INITIALIZED"

    def solve(self, payload: Any) -> Any:
        raise NotImplementedError

    def explainConflict(self) -> List[Any]:
        return []

    def resetEngine(self) -> None:
        self.status = "INITIALIZED"


# ======================================================================
# SECTION 3.2: PROPOSITIONAL CDCL SAT SOLVER (DPLL ENGINE)
# ======================================================================

def initWatchedLiterals(clauses: List[List[int]], numVars: int) -> Dict[int, List[int]]:
    watches: Dict[int, List[int]] = {lit: [] for var in range(1, numVars + 1) for lit in (var, -var)}
    for idx, clause in enumerate(clauses):
        targets = clause[:2] if len(clause) >= 2 else clause[:1]
        for lit in targets:
            watches[lit].append(idx)
    return watches


def assignLiteral(
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


def isLiteralSatisfied(lit: int, assignments: np.ndarray) -> bool:
    val = assignments[abs(lit)]
    return bool(val == 1 if lit > 0 else val == 0)


def isLiteralFalsified(lit: int, assignments: np.ndarray) -> bool:
    val = assignments[abs(lit)]
    return bool(val == 0 if lit > 0 else val == 1)


def findAlternativeWatch(
    clause: List[int],
    falsifiedLit: int,
    otherWatch: int,
    assignments: np.ndarray,
) -> Optional[int]:
    for lit in clause:
        if lit != otherWatch and not isLiteralFalsified(lit, assignments):
            return lit
    return None


def propagateTwoWatchedLiterals(
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
        if isLiteralSatisfied(otherWatch, assignments):
            continue
        altLit = findAlternativeWatch(clause, falsifiedLit, otherWatch, assignments)
        if altLit:
            watches[falsifiedLit].remove(cIdx)
            watches[altLit].append(cIdx)
            continue
        if assignments[abs(otherWatch)] == -1:
            assignLiteral(otherWatch, currentLevel, cIdx, assignments, trailLevels, antecedents, trail)
        elif isLiteralFalsified(otherWatch, assignments):
            return cIdx
    return None


def analyzeConflict1UIP(
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


def backjumpToLevel(
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


def pickBranchingLiteral(assignments: np.ndarray, activityScores: np.ndarray) -> Optional[int]:
    unassigned = np.where(assignments[1:] == -1)[0] + 1
    if len(unassigned) == 0:
        return None
    scores = activityScores[unassigned]
    bestVar = int(unassigned[np.argmax(scores)])
    return bestVar


class DpllEngine(BaseEngine):
    def __init__(self) -> None:
        super().__init__(engineName="DpllEngine")
        self.learnedClauses: List[List[int]] = []

    def solveSat(self, cnf: CnfFormula, assumptions: Optional[List[int]] = None) -> Dict[str, Any]:
        numVars = cnf.numVariables
        clauses = [list(c) for c in cnf.clauses]
        assignments = np.full(numVars + 1, -1, dtype=np.int8)
        trailLevels = np.full(numVars + 1, -1, dtype=np.int32)
        antecedents = np.full(numVars + 1, -1, dtype=np.int32)
        activityScores = np.ones(numVars + 1, dtype=np.float64)
        trail: List[int] = []
        watches = initWatchedLiterals(clauses, numVars)
        currentLevel = 0
        for unitClause in [c for c in clauses if len(c) == 1]:
            assignLiteral(unitClause[0], 0, -1, assignments, trailLevels, antecedents, trail)
        activeAssumptions = list(assumptions or [])
        for aLit in activeAssumptions:
            currentLevel += 1
            assignLiteral(aLit, currentLevel, -1, assignments, trailLevels, antecedents, trail)
            conflictIdx = propagateTwoWatchedLiterals(
                -aLit, clauses, assignments, watches, trailLevels, antecedents, trail, currentLevel
            )
            if conflictIdx is not None:
                self.status = "UNSATISFIABLE"
                return {"status": "UNSATISFIABLE", "assignments": {}, "conflict": [aLit]}
        while True:
            branchLit = pickBranchingLiteral(assignments, activityScores)
            if branchLit is None:
                self.status = "SATISFIABLE"
                resModel = {v: bool(assignments[v] == 1) for v in range(1, numVars + 1)}
                return {"status": "SATISFIABLE", "assignments": resModel, "conflict": []}
            currentLevel += 1
            assignLiteral(branchLit, currentLevel, -1, assignments, trailLevels, antecedents, trail)
            conflictIdx = propagateTwoWatchedLiterals(
                -branchLit, clauses, assignments, watches, trailLevels, antecedents, trail, currentLevel
            )
            while conflictIdx is not None:
                if currentLevel == 0:
                    self.status = "UNSATISFIABLE"
                    return {"status": "UNSATISFIABLE", "assignments": {}, "conflict": []}
                learnedClause, backjumpLevel = analyzeConflict1UIP(
                    conflictIdx, clauses, trail, trailLevels, antecedents, currentLevel
                )
                clauses.append(learnedClause)
                self.learnedClauses.append(learnedClause)
                backjumpToLevel(backjumpLevel, trail, assignments, trailLevels, antecedents)
                currentLevel = backjumpLevel
                if len(learnedClause) > 0:
                    assignLiteral(learnedClause[0], currentLevel, len(clauses) - 1, assignments, trailLevels, antecedents, trail)
                conflictIdx = None

    def solve(self, payload: Any) -> Any:
        return self.solveSat(payload)


# ======================================================================
# SECTION 3.3: LINEAR REAL ARITHMETIC THEORY SOLVER (SMT ENGINE)
# ======================================================================

def buildSymbolIndex(equations: List[Equation]) -> Dict[str, int]:
    uniqueSymbols = sorted(list({eq.symbol for eq in equations}))
    return {sym: idx for idx, sym in enumerate(uniqueSymbols)}


def buildSimplexTableau(
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
        _assignEquationBounds(eq.operator, val, rowIdx, lowerBounds, upperBounds)
        if eq.isFact:
            colValues[colIdx] = val
            colFrozen[colIdx] = True
    rowValues = tableau @ colValues
    return tableau, lowerBounds, upperBounds, rowValues, colFrozen


def _assignEquationBounds(
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


def findViolatedBasicRow(
    values: np.ndarray,
    lowerBounds: np.ndarray,
    upperBounds: np.ndarray,
) -> Optional[int]:
    violations = np.where((values < lowerBounds) | (values > upperBounds))[0]
    return int(violations[0]) if len(violations) > 0 else None


def findEligiblePivotCol(
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


def pivotSimplexTableau(
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


class SmtEngine(BaseEngine):
    def __init__(self) -> None:
        super().__init__(engineName="SmtEngine")
        self.conflictLemmas: List[List[Equation]] = []

    def solveTheory(self, activeEquations: List[Equation]) -> Dict[str, Any]:
        if not activeEquations:
            self.status = "FEASIBLE"
            return {"status": "FEASIBLE", "conflicts": []}
        symbolMap = buildSymbolIndex(activeEquations)
        tableau, lowerBounds, upperBounds, rowValues, colFrozen = buildSimplexTableau(activeEquations, symbolMap)
        maxPivots = 500
        for _ in range(maxPivots):
            violatedRow = findViolatedBasicRow(rowValues, lowerBounds, upperBounds)
            if violatedRow is None:
                self.status = "FEASIBLE"
                return {"status": "FEASIBLE", "conflicts": []}
            pivotCol = findEligiblePivotCol(violatedRow, tableau, rowValues, lowerBounds, upperBounds, colFrozen)
            if pivotCol is None:
                self.status = "INFEASIBLE"
                allViolations = [
                    activeEquations[r]
                    for r in range(len(activeEquations))
                    if (rowValues[r] < lowerBounds[r] or rowValues[r] > upperBounds[r])
                    and findEligiblePivotCol(r, tableau, rowValues, lowerBounds, upperBounds, colFrozen) is None
                ]
                conflict = allViolations if allViolations else [activeEquations[violatedRow]]
                self.conflictLemmas.append(conflict)
                return {"status": "INFEASIBLE", "conflicts": conflict}
            pivotSimplexTableau(tableau, rowValues, violatedRow, pivotCol)
        self.status = "INFEASIBLE"
        return {"status": "INFEASIBLE", "conflicts": activeEquations}

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
    ) -> None:
        self.satSolver: DpllEngine = satSolver or DpllEngine()
        self.theorySolvers: List[BaseEngine] = theorySolvers or [SmtEngine()]

    def solvePolicy(
        self,
        payload: Union[str, Dict[str, Any], ParsedOutputDTO, AndOrGraph],
    ) -> DecisionResult:
        graph = payload if isinstance(payload, AndOrGraph) else assembleAndOrGraph(payload)
        cnf = compileAndOrGraphToCnf(graph)
        satResult = self.satSolver.solveSat(cnf, assumptions=cnf.trackingLiterals)
        smtSolver = next((s for s in self.theorySolvers if isinstance(s, SmtEngine)), SmtEngine())
        activeEquations = [
            eq for lit, eq in cnf.mapping.literalToEquation.items()
            if satResult.get("assignments", {}).get(lit, False)
        ] + [eq for eq in graph.equations if eq.isFact]
        theoryResult = smtSolver.solveTheory(activeEquations)
        isAccepted = satResult["status"] == "SATISFIABLE" and theoryResult["status"] == "FEASIBLE"
        status = "ACCEPTED" if isAccepted else "REJECTED"
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
