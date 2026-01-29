"""Dataset - 数据集定义与筛选规则"""

from typing import Any, Dict, List, Optional, TYPE_CHECKING
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from .sample import Sample


class FilterCondition(BaseModel):
    """单个筛选条件"""
    field: str = Field(..., description="字段名")
    op: str = Field(..., description="操作符: ==, !=, >, >=, <, <=, in, not_in, contains")
    value: Any = Field(..., description="比较值")


class SamplingConfig(BaseModel):
    """采样配置"""
    strategy: str = Field(default="uniform", description="采样策略: uniform, stratified, random")
    max_samples: Optional[int] = Field(default=None, description="最大样本数")
    seed: Optional[int] = Field(default=None, description="随机种子")


class SelectionSpec(BaseModel):
    """
    数据筛选规则

    描述如何从数据源中选择样本。

    Example:
        >>> spec = SelectionSpec(
        ...     source=["online_log"],
        ...     time_range={"start": "2025-01-01", "end": "2025-01-07"},
        ...     filters=[
        ...         FilterCondition(field="language", op="==", value="zh"),
        ...         FilterCondition(field="quality_score", op=">=", value=0.7),
        ...     ],
        ...     sampling=SamplingConfig(strategy="uniform", max_samples=100000),
        ... )
    """
    source: List[str] = Field(default_factory=list, description="数据来源列表")
    time_range: Optional[Dict[str, str]] = Field(default=None, description="时间范围")
    filters: List[FilterCondition] = Field(default_factory=list, description="筛选条件")
    sampling: Optional[SamplingConfig] = Field(default=None, description="采样配置")

    def matches(self, sample: "Sample") -> bool:
        """检查样本是否匹配筛选规则"""
        # 检查数据来源
        if self.source and sample.source not in self.source:
            return False

        # 检查筛选条件
        for condition in self.filters:
            if not self._check_condition(sample, condition):
                return False

        return True

    def _check_condition(self, sample: "Sample", condition: FilterCondition) -> bool:
        """检查单个筛选条件"""
        # 获取字段值
        value = getattr(sample, condition.field, None)
        if value is None:
            value = sample.metadata.get(condition.field)

        # 执行比较
        op = condition.op
        target = condition.value

        if op == "==":
            return value == target
        elif op == "!=":
            return value != target
        elif op == ">":
            return value is not None and value > target
        elif op == ">=":
            return value is not None and value >= target
        elif op == "<":
            return value is not None and value < target
        elif op == "<=":
            return value is not None and value <= target
        elif op == "in":
            return value in target
        elif op == "not_in":
            return value not in target
        elif op == "contains":
            return target in value if value else False
        else:
            return True


class Dataset(BaseModel):
    """
    数据集定义

    逻辑数据集，包含样本引用和筛选规则。

    Attributes:
        dataset_id: 数据集唯一标识
        version: 版本号
        description: 描述
        sample_ids: 样本 ID 列表
        selection_spec: 筛选规则（数据是怎么选出来的）
        created_by: 创建者
        created_at: 创建时间戳
    """
    dataset_id: str = Field(..., description="数据集唯一标识")
    version: str = Field(default="1.0.0", description="版本号")
    description: Optional[str] = Field(default=None, description="描述")

    sample_ids: List[str] = Field(default_factory=list, description="样本 ID 列表")
    selection_spec: Optional[SelectionSpec] = Field(default=None, description="筛选规则")

    created_by: str = Field(default="unknown", description="创建者")
    created_at: int = Field(..., description="创建时间戳（毫秒）")

    # 元数据
    metadata: Dict[str, Any] = Field(default_factory=dict, description="附加元数据")

    def __len__(self) -> int:
        """返回样本数量"""
        return len(self.sample_ids)

    def add_sample(self, sample_id: str) -> "Dataset":
        """添加样本"""
        if sample_id not in self.sample_ids:
            self.sample_ids.append(sample_id)
        return self

    def add_samples(self, sample_ids: List[str]) -> "Dataset":
        """批量添加样本"""
        for sid in sample_ids:
            self.add_sample(sid)
        return self
