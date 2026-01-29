"""Astrolabe - LLM 数据处理 Pipeline SDK"""

__version__ = "0.1.0"

# Schema - 数据模型
from .schema import (
    InteractionType,
    Role,
    DataSource,
    Interaction,
    Sample,
    Dataset,
    FilterCondition,
    SamplingConfig,
    SelectionSpec,
    create_sample_from_messages,
)

# Operator - 算子
from .operator import (
    Op,
    Read,
    Map,
    Filter,
    Write,
    Select,
    Join,
    ConvertFormat,
    FilterBySpec,
)

# Pipeline
from .pipeline import (
    Pipeline,
    PipelineBuilder,
    Runner,
    RunResult,
    RunStatus,
    LocalRunner,
    SparkRunner,
    RayRunner,
)

__all__ = [
    "__version__",
    # Schema
    "InteractionType",
    "Role",
    "DataSource",
    "Interaction",
    "Sample",
    "Dataset",
    "FilterCondition",
    "SamplingConfig",
    "SelectionSpec",
    "create_sample_from_messages",
    # Operator
    "Op",
    "Read",
    "Map",
    "Filter",
    "Write",
    "Select",
    "Join",
    "ConvertFormat",
    "FilterBySpec",
    # Pipeline
    "Pipeline",
    "PipelineBuilder",
    "Runner",
    "RunResult",
    "RunStatus",
    "LocalRunner",
    "SparkRunner",
    "RayRunner",
]
