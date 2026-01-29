from datetime import timedelta
from temporalio import workflow, client
import dynamic_models.workflow_input as input_module
import temporalio.common as temporalio_common


def to_temporal_retry_policy(rp: input_module.RetryPolicy | None) -> temporalio_common.RetryPolicy | None:
    if rp is None or isinstance(rp, temporalio_common.RetryPolicy):
        return rp
    return temporalio_common.RetryPolicy(
        initial_interval=timedelta(milliseconds=rp.initial_interval) if rp.initial_interval else None,
        maximum_interval=timedelta(milliseconds=rp.maximum_interval) if rp.maximum_interval else None,
        backoff_coefficient=rp.backoff_coefficient or 2,
        maximum_attempts=rp.maximum_attempts or 0,
        non_retryable_error_types=rp.non_retryable_error_types,

    )


def to_timedelta(ms: int | None) -> timedelta | None:
    if ms is None:
        return None
    return timedelta(milliseconds=ms)


async def start_workflow(wflow: input_module.Workflow, input_data: input_module.WorkflowInput, workflow_executor: callable = None):
    child_workflow = await workflow_executor(
        wflow.name,
        input_data,
        id=wflow.id or None,
        task_queue=wflow.queue,
        retry_policy=to_temporal_retry_policy(wflow.retry_policy),
        execution_timeout=to_timedelta(wflow.execution_timeout),
        run_timeout=to_timedelta(wflow.run_timeout),
        task_timeout=to_timedelta(wflow.task_timeout),
        result_type=dict,
    )
    return child_workflow


async def process_workflow(id: str, wflow: input_module.Workflow, input_data: dict, wait_execution: bool, workflow_executor=None):
    workflow_executor = workflow_executor or (workflow.execute_child_workflow if wait_execution else workflow.start_child_workflow)
    child_workflow = await workflow_executor(
        wflow.name,
        input_module.ActivityInput(id=id, input=input_data, app_config=wflow.app_config),
        id=wflow.id or None,
        task_queue=wflow.queue,
        retry_policy=to_temporal_retry_policy(wflow.retry_policy),
        execution_timeout=to_timedelta(wflow.execution_timeout),
        run_timeout=to_timedelta(wflow.run_timeout),
        task_timeout=to_timedelta(wflow.task_timeout),
        result_type=dict,
    )
    return child_workflow


async def process_activity(id: str, activity: input_module.Activity, input_data: dict, wait_execution: bool):
    activity_executor = workflow.execute_activity if wait_execution else workflow.start_activity
    result = await activity_executor(
        activity.name,
        input_module.ActivityInput(id=id, input=input_data, app_config=activity.app_config),
        task_queue=activity.queue,
        retry_policy=to_temporal_retry_policy(activity.retry_policy),
        schedule_to_close_timeout=to_timedelta(activity.schedule_to_close_timeout),
        schedule_to_start_timeout=to_timedelta(activity.schedule_to_start_timeout),
        start_to_close_timeout=to_timedelta(activity.start_to_close_timeout),
        heartbeat_timeout=to_timedelta(activity.heartbeat_timeout),
        result_type=dict,
    )
    return result


async def process_executor(id: str, executor: input_module.Executor, input_data: dict):
    if executor.is_workflow and executor.workflow:
        return await process_workflow(id, executor.workflow, input_data, executor.wait_execution)
    elif not executor.is_workflow and executor.activity:
        return await process_activity(id, executor.activity, input_data, executor.wait_execution)
    else:
        raise ValueError("Invalid executor configuration")
