from typing import Any, Callable, Dict, List, Optional, Union

from .base import Op
from ..schema import Sample, Dataset

class Read(Op):
    """
    读取算子

    从指定的数据源读取数据。支持：
    - 直接传入 Sample 列表
    - 传入 Dataset 对象
    - 传入原始字典数据
    """

    def __init__(
        self,
        data: Optional[Union[List[Sample], List[Dict[str, Any]]]] = None,
        dataset: Optional[Dataset] = None,
        name: Optional[str] = None,
    ):
        super().__init__(name=name or "Read")
        self.data = data
        self.dataset = dataset

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        if self.dataset:
            base["dataset_id"] = self.dataset.dataset_id
        if self.data:
            base["data_count"] = len(self.data)
        return base


class Map(Op):
    """
    对每条记录应用转换函数，生成新记录。
    """

    def __init__(
        self,
        func: Callable[[Any], Any],
        name: Optional[str] = None,
    ):
        super().__init__(name=name or "Map")
        self.func = func

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base["func_name"] = getattr(self.func, "__name__", "<lambda>")
        return base

class Filter(Op):
    """
    根据条件函数过滤记录，只保留满足条件的记录。
    """

    def __init__(
        self,
        predicate: Callable[[Any], bool],
        name: Optional[str] = None,
    ):
        super().__init__(name=name or "Filter")
        self.predicate = predicate

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base["predicate_name"] = getattr(self.predicate, "__name__", "<lambda>")
        return base

class Write(Op):
    """
    将数据写入目标
    """

    def __init__(
        self,
        target: Optional[str] = None,
        mode: str = "overwrite",
        format: str = "json",
        name: Optional[str] = None,
    ):
        super().__init__(name=name or "Write")
        self.target = target
        self.mode = mode
        self.format = format

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base["target"] = self.target
        base["mode"] = self.mode
        base["format"] = self.format
        return base

class Select(Op):
    """
    选择 Sample 的指定字段，用于数据裁剪。
    """

    def __init__(
        self,
        fields: List[str],
        name: Optional[str] = None,
    ):
        super().__init__(name=name or "Select")
        self.fields = fields

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base["fields"] = self.fields
        return base


class Join(Op):
    """
    将两个数据集按指定键连接。
    """

    def __init__(
        self,
        right: Union[List[Any], Dataset],
        left_key: str,
        right_key: str,
        how: str = "inner",
        name: Optional[str] = None,
    ):
        super().__init__(name=name or "Join")
        self.right = right
        self.left_key = left_key
        self.right_key = right_key
        self.how = how

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base["left_key"] = self.left_key
        base["right_key"] = self.right_key
        base["how"] = self.how
        return base

class ConvertFormat(Op):
    """
    将 Sample 转换为指定的 LLM API 格式。
    """

    def __init__(
        self,
        target_format: str = "openai",
        name: Optional[str] = None,
    ):
        super().__init__(name=name or f"ConvertFormat({target_format})")
        self.target_format = target_format

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base["target_format"] = self.target_format
        return base


class FilterBySpec(Op):
    """
    使用 SelectionSpec 筛选 Sample。
    """

    def __init__(
        self,
        spec: Any,  # SelectionSpec
        name: Optional[str] = None,
    ):
        super().__init__(name=name or "FilterBySpec")
        self.spec = spec

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        if hasattr(self.spec, "model_dump"):
            base["spec"] = self.spec.model_dump()
        return base
