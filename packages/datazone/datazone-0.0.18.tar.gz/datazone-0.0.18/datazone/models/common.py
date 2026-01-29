from enum import Enum
from typing import List


class ExecutionTypes(str, Enum):
    ALL = "all"
    SINGLE = "single"
    UPSTREAM = "upstream"
    DOWNSTREAM = "downstream"


class ExecutionStatus(str, Enum):
    CREATED = "CREATED"
    WAITING_UPSTREAMS = "WAITING_UPSTREAMS"
    UPSTREAM_FAILURE = "UPSTREAM_FAILURE"
    READY_TO_START = "READY_TO_START"
    NOT_STARTED = "NOT_STARTED"
    STARTING = "STARTING"
    STARTED = "STARTED"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    CANCELING = "CANCELING"
    CANCELED = "CANCELED"


RUNNING_STATUSES: List[ExecutionStatus] = [ExecutionStatus.STARTING, ExecutionStatus.STARTED]

FINISHED_STATUSES: List[ExecutionStatus] = [
    ExecutionStatus.SUCCESS,
    ExecutionStatus.FAILURE,
    ExecutionStatus.CANCELED,
    ExecutionStatus.UPSTREAM_FAILURE,
]


class JobType(str, Enum):
    EXTRACT = "extract"
    PIPELINE = "pipeline"


class OutputMode(str, Enum):
    OVERWRITE = "overwrite"
    APPEND = "append"
