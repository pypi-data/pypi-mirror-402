from datetime import timedelta
from typing import List, Dict
from pydantic import BaseModel, ConfigDict, Field


class BaseAppModel(BaseModel):
    model_config = ConfigDict(
        ser_json_toplevel_exclude_none=True,  # effect .model_dump_json()
        ser_omit_none=True,                   # skip None when .model_dump()
    )

    def __repr__(self) -> str:
        fields = self.model_dump(exclude_none=True)
        return f"{self.__class__.__name__}({fields})"

    def __dir__(self):
        # Chỉ hiện field user định nghĩa
        return list(self.model_fields.keys())

    def model_dump(self, *args, **kwargs):
        # Mặc định exclude_none=True
        if 'exclude_none' not in kwargs:
            kwargs['exclude_none'] = True
        return super().model_dump(*args, **kwargs)


class RetryPolicy(BaseAppModel):
    initial_interval: int | None = None
    maximum_interval: int | None = None
    backoff_coefficient: float | None = None
    maximum_attempts: int | None = None
    non_retryable_error_types: List[str] | None = None


class Activity(BaseAppModel):
    name: str
    queue: str
    retry_policy: RetryPolicy | None = None
    schedule_to_close_timeout: int | None = None
    schedule_to_start_timeout: int | None = None
    start_to_close_timeout: int | None = None
    heartbeat_timeout: int | None = None
    app_config: Dict = Field(default_factory=dict)


class Workflow(BaseAppModel):
    name: str
    id: str | None = None
    queue: str | None = None
    retry_policy: RetryPolicy | None = None
    execution_timeout: int | None = None
    run_timeout: int | None = None
    task_timeout: int | None = None
    app_config: Dict = Field(default_factory=dict)


class InternalState(BaseAppModel):
    max_renews: int = 5
    current_renew: int = 0


class Executor(BaseAppModel):
    # workflow or activity config
    is_workflow: bool
    activity: Activity | None = None
    workflow: Workflow | None = None
    key_name: str | None = None  # Optional key name for identifying the executor
    input_keys: List[str] | None = None  # Optional key to extract specific input data
    wait_execution: bool = True  # Whether to wait for execution to complete
    internal_state: InternalState = Field(default_factory=InternalState)
    renew_when_expired: bool = False


class WorkflowInput(BaseAppModel):
    id: str | None = None
    input: Dict
    workflow_start: Workflow
    executors: List[Executor] = Field(default_factory=list)
    output_key: str | None = None  # Optional key to extract specific output data, if none return last executor output


class ActivityInput(BaseAppModel):
    id: str|None = None
    input: Dict
    app_config: Dict
