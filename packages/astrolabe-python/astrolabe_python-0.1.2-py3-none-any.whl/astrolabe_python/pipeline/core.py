from typing import TYPE_CHECKING, Any, Dict, List, Optional
from ..operator import Op

if TYPE_CHECKING:
    from ..runner import Runner, RunResult

class Pipeline:
    """
    数据处理流水线

    Pipeline 是一系列算子的有序集合，描述从数据读取到输出的完整流程。

    设计说明：
    - add() 返回 self，支持链式调用
    - run() 接收 Runner，实现 Pipeline 与执行引擎解耦

    Example:
        >>> pipeline = (
        ...     Pipeline("etl_job")
        ...     .add(Read(data=samples))
        ...     .add(Filter(lambda s: s.language == "zh"))
        ...     .add(Map(lambda s: transform(s)))
        ...     .add(Write())
        ... )
        >>> result = pipeline.run(LocalRunner())
    """

    def __init__(self, name: str):
        self.name = name
        self.operators: List[Op] = []
        self._metadata: Dict[str, Any] = {}

    def add(self, op: Op) -> "Pipeline":
        """添加算子到 Pipeline"""
        self.operators.append(op)
        return self

    def run(self, runner: "Runner") -> "RunResult":
        """执行 Pipeline"""
        return runner.run(self)

    def set_metadata(self, key: str, value: Any) -> "Pipeline":
        """设置元数据"""
        self._metadata[key] = value
        return self

    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典"""
        return {
            "name": self.name,
            "operators": [op.to_dict() for op in self.operators],
            "metadata": self._metadata,
        }

    def __len__(self) -> int:
        return len(self.operators)

    def __repr__(self) -> str:
        return f"Pipeline({self.name!r}, operators={len(self.operators)})"

    def describe(self) -> str:
        """返回 Pipeline 的可读描述"""
        lines = [f"Pipeline: {self.name}", "=" * 40]
        for i, op in enumerate(self.operators, 1):
            lines.append(f"  {i}. {op}")
        return "\n".join(lines)


class PipelineBuilder:
    def __init__(self, name: str):
        self._pipeline = Pipeline(name)

    def read(self, data=None, dataset=None) -> "PipelineBuilder":
        from ..operator import Read
        self._pipeline.add(Read(data=data, dataset=dataset))
        return self

    def filter(self, predicate) -> "PipelineBuilder":
        from ..operator import Filter
        self._pipeline.add(Filter(predicate))
        return self

    def map(self, func) -> "PipelineBuilder":
        from ..operator import Map
        self._pipeline.add(Map(func))
        return self

    def select(self, fields) -> "PipelineBuilder":
        from ..operator import Select
        self._pipeline.add(Select(fields))
        return self

    def write(self, target=None, mode="overwrite") -> "PipelineBuilder":
        from ..operator import Write
        self._pipeline.add(Write(target=target, mode=mode))
        return self

    def build(self) -> Pipeline:
        """构建并返回 Pipeline"""
        return self._pipeline
