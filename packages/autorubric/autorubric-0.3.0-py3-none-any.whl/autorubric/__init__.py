from pathlib import Path

from autorubric.dataset import DataItem, RubricDataset
from autorubric.llm import (
    GenerateResult,
    LLMClient,
    LLMConfig,
    ThinkingConfig,
    ThinkingLevel,
    ThinkingLevelLiteral,
    ThinkingParam,
    generate,
)
from autorubric.rubric import Rubric
from autorubric.types import (
    AggregationStrategy,
    AggregatedMultiChoiceVerdict,
    CannotAssessConfig,
    CannotAssessStrategy,
    CountFn,
    Criterion,
    CriterionJudgment,
    CriterionOption,
    CriterionReport,
    CriterionVerdict,
    EnsembleCriterionReport,
    EnsembleEvaluationReport,
    EvaluationReport,
    FewShotConfig,
    FewShotExample,
    JudgeVote,
    LengthPenalty,
    MultiChoiceJudgment,
    MultiChoiceJudgeVote,
    MultiChoiceVerdict,
    NominalAggregation,
    OrdinalAggregation,
    PenaltyType,
    ScaleType,
    ThinkingOutputDict,
    ToGradeInput,
    TokenUsage,
)
from autorubric.utils import (
    aggregate_completion_cost,
    aggregate_evaluation_usage,
    aggregate_token_usage,
    compute_length_penalty,
    fill_ground_truth,
    normalize_to_grade_input,
    parse_thinking_output,
    word_count,
)
from autorubric.eval import (
    EvalConfig,
    EvalResult,
    EvalRunner,
    EvalTimingStats,
    ExperimentManifest,
    ItemResult,
    evaluate,
)
from autorubric.metrics import (
    # Main interface
    compute_metrics,
    # Result types
    BiasResult,
    BootstrapResult,
    BootstrapResults,
    CannotAssessMode,
    ConfidenceInterval,
    CorrelationResult,
    CriterionMetrics,
    DistributionResult,
    EMDResult,
    JudgeMetrics,
    KSTestResult,
    MetricsResult,
    # Distribution metrics (unique to autorubric)
    earth_movers_distance,
    wasserstein_distance,
    ks_test,
    score_distribution,
    systematic_bias,
    # Helpers
    extract_verdicts_from_report,
    filter_cannot_assess,
    verdict_to_binary,
    verdict_to_string,
)

# Read version from VERSION file at project root
_version_file = Path(__file__).parent.parent.parent / "VERSION"
__version__ = _version_file.read_text().strip() if _version_file.exists() else "0.0.0"
__all__ = [
    # Dataset classes
    "DataItem",
    "RubricDataset",
    # LLM Infrastructure
    "GenerateResult",
    "LLMClient",
    "LLMConfig",
    "ThinkingConfig",
    "ThinkingLevel",
    "ThinkingLevelLiteral",
    "ThinkingParam",
    "generate",
    # Core types
    "AggregationStrategy",
    "CannotAssessConfig",
    "CannotAssessStrategy",
    "CountFn",
    "Criterion",
    "CriterionJudgment",
    "CriterionOption",
    "CriterionReport",
    "CriterionVerdict",
    "EvaluationReport",
    "LengthPenalty",
    "PenaltyType",
    "Rubric",
    "ScaleType",
    "ThinkingOutputDict",
    "ToGradeInput",
    "TokenUsage",
    # Multi-choice types
    "AggregatedMultiChoiceVerdict",
    "MultiChoiceJudgment",
    "MultiChoiceJudgeVote",
    "MultiChoiceVerdict",
    "NominalAggregation",
    "OrdinalAggregation",
    # Few-shot types
    "FewShotConfig",
    "FewShotExample",
    # Ensemble types
    "EnsembleCriterionReport",
    "EnsembleEvaluationReport",
    "JudgeVote",
    # Utility functions
    "aggregate_completion_cost",
    "aggregate_evaluation_usage",
    "aggregate_token_usage",
    "compute_length_penalty",
    "fill_ground_truth",
    "normalize_to_grade_input",
    "parse_thinking_output",
    "word_count",
    # Evaluation runner
    "EvalConfig",
    "EvalResult",
    "EvalRunner",
    "EvalTimingStats",
    "ExperimentManifest",
    "ItemResult",
    "evaluate",
    # Metrics - main interface
    "compute_metrics",
    "MetricsResult",
    # Metrics result types
    "BiasResult",
    "BootstrapResult",
    "BootstrapResults",
    "CannotAssessMode",
    "ConfidenceInterval",
    "CorrelationResult",
    "CriterionMetrics",
    "DistributionResult",
    "EMDResult",
    "JudgeMetrics",
    "KSTestResult",
    # Distribution metrics (unique to autorubric)
    "earth_movers_distance",
    "wasserstein_distance",
    "ks_test",
    "score_distribution",
    "systematic_bias",
    # Helpers
    "extract_verdicts_from_report",
    "filter_cannot_assess",
    "verdict_to_binary",
    "verdict_to_string",
]
__name__ = "autorubric"
__author__ = "Delip Rao"
