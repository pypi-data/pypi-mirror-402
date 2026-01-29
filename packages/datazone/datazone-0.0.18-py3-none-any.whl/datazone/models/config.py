from typing import List, Optional, Annotated, Union

from pydantic import BaseModel, FilePath, Field, StrictStr, model_validator

from datazone.utils.types import PydanticObjectId

KubernetesMemorySpec = Annotated[
    str, Field(pattern=r"^\d+[EPTGMK]i$", description="Kubernetes memory spec"),
]
KubernetesCPUSpec = Union[
    Annotated[str, Field(pattern=r"^\d+m?$", description="Kubernetes CPU spec")],
    int,
    float,
]

SparkMemorySpec = Annotated[
    str, Field(pattern=r"^\d+[kmgt]$", description="Spark memory spec"),
]


class Spec(BaseModel):
    cpu: Optional[KubernetesCPUSpec] = None
    memory: Optional[KubernetesMemorySpec] = None


class SparkSpec(BaseModel):
    cpu: Optional[Union[str, int, float]] = None
    memory: Optional[SparkMemorySpec] = None


class SparkExecutorSpec(BaseModel):
    memory: Optional[SparkMemorySpec] = None
    cpu: Optional[Union[str, int, float]] = None
    instances: Optional[int] = None


class Resources(BaseModel):
    requests: Optional[Spec] = None
    limits: Optional[Spec] = None


class SparkConfig(BaseModel):
    executor: Optional[SparkExecutorSpec] = None
    driver: Optional[SparkSpec] = None
    deploy_mode: Optional[str] = "local"


class Pipeline(BaseModel):
    alias: StrictStr
    name: Optional[StrictStr] = None
    path: FilePath
    resources: Optional[Resources] = None
    spark_config: Optional[SparkConfig] = None


class Config(BaseModel):
    project_name: str
    project_id: PydanticObjectId
    pipelines: List[Pipeline] = Field(default_factory=list)

    @model_validator(mode="before")
    def validate_pipeline_unique(cls, data):
        pipelines = None
        if isinstance(data, dict):
            pipelines = data.get("pipelines")

        if not pipelines:
            return data

        aliases = [
            pipeline.get("alias")
            for pipeline in pipelines
            if pipeline and "alias" in pipeline
        ]
        if len(aliases) != len(set(aliases)):
            raise ValueError("Pipeline aliases should be unique.")

        paths = [
            pipeline.get("path")
            for pipeline in pipelines
            if pipeline and "path" in pipeline
        ]
        if len(paths) != len(set(paths)):
            raise ValueError("Pipeline paths should be unique.")
        return data
