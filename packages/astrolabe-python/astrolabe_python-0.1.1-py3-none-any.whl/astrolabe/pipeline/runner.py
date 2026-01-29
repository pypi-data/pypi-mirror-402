"""Runner - 执行引擎基类与本地执行器"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .core import Pipeline


class RunStatus(Enum):
    """执行状态"""
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RUNNING = "running"


@dataclass
class RunResult:
    """执行结果"""
    status: RunStatus
    metrics: Dict[str, Any] = field(default_factory=dict)
    output: Optional[List[Any]] = None
    error: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    @property
    def success(self) -> bool:
        return self.status == RunStatus.SUCCESS

    @property
    def duration_seconds(self) -> Optional[float]:
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status.value,
            "metrics": self.metrics,
            "error": self.error,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": self.duration_seconds,
        }

    def __repr__(self) -> str:
        if self.success:
            metrics_str = ", ".join(f"{k}={v}" for k, v in self.metrics.items())
            return f"RunResult(SUCCESS, {metrics_str})"
        else:
            return f"RunResult({self.status.value}, error={self.error!r})"


class Runner(ABC):
    """执行引擎抽象基类"""

    @abstractmethod
    def run(self, pipeline: "Pipeline") -> RunResult:
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        pass


class LocalRunner(Runner):
    """本地执行器"""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose

    @property
    def name(self) -> str:
        return "LocalRunner"

    def run(self, pipeline: "Pipeline") -> RunResult:
        from ..operator import Read, Map, Filter, Write, Select, ConvertFormat, FilterBySpec

        start_time = datetime.now()
        metrics: Dict[str, Any] = {
            "pipeline_name": pipeline.name,
            "operators_count": len(pipeline.operators),
        }

        if self.verbose:
            print(f"[LocalRunner] 开始执行 Pipeline: {pipeline.name}")
            print(f"[LocalRunner] 共 {len(pipeline.operators)} 个算子")

        try:
            data: List[Any] = []
            rows_in = 0

            for i, op in enumerate(pipeline.operators):
                if self.verbose:
                    print(f"[LocalRunner] 执行算子 {i+1}: {op}")

                if isinstance(op, Read):
                    if op.data is not None:
                        data = list(op.data)
                    else:
                        data = []
                    rows_in = len(data)
                    if self.verbose:
                        print(f"    读取 {len(data)} 条记录")

                elif isinstance(op, Filter):
                    before_count = len(data)
                    data = [r for r in data if op.predicate(r)]
                    if self.verbose:
                        print(f"    过滤: {before_count} -> {len(data)} 条")

                elif isinstance(op, Map):
                    data = [op.func(r) for r in data]
                    if self.verbose:
                        print(f"    映射: {len(data)} 条")

                elif isinstance(op, Select):
                    def select_fields(record, fields):
                        if hasattr(record, "model_dump"):
                            full = record.model_dump()
                            return {f: full.get(f) for f in fields}
                        elif isinstance(record, dict):
                            return {f: record.get(f) for f in fields}
                        return record

                    data = [select_fields(r, op.fields) for r in data]
                    if self.verbose:
                        print(f"    选择字段: {op.fields}")

                elif isinstance(op, ConvertFormat):
                    def convert(record, fmt):
                        if hasattr(record, f"as_{fmt}_format"):
                            return getattr(record, f"as_{fmt}_format")()
                        return record

                    data = [convert(r, op.target_format) for r in data]
                    if self.verbose:
                        print(f"    转换格式: {op.target_format}")

                elif isinstance(op, FilterBySpec):
                    before_count = len(data)
                    data = [r for r in data if op.spec.matches(r)]
                    if self.verbose:
                        print(f"    按规则过滤: {before_count} -> {len(data)} 条")

                elif isinstance(op, Write):
                    if self.verbose:
                        print(f"    输出 {len(data)} 条记录")

                else:
                    raise ValueError(f"不支持的算子类型: {type(op).__name__}")

            end_time = datetime.now()
            metrics.update({
                "rows_in": rows_in,
                "rows_out": len(data),
                "duration_ms": (end_time - start_time).total_seconds() * 1000,
            })

            if self.verbose:
                print(f"[LocalRunner] 执行完成: {metrics}")

            return RunResult(
                status=RunStatus.SUCCESS,
                metrics=metrics,
                output=data,
                start_time=start_time,
                end_time=end_time,
            )

        except Exception as e:
            end_time = datetime.now()
            if self.verbose:
                print(f"[LocalRunner] 执行失败: {e}")

            return RunResult(
                status=RunStatus.FAILED,
                metrics=metrics,
                error=str(e),
                start_time=start_time,
                end_time=end_time,
            )
