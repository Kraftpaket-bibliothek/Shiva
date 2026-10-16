from __future__ import annotations

import json
from typing import Any, Callable, Dict, List, Optional, Set, Union
from pydantic import BaseModel, Field
from src.textProcessor import ParsedFactDTO, ParsedOutputDTO, ParsedRuleDTO


# ======================================================================
# GRAPH AND EQUATION DATA STRUCTURES
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
# EQUATION FACTORIES AND BUILDERS
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
# AND-OR BRANCH DISPATCHERS
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
# AND-OR GRAPH PIPELINE COORDINATOR
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
