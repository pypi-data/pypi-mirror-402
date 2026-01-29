# mypy: disable-error-code=empty-body
from typing import List, Callable, Dict, Optional, TypeVar, Any, Union, Literal
from enum import Enum

TransformFunction = TypeVar("TransformFunction", bound=Callable[..., Any])


class OutputMode(str, Enum):
    OVERWRITE = "overwrite"
    APPEND = "append"


OutputModeType = Union[Literal["overwrite"], Literal["append"], OutputMode]


class Dataset:
    def __init__(
        self,
        id: str | None = None,
        alias: str | None = None,
        run_upstream: bool = False,
        freshness_duration: Optional[int] = None,
    ) -> None:
        ...


class Variable:
    def __init__(self, name: str) -> None:
        ...

    def get_value(self) -> str:
        ...


class Input:
    entity: Union[Dataset, Callable[..., Any]]
    output_name: Optional[str]
    kwargs: Dict[str, Any]

    def __init__(
        self,
        entity: Union[Dataset, Callable[..., Any]],
        output_name: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        ...


class Output:
    dataset: Optional[Dataset]
    materialized: bool
    partition_by: Optional[List[str]]
    mode: Optional[OutputModeType]

    def __init__(
        self,
        dataset: Optional[Dataset] = None,
        materialized: bool = False,
        partition_by: Optional[List[str]] = None,
        mode: Optional[OutputModeType] = OutputMode.OVERWRITE,
    ) -> None:
        ...


def transform(
    compute_fn: Optional[TransformFunction] = None,
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    input_mapping: Optional[Dict[str, Input]] = None,
    output_mapping: Optional[Dict[str, Output]] = None,
    partition_by: Optional[List[str]] = None,
    materialized: Optional[bool] = False,
    tags: Optional[List[Any]] = None,
) -> Callable[[TransformFunction], TransformFunction]:
    ...
