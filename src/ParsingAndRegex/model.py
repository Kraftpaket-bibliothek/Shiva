from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, List, Optional, Set, Union
import spacy
from spacy.language import Language
from spacy.tokens import Doc, Span, Token

logger = logging.getLogger("Yukti.Perception.Model")

cachedPipelines: dict[str, Language] = {}


def readConfig(configPath: Optional[Union[str, Path]] = None) -> dict[str, Any]:

    targetPath: Optional[Path] = None
    if configPath:
        p = Path(configPath)
        if p.is_file():
            targetPath = p

    if not targetPath:
        searchPaths = [
            Path(".config"),
            Path(__file__).resolve().parents[2] / ".config",
            Path(__file__).resolve().parents[1] / ".config",
        ]
        for candidate in searchPaths:
            if candidate.exists() and candidate.is_file():
                targetPath = candidate.resolve()
                break

    if not targetPath:
        logger.warning("No .config file found; applying default settings.")
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

    rawProps: dict[str, str] = {}
    with open(targetPath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or line.startswith(";") or line.startswith("["):
                continue
            if "=" in line:
                key, val = line.split("=", 1)
                rawProps[key.strip().lower()] = val.strip()

    # Parse aliases
    aliases: dict[str, str] = {}
    rawAliases = rawProps.get("model_aliases", "")
    for pair in rawAliases.split(","):
        if ":" in pair:
            src, dst = pair.split(":", 1)
            aliases[src.strip().lower()] = dst.strip()

    # Resolve active model name
    rawModel = rawProps.get("model_name", "en_core_web_lg").strip()
    resolvedModel = aliases.get(rawModel.lower(), rawModel)

    # Parse disabled pipes
    rawPipes = rawProps.get("disabled_pipes", "ner, textcat")
    disabledPipes = [p.strip() for p in rawPipes.split(",") if p.strip()]

    # Parse dependency pruning sets
    rawRelevant = rawProps.get("relevant_dep_labels", "")
    relevantDeps = {d.strip() for d in rawRelevant.split(",") if d.strip()}

    rawUnused = rawProps.get("unused_dep_labels", "")
    unusedDeps = {d.strip() for d in rawUnused.split(",") if d.strip()}

    return {
        "modelName": resolvedModel,
        "modelAliases": aliases,
        "disabledPipes": disabledPipes,
        "autoDownload": rawProps.get("auto_download", "true").lower() in ("true", "1", "yes"),
        "removeUnusedDependencies": rawProps.get("remove_unused_dependencies", "true").lower() in ("true", "1", "yes"),
        "relevantDepLabels": relevantDeps,
        "unusedDepLabels": unusedDeps,
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
        config: Optional[dict[str, Any]] = None,
    ) -> Language:
        activeConfig = config or readConfig()
        targetModel = modelName or activeConfig["modelName"]
        targetModel = activeConfig["modelAliases"].get(targetModel.lower(), targetModel)
        disabledPipes = activeConfig["disabledPipes"]

        cacheKey = f"{targetModel}__disabled={','.join(sorted(disabledPipes))}"
        if cacheKey in cachedPipelines:
            return cachedPipelines[cacheKey]

        try:
            pipeline = spacy.load(targetModel, disable=disabledPipes)
            logger.info(f"Loaded '{targetModel}' (disabled components: {disabledPipes})")
        except OSError:
            if activeConfig["autoDownload"]:
                downloadModel(targetModel)
                pipeline = spacy.load(targetModel, disable=disabledPipes)
            else:
                raise FileNotFoundError(
                    f"spaCy model '{targetModel}' is not installed. "
                    f"Run 'python -m spacy download {targetModel}' or set Auto_Download = True in .config."
                )

        cachedPipelines[cacheKey] = pipeline
        return pipeline

    @staticmethod
    def _warmup(
        pipeline: Language,
        config: Optional[dict[str, Any]] = None,
    ) -> Doc:
        """
        Internal Method 2: Runs an initial inference pass to pre-heat memory and weights.
        """
        activeConfig = config or readConfig()
        warmupText = activeConfig["warmupText"]
        doc = pipeline(warmupText)
        logger.debug(f"Model warmup pass completed for: '{warmupText}'")
        return doc

    @staticmethod
    def _pruneDependencies(
        docOrSpan: Union[Doc, Span],
        config: Optional[dict[str, Any]] = None,
    ) -> List[Token]:
        activeConfig = config or readConfig()
        relevantDeps: Set[str] = activeConfig["relevantDepLabels"]
        unusedDeps: Set[str] = activeConfig["unusedDepLabels"]

        prunedTokens: List[Token] = [
            token for token in docOrSpan
            if (not relevantDeps or token.dep_ in relevantDeps)
            and token.dep_ not in unusedDeps
        ]
        return prunedTokens
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
        logger.info(f"Model '{config['modelName']}' is resident in memory and ready for inference.")
        return pipeline

loadModelToMemory = Model.loadModelToMemory
