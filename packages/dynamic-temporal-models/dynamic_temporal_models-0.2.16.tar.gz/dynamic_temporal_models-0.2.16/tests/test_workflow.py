import uuid
import pytest
from temporalio.worker import Worker
from temporalio.testing import WorkflowEnvironment
import dynamic_models.workflow_input as input_module
from temporal.workflow import DynamicWorkflowExecutor
from temporalio.contrib.pydantic import pydantic_data_converter


@pytest.mark.asyncio
async def test_execute_workflow():
    task_queue_name = str(uuid.uuid4())
    async with await WorkflowEnvironment.start_time_skipping(data_converter=pydantic_data_converter) as env:
        async with Worker(
            env.client,
            task_queue=task_queue_name,
            workflows=[DynamicWorkflowExecutor],
        ):
            wfc = input_module.Workflow(name='', queue='')
            data = input_module.WorkflowInput(
                input={'name': 'World'},
                workflow_start=wfc
            )
            result = await env.client.execute_workflow(
                DynamicWorkflowExecutor.main_workflow, data,
                id=str(uuid.uuid4()),
                task_queue=task_queue_name,
            )
            pass
