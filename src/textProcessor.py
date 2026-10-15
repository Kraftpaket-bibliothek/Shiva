from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
from pydantic import BaseModel, Field
import spacy
from spacy.language import Language
from spacy.tokens import Doc, Span, Token

logger = logging.getLogger("Yukti.Perception.TextProcessor")


# ======================================================================
# Model & Configuration Manager
# ======================================================================

cachedPipelines: Dict[str, Language] = {}


def readConfig(configPath: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
    targetPath: Optional[Path] = None
    if configPath:
        p = Path(configPath)
        targetPath = p if p.is_file() else None

    if not targetPath:
        searchPaths = [
            Path(".config"),
            Path(__file__).resolve().parents[2] / ".config",
            Path(__file__).resolve().parents[1] / ".config",
        ]
        targetPath = next((p.resolve() for p in searchPaths if p.exists() and p.is_file()), None)

    if not targetPath:
        return {
            "modelName": "en_core_web_lg",
            "modelAliases": {"en_core_web_large": "en_core_web_lg"},
            "disabledPipes": ["ner", "textcat"],
            "autoDownload": True,
            "removeUnusedDependencies": True,
            "relevantDepLabels": {"nsubj", "compound", "amod", "ROOT"},
            "unusedDepLabels": {"det", "punct", "aux"},
            "warmupText": "Model warmup check.",
        }

    rawProps: Dict[str, str] = {}
    with open(targetPath, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            parts = stripped.split("=", 1) if "=" in stripped and not stripped.startswith(("#", ";", "[")) else None
            rawProps.update({parts[0].strip().lower(): parts[1].strip()} if parts else {})

    aliases: Dict[str, str] = {
        src.strip().lower(): dst.strip()
        for pair in rawProps.get("model_aliases", "").split(",")
        if ":" in pair
        for src, dst in [pair.split(":", 1)]
    }

    rawModel = rawProps.get("model_name", "en_core_web_lg").strip()
    return {
        "modelName": aliases.get(rawModel.lower(), rawModel),
        "modelAliases": aliases,
        "disabledPipes": [p.strip() for p in rawProps.get("disabled_pipes", "ner, textcat").split(",") if p.strip()],
        "autoDownload": rawProps.get("auto_download", "true").lower() in ("true", "1", "yes"),
        "removeUnusedDependencies": rawProps.get("remove_unused_dependencies", "true").lower() in ("true", "1", "yes"),
        "relevantDepLabels": {d.strip() for d in rawProps.get("relevant_dep_labels", "").split(",") if d.strip()},
        "unusedDepLabels": {d.strip() for d in rawProps.get("unused_dep_labels", "").split(",") if d.strip()},
        "warmupText": rawProps.get("warmup_text", "Model warmup check."),
    }


def downloadModel(modelName: str) -> None:
    logger.info(f"Downloading spaCy model '{modelName}'...")
    spacy.cli.download(modelName) # type: ignore
    logger.info(f"Successfully downloaded '{modelName}'.")


class Model:

    @staticmethod
    def _loadModel(
        modelName: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> Language:
        activeConfig = config or readConfig()
        targetModel = modelName or activeConfig["modelName"]
        targetModel = activeConfig["modelAliases"].get(targetModel.lower(), targetModel)
        disabledPipes = activeConfig["disabledPipes"]

        cacheKey = f"{targetModel}__disabled={','.join(sorted(disabledPipes))}"
        cached = cachedPipelines.get(cacheKey)
        if cached:
            return cached

        try:
            pipeline = spacy.load(targetModel, disable=disabledPipes)
        except OSError:
            downloadModel(targetModel)
            pipeline = spacy.load(targetModel, disable=disabledPipes)

        cachedPipelines[cacheKey] = pipeline
        return pipeline

    @staticmethod
    def _warmup(
        pipeline: Language,
        config: Optional[Dict[str, Any]] = None,
    ) -> Doc:
        activeConfig = config or readConfig()
        return pipeline(activeConfig["warmupText"])

    @staticmethod
    def _pruneDependencies(
        docOrSpan: Union[Doc, Span],
        config: Optional[Dict[str, Any]] = None,
    ) -> List[Token]:
        activeConfig = config or readConfig()
        relevantDeps: Set[str] = activeConfig["relevantDepLabels"]
        unusedDeps: Set[str] = activeConfig["unusedDepLabels"]
        return [
            token for token in docOrSpan
            if (not relevantDeps or token.dep_ in relevantDeps) and token.dep_ not in unusedDeps
        ]

    loadModel = _loadModel
    warmup = _warmup
    pruneDependencies = _pruneDependencies

    @staticmethod
    def loadModelToMemory(
        modelName: Optional[str] = None,
        configPath: Optional[Union[str, Path]] = None,
    ) -> Language:
        config = readConfig(configPath)
        pipeline = Model._loadModel(modelName=modelName, config=config)
        warmupDoc = Model._warmup(pipeline=pipeline, config=config)
        Model._pruneDependencies(docOrSpan=warmupDoc, config=config)
        return pipeline


loadModelToMemory = Model.loadModelToMemory


# ======================================================================
# Pydantic Data Transfer Objects (DTOs)
# ======================================================================

class DataInput(BaseModel):
    Rules: List[str] = Field(default_factory=list, description="Collection of policy rule constraint strings")
    Facts: List[str] = Field(default_factory=list, description="Collection of case fact strings")
    RequiredOutcome: List[str] = Field(default_factory=list, description="Collection of target outcome strings")


class ParsedRuleDTO(BaseModel):
    ruleId: str = Field(description="Unique rule identifier e.g. Rule_1")
    symbol: str = Field(description="Normalized variable name e.g. credit_score")
    operator: str = Field(description="Normalized mathematical comparison operator e.g. >=, <, ==")
    threshold: Union[float, int, str, bool] = Field(description="Normalized scalar or boolean threshold")
    conditionSymbol: Optional[str] = Field(default=None, description="Antecedent variable name if rule is conditional")
    conditionOperator: Optional[str] = Field(default=None, description="Antecedent operator e.g. ==")
    conditionValue: Optional[Union[float, int, str, bool]] = Field(default=None, description="Antecedent value e.g. True")
    rawText: str = Field(default="", description="Original natural language rule text")


class ParsedFactDTO(BaseModel):
    factId: str = Field(description="Unique fact identifier e.g. Fact_1")
    symbol: str = Field(description="Normalized variable name e.g. credit_score")
    value: Union[float, int, str, bool] = Field(description="Observed fact value")
    rawText: str = Field(default="", description="Original natural language fact text")


class ParsedOutputDTO(BaseModel):
    rules: List[ParsedRuleDTO] = Field(default_factory=list, description="List of parsed rule DTOs")
    facts: List[ParsedFactDTO] = Field(default_factory=list, description="List of parsed fact DTOs")
    requiredOutcome: str = Field(default="ALL_RULES", description="Target outcome query or goal")
    parsingStatus: str = Field(default="SUCCESS", description="Perception pipeline status")

    def toJson(self) -> str:
        return self.model_dump_json(indent=2)


def createJsonOutput(
    rules: List[ParsedRuleDTO],
    facts: List[ParsedFactDTO],
    requiredOutcome: str = "ALL_RULES",
    parsingStatus: str = "SUCCESS",
) -> str:
    outputDto = ParsedOutputDTO(
        rules=rules,
        facts=facts,
        requiredOutcome=requiredOutcome,
        parsingStatus=parsingStatus,
    )
    return outputDto.toJson()


# ======================================================================
# Declarative Lookup Tables & Pre-Compiled Patterns
# ======================================================================

BOOLEAN_MAP: Dict[str, bool] = {
    "true": True, "yes": True, "1": True, "active": True,
    "false": False, "no": False, "0": False, "inactive": False,
}

OPERATOR_MAP: Dict[str, str] = {
    ">=": ">=", "at least": ">=", "needs to be at least": ">=", "must be at least": ">=", "minimum of": ">=",
    "<=": "<=", "at most": "<=", "no more than": "<=", "maximum of": "<=",
    ">": ">", "exceeds": ">", "exceed": ">", "must exceed": ">", "strictly greater than": ">",
    "<": "<", "under": "<", "should stay under": "<", "must stay under": "<", "must be under": "<", "strictly less than": "<",
    "==": "==", "is equal to": "==", "must be equal to": "==", "equals": "==", "is": "==", ":": "==", "=": "==",
    "!=": "!=", "is not": "!=", "not equal to": "!=",
}

OPERATOR_REGEX: str = "|".join(re.escape(k) for k in sorted(OPERATOR_MAP.keys(), key=len, reverse=True))

CLAUSE_PATTERN = re.compile(
    rf"^(?P<subject>.*?)\s*(?P<op>{OPERATOR_REGEX})\s*(?P<val>\d+(?:\.\d+)?%?|\w+)?\s*$",
    re.IGNORECASE,
)

FACT_PATTERN = re.compile(
    r"^(?P<symbol>[^:=]+?)\s*(?:[:=]|\bis\b)\s*(?P<val>.+)$",
    re.IGNORECASE,
)

CONDITION_PATTERN = re.compile(r"\b(?:when|if|unless)\b", re.IGNORECASE)

UNUSED_DEP_TAGS: Set[str] = {"det", "punct", "aux", "auxpass", "expl", "intj", "meta"}


# ======================================================================
# Value Parsers & Normalizers
# ======================================================================

def formatSymbol(text: str) -> str:
    cleaned = re.sub(r"[^\w\s]", " ", text).strip().lower()
    return re.sub(r"\s+", "_", cleaned)


def parseBoolean(text: str) -> Optional[bool]:
    return BOOLEAN_MAP.get(text.strip().lower())


def parseNumeric(text: str) -> Union[float, int, str]:
    cleaned = text.strip()
    scale = 0.01 if cleaned.endswith("%") else 1.0
    digits = cleaned.rstrip("%").strip()
    try:
        return float(digits) * scale
    except ValueError:
        return cleaned


def parseValue(text: str) -> Union[float, int, str, bool]:
    boolVal = parseBoolean(text)
    return boolVal if boolVal is not None else parseNumeric(text)


# ======================================================================
# Linguistic Extraction Helpers
# ======================================================================

def pruneDependencies(docOrSpan: Union[Doc, Span]) -> List[Token]:
    return [token for token in docOrSpan if token.dep_ not in UNUSED_DEP_TAGS]


def extractSubject(doc: Doc) -> str:
    chunks = list(doc.noun_chunks)
    candidate = chunks[0].text if chunks else " ".join(
        t.text for t in pruneDependencies(doc) if t.dep_ in ("nsubj", "nsubjpass", "compound", "amod", "attr")
    )
    return formatSymbol(candidate or doc.text)


def parseClause(clauseText: str, nlp: Language) -> Tuple[str, str, Union[float, int, str, bool]]:
    match = CLAUSE_PATTERN.search(clauseText.strip())
    data = match.groupdict() if match else {"subject": clauseText, "op": ">=", "val": "0.0"}
    rawSubject = data.get("subject") or clauseText
    rawOp = data.get("op") or ">="
    rawVal = data.get("val") or "0.0"
    return extractSubject(nlp(rawSubject)), OPERATOR_MAP.get(rawOp.lower().strip(), ">="), parseValue(rawVal)


# ======================================================================
# Clause & Record Builders
# ======================================================================

def splitCondition(ruleText: str) -> Tuple[str, str]:
    parts = CONDITION_PATTERN.split(ruleText, maxsplit=1)
    mainPart = parts[0].strip()
    condPart = parts[1].strip() if len(parts) > 1 else ""
    return mainPart, condPart


def buildRuleRecord(ruleText: str, index: int, nlp: Language) -> Dict[str, Any]:
    mainText, condText = splitCondition(ruleText)
    mainSym, mainOp, mainThresh = parseClause(mainText, nlp)
    condSym, condOp, condVal = parseClause(condText, nlp) if condText else (None, None, None)
    return {
        "ruleId": f"Rule_{index}",
        "symbol": mainSym,
        "operator": mainOp,
        "threshold": mainThresh,
        "conditionSymbol": condSym,
        "conditionOperator": condOp,
        "conditionValue": condVal,
        "rawText": ruleText,
    }


def buildFactRecord(factText: str, index: int) -> Dict[str, Any]:
    match = FACT_PATTERN.search(factText)
    data = match.groupdict() if match else {"symbol": factText, "val": "true"}
    return {
        "factId": f"Fact_{index}",
        "symbol": formatSymbol(data["symbol"]),
        "value": parseValue(data["val"]),
        "rawText": factText,
    }


# ======================================================================
# Pipeline Harness Class
# ======================================================================

class TextProcess:
    def __init__(self, model: Optional[Language] = None) -> None:
        self.model: Language = model or loadModelToMemory()
        self.steps: List[Callable[[Dict[str, Any]], Dict[str, Any]]] = []

    def addStep(
        self,
        step: Union[Callable[[Dict[str, Any]], Dict[str, Any]], List[Callable[[Dict[str, Any]], Dict[str, Any]]]],
    ) -> TextProcess:
        items = step if isinstance(step, list) else [step]
        self.steps.extend(items)
        return self

    def clearSteps(self) -> None:
        self.steps.clear()

    def listSteps(self) -> List[str]:
        return [fn.__name__ for fn in self.steps]

    def executePipeline(self, inputData: Any) -> str:
        context: Dict[str, Any] = {
            "model": self.model,
            "rawInput": inputData,
            "rawRules": [],
            "rawFacts": [],
            "requiredOutcome": "ALL_RULES",
            "extractedRules": [],
            "extractedFacts": [],
            "outputDto": None,
            "jsonOutput": "",
        }
        for step in self.steps:
            context = step(context)
        return context["jsonOutput"]


# ======================================================================
# Standalone Pipeline Recipe Steps
# ======================================================================

PAYLOAD_PARSERS: Dict[type, Callable[[Any], Tuple[List[str], List[str], str]]] = {
    DataInput: lambda d: (list(d.Rules), list(d.Facts), d.RequiredOutcome[0] if d.RequiredOutcome else "ALL_RULES"),
    dict: lambda d: (list(d.get("Rules", [])), list(d.get("Facts", [])), d.get("RequiredOutcome", ["ALL_RULES"])[0] if isinstance(d.get("RequiredOutcome"), list) else str(d.get("RequiredOutcome", "ALL_RULES"))),
    str: lambda s: ([line.strip() for line in s.splitlines() if line.strip()], [], "ALL_RULES"),
}


def parsePayload(context: Dict[str, Any]) -> Dict[str, Any]:
    parser = PAYLOAD_PARSERS.get(type(context["rawInput"]), lambda _: ([], [], "ALL_RULES"))
    rules, facts, outcome = parser(context["rawInput"])
    context["rawRules"] = rules
    context["rawFacts"] = facts
    context["requiredOutcome"] = outcome
    return context


def extractRules(context: Dict[str, Any]) -> Dict[str, Any]:
    nlp: Language = context["model"]
    context["extractedRules"] = [buildRuleRecord(r, i, nlp) for i, r in enumerate(context["rawRules"], 1)]
    return context


def extractFacts(context: Dict[str, Any]) -> Dict[str, Any]:
    context["extractedFacts"] = [buildFactRecord(f, i) for i, f in enumerate(context["rawFacts"], 1)]
    return context


def assembleDto(context: Dict[str, Any]) -> Dict[str, Any]:
    ruleDtos = [ParsedRuleDTO(**r) for r in context["extractedRules"]]
    factDtos = [ParsedFactDTO(**f) for f in context["extractedFacts"]]
    context["outputDto"] = ParsedOutputDTO(
        rules=ruleDtos,
        facts=factDtos,
        requiredOutcome=context["requiredOutcome"],
        parsingStatus="SUCCESS",
    )
    return context


def exportJson(context: Dict[str, Any]) -> Dict[str, Any]:
    outputDto = context.get("outputDto") or ParsedOutputDTO(
        rules=[],
        facts=[],
        requiredOutcome=context.get("requiredOutcome", "ALL_RULES"),
        parsingStatus="EMPTY",
    )
    context["jsonOutput"] = outputDto.toJson()
    return context


# ======================================================================
# Default Recipe Assembler
# ======================================================================

def buildDefaultRecipe(processor: Optional[TextProcess] = None) -> TextProcess:
    proc = processor or TextProcess()
    proc.addStep([
        parsePayload,
        extractRules,
        extractFacts,
        assembleDto,
        exportJson,
    ])
    return proc
