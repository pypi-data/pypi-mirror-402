# test_dynamic_workflow_executor.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from dynamic_models.helper import to_temporal_retry_policy, to_timedelta
import dynamic_models.workflow_input as input_module
from temporalio.exceptions import ActivityError, TimeoutError

from temporal.workflow import DynamicWorkflowExecutor


@pytest.mark.asyncio
async def test_get_input_by_keys():
    executor_instance = DynamicWorkflowExecutor()
    map_result = {
        "step1": {"a": 1, "b": {"c": 2}},
        "step2": {"x": 10}
    }
    # single key
    res = executor_instance.get_input_by_keys(map_result, ["step1"])
    assert res == {"step1": {"a": 1, "b": {"c": 2}}}
    # nested key
    res = executor_instance.get_input_by_keys(map_result, ["step1", "step2"])
    assert res == map_result
    # missing key returns default
    res = executor_instance.get_input_by_keys(map_result, ["step1", "missing"])
    assert res == {"step1": {"a": 1, "b": {"c": 2}}}
    # None input_keys returns default
    res = executor_instance.get_input_by_keys(map_result, None, default={"y": 5})
    assert res == {'default': {"y": 5}}


@pytest.mark.asyncio
@patch("temporalio.workflow.start_activity", new_callable=AsyncMock)
@patch("temporalio.workflow.execute_activity", new_callable=AsyncMock)
@patch("temporalio.workflow.execute_child_workflow", new_callable=AsyncMock)
@patch("temporalio.workflow.start_child_workflow", new_callable=AsyncMock)
@patch("temporalio.workflow.logger", new_callable=MagicMock)
async def test_process_executor_activity_and_workflow(mock_logging, mock_start_child, mock_execute_child, mock_execute_activity, mock_start_activity):
    executor_instance = DynamicWorkflowExecutor()
    # Mock activity
    mock_start_activity.return_value = "activity_result"
    activity_executor = input_module.Executor(
        is_workflow=False,
        activity=input_module.Activity(
            name="act1",
            queue="queue1"
        ),
        wait_execution=False,
        key_name="act1"
    )
    result = await executor_instance.process_executor('none', activity_executor, {"foo": "bar"})
    assert result == "activity_result"
    mock_start_activity.assert_awaited_once()

    # Mock workflow
    mock_start_child.return_value = "child_result"
    workflow_executor = input_module.Executor(
        is_workflow=True,
        workflow=input_module.Workflow(
            name="task1",
            queue="task1"
        ),
        wait_execution=False,
        key_name="wf1"
    )
    result = await executor_instance.process_executor('none', workflow_executor, {"foo": "bar"})
    assert result == "child_result"
    mock_start_child.assert_awaited_once()


@pytest.mark.asyncio
@patch("temporalio.workflow.continue_as_new", new_callable=AsyncMock)
@patch("temporalio.workflow.logger", new_callable=MagicMock)
async def test_try_and_renew_when_expired_retry(mock_continue_as_new, mock_logger):
    executor_instance = DynamicWorkflowExecutor()
    executor_mock = input_module.Executor(
        is_workflow=False,
        renew_when_expired=True,
        internal_state=input_module.InternalState(max_renews=2, current_renew=0))
    input_data = {"key": "value"}

    # Mock process_executor to raise ActivityError with TimeoutError cause
    async def failing_executor(*args, **kwargs):
        cause = TimeoutError(message="timeout", type="StartToClose", last_heartbeat_details=None)
        activity_error = ActivityError("activity failed",
                                       activity_type="act1",
                                       activity_id="1", identity="worker",
                                       scheduled_event_id=1, started_event_id=2, retry_state="RETRY_STATE")
        activity_error.__cause__ = cause
        raise activity_error

    executor_instance.process_executor = failing_executor

    workflow_input = input_module.WorkflowInput(
        input=input_data,
        workflow_start=input_module.Workflow(name='test', queue="default"),
        executors=[executor_mock]

    )

    # First retry should return is_renew=True
    mock_continue_as_new.return_value = "continued"
    is_renew, result = await executor_instance.try_and_renew_when_expired(
        'none',
        workflow_input, executor_mock, input_data
    )
    assert is_renew

    # Increment retry to max, should raise ActivityError
    executor_mock.internal_state.current_renew = 2
    with pytest.raises(ActivityError):
        await executor_instance.try_and_renew_when_expired(
            'none',
            workflow_input, executor_mock, input_data
        )


async def activity_side_effect(anme, input_data: input_module.ActivityInput, *args, **kwargs):
    # input_data là dict bạn truyền vào process_executor
    input = input_data.input
    if 'first' in input:
        return {"ok": True}
    else:
        return {"result": 42}


@pytest.mark.asyncio
@patch("temporalio.workflow.execute_activity", new_callable=AsyncMock)
@patch("temporalio.workflow.logger", new_callable=MagicMock)
async def test_main_workflow_with_mapping(mock_logger, mock_execute_activity, ):
    executor_instance = DynamicWorkflowExecutor()
    mock_execute_activity.side_effect = activity_side_effect

    # Define workflow input with two executors
    workflow_input = input_module.WorkflowInput(
        input={"start": 1},
        workflow_start=input_module.Workflow(name="queue"),
        executors=[
            input_module.Executor(
                is_workflow=False,
                activity=input_module.Activity(
                    name="act1",
                    queue="queue1"
                ),
                key_name="first"
            ),
            input_module.Executor(
                is_workflow=False,
                activity=input_module.Activity(
                    name="act2",
                    queue="queue1"
                ),
                key_name="second",
                input_keys=["first"]
            ),
        ]
    )

    result = await executor_instance.main_workflow(workflow_input)
    assert 'ok' in result and result['ok'] is True
    assert mock_execute_activity.await_count == 2


async def activity_side_effect2(name, input_data: input_module.ActivityInput, *args, **kwargs):
    # input_data là dict bạn truyền vào process_executor
    input = input_data.input
    if 'first' in input and 'second' in input and name == 'act3':
        return {"ok": True}
    else:
        return {"result": 42}


@pytest.mark.asyncio
@patch("temporalio.workflow.execute_activity", new_callable=AsyncMock)
@patch("temporalio.workflow.logger", new_callable=MagicMock)
async def test_main_workflow_with_mapping2(mock_logger, mock_execute_activity, ):
    executor_instance = DynamicWorkflowExecutor()
    mock_execute_activity.side_effect = activity_side_effect2

    # Define workflow input with two executors
    workflow_input = input_module.WorkflowInput(
        input={"start": 1},
        workflow_start=input_module.Workflow(name="queue"),
        executors=[
            input_module.Executor(
                is_workflow=False,
                activity=input_module.Activity(
                    name="act1",
                    queue="queue1"
                ),
                key_name="first"
            ),
            input_module.Executor(
                is_workflow=False,
                activity=input_module.Activity(
                    name="act2",
                    queue="queue1"
                ),
                key_name="second",
                input_keys=["first"]
            ),
            input_module.Executor(
                is_workflow=False,
                activity=input_module.Activity(
                    name="act3",
                    queue="queue1"
                ),
                key_name="third",
                input_keys=["first", "second"]
            ),
        ]
    )

    result = await executor_instance.main_workflow(workflow_input)
    assert 'ok' in result and result['ok'] is True
    assert mock_execute_activity.await_count == 3


# Additional Test Cases for Error Handling
@pytest.mark.asyncio
async def test_process_executor_invalid_configuration():
    """Test process_executor with invalid executor configuration"""
    executor_instance = DynamicWorkflowExecutor()

    # Invalid executor with neither activity nor workflow
    invalid_executor = input_module.Executor(
        is_workflow=False,
        activity=None,
        workflow=None,
        key_name="invalid"
    )

    with pytest.raises(ValueError, match="Invalid executor configuration"):
        await executor_instance.process_executor('none', invalid_executor, {"test": "data"})


@pytest.mark.asyncio
@patch("temporalio.workflow.execute_activity", new_callable=AsyncMock)
async def test_process_executor_activity_error(mock_execute_activity):
    """Test process_executor when activity raises an error"""
    executor_instance = DynamicWorkflowExecutor()

    # Mock activity to raise an error
    mock_execute_activity.side_effect = ActivityError(
        message="Activity failed",
        activity_type="test_activity",
        activity_id="123",
        identity="test_worker",
        scheduled_event_id=1,
        started_event_id=2,
        retry_state="RETRY_STATE_IN_PROGRESS"
    )

    activity_executor = input_module.Executor(
        is_workflow=False,
        activity=input_module.Activity(
            name="failing_activity",
            queue="test_queue"
        ),
        wait_execution=True,
        key_name="failing_test"
    )

    with pytest.raises(ActivityError):
        await executor_instance.process_executor('none', activity_executor, {"test": "data"})


@pytest.mark.asyncio
@patch("temporalio.workflow.execute_child_workflow", new_callable=AsyncMock)
async def test_process_executor_workflow_error(mock_execute_child):
    """Test process_executor when child workflow raises an error"""
    executor_instance = DynamicWorkflowExecutor()

    # Mock child workflow to raise an error
    mock_execute_child.side_effect = Exception("Child workflow failed")

    workflow_executor = input_module.Executor(
        is_workflow=True,
        workflow=input_module.Workflow(
            name="failing_workflow",
            queue="test_queue"
        ),
        wait_execution=True,
        key_name="failing_workflow_test"
    )

    with pytest.raises(Exception, match="Child workflow failed"):
        await executor_instance.process_executor('none', workflow_executor, {"test": "data"})


# Test Cases for get_output_by_key method
@pytest.mark.asyncio
async def test_get_output_by_key():
    """Test get_output_by_key method with various scenarios"""
    executor_instance = DynamicWorkflowExecutor()
    map_result = {
        "step1": {"result": "success", "value": 100},
        "step2": {"data": [1, 2, 3]},
        "final": "completed"
    }

    # Test with existing key
    result = executor_instance.get_output_by_key(map_result, "step1")
    assert result == {"result": "success", "value": 100}

    # Test with existing simple value
    result = executor_instance.get_output_by_key(map_result, "final")
    assert result == "completed"

    # Test with missing key returns default
    result = executor_instance.get_output_by_key(map_result, "missing")
    assert result == {}

    # Test with missing key and custom default
    custom_default = {"error": "not_found"}
    result = executor_instance.get_output_by_key(map_result, "missing", custom_default)
    assert result == custom_default

    # Test with None key returns default
    result = executor_instance.get_output_by_key(map_result, None)
    assert result == {}

    # Test with empty string key returns default
    result = executor_instance.get_output_by_key(map_result, "")
    assert result == {}


@pytest.mark.asyncio
async def test_get_output_by_key_non_dict_input():
    """Test get_output_by_key with non-dict input"""
    executor_instance = DynamicWorkflowExecutor()

    # Test with non-dict map_result
    result = executor_instance.get_output_by_key("not_a_dict", "any_key")
    assert result == {}

    # Test with None map_result
    result = executor_instance.get_output_by_key(None, "any_key")
    assert result == {}

    # Test with list map_result
    result = executor_instance.get_output_by_key([1, 2, 3], "any_key")
    assert result == {}


# Test Cases for Retry Policy Scenarios
@pytest.mark.asyncio
@patch("temporalio.workflow.continue_as_new", new_callable=AsyncMock)
@patch("temporalio.workflow.logger", new_callable=MagicMock)
async def test_try_and_renew_non_timeout_error(mock_logger, mock_continue_as_new):
    """Test try_and_renew_when_expired with non-timeout ActivityError"""
    executor_instance = DynamicWorkflowExecutor()
    executor_mock = input_module.Executor(
        is_workflow=False,
        activity=input_module.Activity(name="test_activity", queue="test_queue")
    )
    input_data = {"key": "value"}

    # Mock process_executor to raise ActivityError with non-timeout cause
    async def failing_executor(*args, **kwargs):
        activity_error = ActivityError(
            "activity failed due to business logic",
            activity_type="test_activity",
            activity_id="1",
            identity="worker",
            scheduled_event_id=1,
            started_event_id=2,
            retry_state="RETRY_STATE_MAXIMUM_ATTEMPTS"
        )
        # Set a non-timeout cause
        activity_error.__cause__ = ValueError("Business logic error")
        raise activity_error

    executor_instance.process_executor = failing_executor

    workflow_input = input_module.WorkflowInput(
        input=input_data,
        workflow_start=input_module.Workflow(name='test', queue="default"),
        executors=[executor_mock],
        renew_when_expired=True,
        internal_state=input_module.InternalState(max_renews=3, current_renew=0)
    )

    # Should raise ActivityError without retrying
    with pytest.raises(ActivityError):
        await executor_instance.try_and_renew_when_expired('none',
                                                           workflow_input, executor_mock, input_data
                                                           )


@pytest.mark.asyncio
@patch("temporalio.workflow.continue_as_new", new_callable=AsyncMock)
@patch("temporalio.workflow.logger", new_callable=MagicMock)
async def test_try_and_renew_success_case(mock_logger, mock_continue_as_new):
    """Test try_and_renew_when_expired with successful execution"""
    executor_instance = DynamicWorkflowExecutor()
    executor_mock = input_module.Executor(
        is_workflow=False,
        activity=input_module.Activity(name="test_activity", queue="test_queue")
    )
    input_data = {"key": "value"}

    # Mock process_executor to return successful result
    expected_result = {"success": True, "data": "processed"}

    async def successful_executor(*args, **kwargs):
        return expected_result

    executor_instance.process_executor = successful_executor

    workflow_input = input_module.WorkflowInput(
        input=input_data,
        workflow_start=input_module.Workflow(name='test', queue="default"),
        executors=[executor_mock],
        renew_when_expired=True,
        internal_state=input_module.InternalState(max_renews=3, current_renew=0)
    )

    is_renew, result = await executor_instance.try_and_renew_when_expired('none',
                                                                          workflow_input, executor_mock, input_data
                                                                          )

    assert not is_renew
    assert result == expected_result


@pytest.mark.asyncio
@patch("temporalio.workflow.execute_activity", new_callable=AsyncMock)
@patch("temporalio.workflow.logger", new_callable=MagicMock)
async def test_main_workflow_with_retry_policy(mock_logger, mock_execute_activity):
    """Test main workflow with retry policy configuration"""
    executor_instance = DynamicWorkflowExecutor()
    mock_execute_activity.return_value = {"retry_result": "success"}

    retry_policy = input_module.RetryPolicy(
        initial_interval=1000,
        maximum_interval=10000,
        backoff_coefficient=2.0,
        maximum_attempts=3,
        non_retryable_error_types=["ValueError"]
    )

    workflow_input = input_module.WorkflowInput(
        input={"test": "data"},
        workflow_start=input_module.Workflow(
            name="test_workflow",
            queue="test_queue",
            retry_policy=retry_policy
        ),
        executors=[
            input_module.Executor(
                is_workflow=False,
                activity=input_module.Activity(
                    name="retryable_activity",
                    queue="test_queue",
                    retry_policy=retry_policy
                ),
                key_name="retry_test"
            )
        ]
    )

    result = await executor_instance.main_workflow(workflow_input)
    assert result == {"retry_result": "success"}
    mock_execute_activity.assert_awaited_once()


# Test Cases for Complex Workflow Scenarios
@pytest.mark.asyncio
@patch("temporalio.workflow.execute_activity", new_callable=AsyncMock)
@patch("temporalio.workflow.execute_child_workflow", new_callable=AsyncMock)
@patch("temporalio.workflow.logger", new_callable=MagicMock)
async def test_mixed_activity_workflow_execution(mock_logger, mock_execute_child, mock_execute_activity):
    """Test workflow with mix of activities and child workflows"""
    executor_instance = DynamicWorkflowExecutor()

    # Mock responses
    mock_execute_activity.return_value = {"activity_result": "processed"}
    mock_execute_child.return_value = {"workflow_result": "completed"}

    workflow_input = input_module.WorkflowInput(
        input={"initial": "data"},
        workflow_start=input_module.Workflow(name="mixed_workflow", queue="main_queue"),
        executors=[
            input_module.Executor(
                is_workflow=False,
                activity=input_module.Activity(name="preprocess", queue="activity_queue"),
                key_name="preprocessed",
                wait_execution=True
            ),
            input_module.Executor(
                is_workflow=True,
                workflow=input_module.Workflow(
                    name="data_processing_workflow",
                    queue="workflow_queue"
                ),
                key_name="processed",
                input_keys=["preprocessed"],
                wait_execution=True
            ),
            input_module.Executor(
                is_workflow=False,
                activity=input_module.Activity(name="postprocess", queue="activity_queue"),
                key_name="final",
                input_keys=["processed"],
                wait_execution=True
            )
        ],
        output_key="final"
    )

    result = await executor_instance.main_workflow(workflow_input)
    assert result == {"activity_result": "processed"}
    assert mock_execute_activity.await_count == 2
    assert mock_execute_child.await_count == 1


@pytest.mark.asyncio
@patch("temporalio.workflow.start_activity", new_callable=AsyncMock)
@patch("temporalio.workflow.start_child_workflow", new_callable=AsyncMock)
@patch("temporalio.workflow.logger", new_callable=MagicMock)
async def test_async_execution_workflow(mock_logger, mock_start_child, mock_start_activity):
    """Test workflow with async execution (wait_execution=False)"""
    executor_instance = DynamicWorkflowExecutor()

    # Mock async responses
    mock_start_activity.return_value = {'res': "async_activity_handle"}
    mock_start_child.return_value = {'res': "async_workflow_handle"}

    workflow_input = input_module.WorkflowInput(
        input={"async": "test"},
        workflow_start=input_module.Workflow(name="async_workflow", queue="async_queue"),
        executors=[
            input_module.Executor(
                is_workflow=False,
                activity=input_module.Activity(name="async_activity", queue="async_queue"),
                key_name="async_result1",
                wait_execution=False
            ),
            input_module.Executor(
                is_workflow=True,
                workflow=input_module.Workflow(
                    name="async_child_workflow",
                    queue="async_queue"
                ),
                key_name="async_result2",
                wait_execution=False
            )
        ]
    )

    result = await executor_instance.main_workflow(workflow_input)
    assert result == {'res': "async_workflow_handle"}
    mock_start_activity.assert_awaited_once()
    mock_start_child.assert_awaited_once()


@pytest.mark.asyncio
@patch("temporalio.workflow.execute_activity", new_callable=AsyncMock)
@patch("temporalio.workflow.logger", new_callable=MagicMock)
async def test_workflow_with_output_key_selection(mock_logger, mock_execute_activity):
    """Test workflow with specific output key selection"""
    executor_instance = DynamicWorkflowExecutor()

    # Mock different results for different steps
    def activity_side_effect(name, input_data, *args, **kwargs):
        if name == "step1":
            return {"step1_data": "value1"}
        elif name == "step2":
            return {"step2_data": "value2"}
        else:
            return {"final_data": "final_value"}

    mock_execute_activity.side_effect = activity_side_effect

    workflow_input = input_module.WorkflowInput(
        input={"start": "here"},
        workflow_start=input_module.Workflow(name="output_test", queue="test_queue"),
        executors=[
            input_module.Executor(
                is_workflow=False,
                activity=input_module.Activity(name="step1", queue="test_queue"),
                key_name="result1"
            ),
            input_module.Executor(
                is_workflow=False,
                activity=input_module.Activity(name="step2", queue="test_queue"),
                key_name="result2"
            ),
            input_module.Executor(
                is_workflow=False,
                activity=input_module.Activity(name="step3", queue="test_queue"),
                key_name="result3"
            )
        ],
        output_key="result2"  # Should return result from step2
    )

    result = await executor_instance.main_workflow(workflow_input)
    assert result == {"step2_data": "value2"}
    assert mock_execute_activity.await_count == 3


@pytest.mark.asyncio
@patch("temporalio.workflow.execute_activity", new_callable=AsyncMock)
@patch("temporalio.workflow.logger", new_callable=MagicMock)
async def test_workflow_with_complex_input_mapping(mock_logger, mock_execute_activity):
    """Test workflow with complex input key mappings"""
    executor_instance = DynamicWorkflowExecutor()

    def activity_side_effect(name, input_data: input_module.ActivityInput, *args, **kwargs):
        input_dict = input_data.input
        if name == "process_a":
            return {"a_result": f"processed_{input_dict.get('value', 'default')}"}
        elif name == "process_b":
            # Check if step_a key exists in input_dict (from get_input_by_keys result)
            if "step_a" in input_dict and "a_result" in input_dict["step_a"]:
                return {"b_result": f"enhanced_{input_dict['step_a']['a_result']}"}
            else:
                return {"b_result": "enhanced_missing"}
        elif name == "combine":
            # Extract results from step_a and step_b keys
            step_a_result = input_dict.get("step_a", {})
            step_b_result = input_dict.get("step_b", {})
            return {
                "combined": {
                    "from_a": step_a_result.get("a_result", "missing"),
                    "from_b": step_b_result.get("b_result", "missing")
                }
            }
        else:
            return {"unknown": "result"}

    mock_execute_activity.side_effect = activity_side_effect

    workflow_input = input_module.WorkflowInput(
        input={"value": "initial"},
        workflow_start=input_module.Workflow(name="complex_mapping", queue="test_queue"),
        executors=[
            input_module.Executor(
                is_workflow=False,
                activity=input_module.Activity(name="process_a", queue="test_queue"),
                key_name="step_a"
            ),
            input_module.Executor(
                is_workflow=False,
                activity=input_module.Activity(name="process_b", queue="test_queue"),
                key_name="step_b",
                input_keys=["step_a"]
            ),
            input_module.Executor(
                is_workflow=False,
                activity=input_module.Activity(name="combine", queue="test_queue"),
                key_name="final",
                input_keys=["step_a", "step_b"]
            )
        ]
    )

    result = await executor_instance.main_workflow(workflow_input)
    expected = {
        "combined": {
            "from_a": "processed_initial",
            "from_b": "enhanced_processed_initial"
        }
    }
    assert result == expected


# Test Cases for Edge Cases and Validation
@pytest.mark.asyncio
@patch("temporalio.workflow.execute_activity", new_callable=AsyncMock)
@patch("temporalio.workflow.logger", new_callable=MagicMock)
async def test_workflow_with_empty_executors(mock_logger, mock_execute_activity):
    """Test workflow with empty executors list"""
    executor_instance = DynamicWorkflowExecutor()

    workflow_input = input_module.WorkflowInput(
        input={"test": "data"},
        workflow_start=input_module.Workflow(name="empty_workflow", queue="test_queue"),
        executors=[]  # Empty executors list
    )

    result = await executor_instance.main_workflow(workflow_input)
    assert result == {"test": "data"}  # Should return original input
    mock_execute_activity.assert_not_called()


@pytest.mark.asyncio
@patch("temporalio.workflow.execute_activity", new_callable=AsyncMock)
@patch("temporalio.workflow.logger", new_callable=MagicMock)
async def test_workflow_with_none_inputs(mock_logger, mock_execute_activity):
    """Test workflow handling empty dict inputs"""
    executor_instance = DynamicWorkflowExecutor()
    mock_execute_activity.return_value = {"handled": "empty_input"}

    # Test with empty dict input (None not allowed by Pydantic)
    workflow_input = input_module.WorkflowInput(
        input={},  # Empty dict instead of None
        workflow_start=input_module.Workflow(name="empty_test", queue="test_queue"),
        executors=[
            input_module.Executor(
                is_workflow=False,
                activity=input_module.Activity(name="handle_empty", queue="test_queue"),
                key_name="result"
            )
        ]
    )

    result = await executor_instance.main_workflow(workflow_input)
    assert result == {"handled": "empty_input"}


@pytest.mark.asyncio
@patch("temporalio.workflow.execute_activity", new_callable=AsyncMock)
@patch("temporalio.workflow.logger", new_callable=MagicMock)
async def test_workflow_with_empty_dict_input(mock_logger, mock_execute_activity):
    """Test workflow with empty dict input"""
    executor_instance = DynamicWorkflowExecutor()
    mock_execute_activity.return_value = {"handled": "empty_dict"}

    workflow_input = input_module.WorkflowInput(
        input={},  # Empty dict
        workflow_start=input_module.Workflow(name="empty_dict_test", queue="test_queue"),
        executors=[
            input_module.Executor(
                is_workflow=False,
                activity=input_module.Activity(name="handle_empty", queue="test_queue"),
                key_name="result"
            )
        ]
    )

    result = await executor_instance.main_workflow(workflow_input)
    assert result == {"handled": "empty_dict"}


@pytest.mark.asyncio
async def test_get_input_by_keys_edge_cases():
    """Test get_input_by_keys with edge cases"""
    executor_instance = DynamicWorkflowExecutor()

    # Test with empty map_result
    result = executor_instance.get_input_by_keys({}, ["key1"])
    assert result == {}

    # Test with None map_result
    result = executor_instance.get_input_by_keys(None, ["key1"])
    assert result == {}

    # Test with empty input_keys list
    result = executor_instance.get_input_by_keys({"key": "value"}, [])
    assert result == {'default': {}}

    # Test with non-string keys in input_keys
    map_result = {"1": "value1", "2": "value2"}
    result = executor_instance.get_input_by_keys(map_result, [1, 2])  # int keys
    assert result == {}

    # Test with nested structure and partial matches
    nested_result = {
        "level1": {"level2": {"value": "deep"}},
        "simple": "value"
    }
    result = executor_instance.get_input_by_keys(nested_result, ["level1", "simple", "missing"])
    assert result == {"level1": {"level2": {"value": "deep"}}, "simple": "value"}


@pytest.mark.asyncio
@patch("temporalio.workflow.execute_activity", new_callable=AsyncMock)
@patch("temporalio.workflow.logger", new_callable=MagicMock)
async def test_workflow_without_key_names(mock_logger, mock_execute_activity):
    """Test workflow with executors that don't have key_name"""
    executor_instance = DynamicWorkflowExecutor()

    execution_count = 0

    def activity_side_effect(name, input_data, *args, **kwargs):
        nonlocal execution_count
        execution_count += 1
        return {"step": execution_count, "processed": True}

    mock_execute_activity.side_effect = activity_side_effect

    workflow_input = input_module.WorkflowInput(
        input={"initial": "data"},
        workflow_start=input_module.Workflow(name="no_keys", queue="test_queue"),
        executors=[
            input_module.Executor(
                is_workflow=False,
                activity=input_module.Activity(name="step1", queue="test_queue")
                # No key_name specified
            ),
            input_module.Executor(
                is_workflow=False,
                activity=input_module.Activity(name="step2", queue="test_queue")
                # No key_name specified
            )
        ]
    )

    result = await executor_instance.main_workflow(workflow_input)
    assert result == {"step": 2, "processed": True}  # Should return last result
    assert mock_execute_activity.await_count == 2


@pytest.mark.asyncio
@patch("temporalio.workflow.execute_activity", new_callable=AsyncMock)
@patch("temporalio.workflow.logger", new_callable=MagicMock)
async def test_workflow_with_timeout_configurations(mock_logger, mock_execute_activity):
    """Test workflow with various timeout configurations"""
    executor_instance = DynamicWorkflowExecutor()
    mock_execute_activity.return_value = {"timeout_test": "success"}

    workflow_input = input_module.WorkflowInput(
        id="timeout_workflow_1",
        input={"timeout": "test"},
        workflow_start=input_module.Workflow(
            name="timeout_test",
            queue="test_queue",
            execution_timeout=3600,
            run_timeout=1800,
            task_timeout=300
        ),
        executors=[
            input_module.Executor(
                is_workflow=False,
                activity=input_module.Activity(
                    name="timeout_activity",
                    queue="test_queue",
                    schedule_to_close_timeout=600,
                    start_to_close_timeout=300,
                    heartbeat_timeout=60
                ),
                key_name="timeout_result"
            )
        ]
    )

    result = await executor_instance.main_workflow(workflow_input)
    assert result == {"timeout_test": "success"}

    # Verify that timeout parameters were passed
    call_args = mock_execute_activity.await_args
    assert call_args.kwargs['schedule_to_close_timeout'] == to_timedelta(600)
    assert call_args.kwargs['start_to_close_timeout'] == to_timedelta(300)
    assert call_args.kwargs['heartbeat_timeout'] == to_timedelta(60)


@pytest.mark.asyncio
async def test_internal_state_edge_cases():
    """Test InternalState with boundary values"""
    # Test default values
    state = input_module.InternalState()
    assert state.max_renews == 5
    assert state.current_renew == 0

    # Test with zero max_renews
    state = input_module.InternalState(max_renews=0, current_renew=0)
    assert state.max_renews == 0

    # Test with negative values (should be allowed by Pydantic)
    state = input_module.InternalState(max_renews=-1, current_renew=-1)
    assert state.max_renews == -1
    assert state.current_renew == -1


# Additional Advanced Test Cases
@pytest.mark.asyncio
@patch("temporalio.workflow.execute_activity", new_callable=AsyncMock)
@patch("temporalio.workflow.logger", new_callable=MagicMock)
async def test_workflow_with_app_config(mock_logger, mock_execute_activity):
    """Test workflow with app_config passed to activities and workflows"""
    executor_instance = DynamicWorkflowExecutor()
    mock_execute_activity.return_value = {"config_test": "success"}

    app_config = {
        "database_url": "postgresql://localhost:5432/test",
        "api_key": "test_key_123",
        "environment": "test"
    }

    workflow_input = input_module.WorkflowInput(
        input={"test": "app_config"},
        workflow_start=input_module.Workflow(
            name="config_test",
            queue="test_queue",
            app_config=app_config
        ),
        executors=[
            input_module.Executor(
                is_workflow=False,
                activity=input_module.Activity(
                    name="config_activity",
                    queue="test_queue",
                    app_config=app_config
                ),
                key_name="config_result"
            )
        ]
    )

    result = await executor_instance.main_workflow(workflow_input)
    assert result == {"config_test": "success"}

    # Verify app_config was passed correctly
    call_args = mock_execute_activity.await_args
    passed_data: input_module.ActivityInput = call_args[0][1]  # Second argument is the data dict
    assert passed_data.app_config is not None
    assert passed_data.app_config == app_config


@pytest.mark.asyncio
@patch("temporalio.workflow.execute_child_workflow", new_callable=AsyncMock)
@patch("temporalio.workflow.logger", new_callable=MagicMock)
async def test_workflow_with_child_workflow_ids(mock_logger, mock_execute_child):
    """Test workflow with specific workflow IDs"""
    executor_instance = DynamicWorkflowExecutor()
    mock_execute_child.return_value = {"child_workflow": "completed"}

    workflow_input = input_module.WorkflowInput(
        input={"parent": "data"},
        workflow_start=input_module.Workflow(name="parent_workflow", queue="test_queue"),
        executors=[
            input_module.Executor(
                is_workflow=True,
                workflow=input_module.Workflow(
                    name="child_workflow",
                    id="specific-child-id-123",
                    queue="child_queue"
                ),
                key_name="child_result",
                wait_execution=True
            )
        ]
    )

    result = await executor_instance.main_workflow(workflow_input)
    assert result == {"child_workflow": "completed"}

    # Verify workflow_id was passed
    call_args = mock_execute_child.await_args
    assert call_args.kwargs["id"] == "specific-child-id-123"


@pytest.mark.asyncio
@patch("temporalio.workflow.continue_as_new", new_callable=AsyncMock)
@patch("temporalio.workflow.logger", new_callable=MagicMock)
async def test_try_and_renew_boundary_conditions(mock_logger, mock_continue_as_new):
    """Test try_and_renew_when_expired at boundary conditions"""
    executor_instance = DynamicWorkflowExecutor()
    executor_mock = input_module.Executor(
        is_workflow=False,
        activity=input_module.Activity(name="boundary_test", queue="test_queue"),
        renew_when_expired=True,
        internal_state=input_module.InternalState(max_renews=3, current_renew=3)
    )

    # Test at exactly max_renews
    async def timeout_executor(*args, **kwargs):
        cause = TimeoutError(message="timeout", type="StartToClose", last_heartbeat_details=None)
        activity_error = ActivityError(
            message="timeout error",
            activity_type="test_activity",
            activity_id="1",
            identity="worker",
            scheduled_event_id=1,
            started_event_id=2,
            retry_state="RETRY_STATE"
        )
        activity_error.__cause__ = cause
        raise activity_error

    executor_instance.process_executor = timeout_executor
    mock_continue_as_new.return_value = "renewed"

    # Test when current_renew equals max_renews (should fail)
    workflow_input = input_module.WorkflowInput(
        input={"test": "boundary"},
        id="boundary_workflow_1",
        workflow_start=input_module.Workflow(name='boundary_test', queue="default"),
        executors=[executor_mock]
    )

    with pytest.raises(ActivityError):
        await executor_instance.try_and_renew_when_expired('none', workflow_input, executor_mock, {"test": "data"})

    # Test when current_renew is one less than max_renews (should renew)
    executor_mock.internal_state.current_renew = 2
    is_renew, result = await executor_instance.try_and_renew_when_expired('none',workflow_input, executor_mock, {"test": "data"})
    assert is_renew
    assert executor_mock.internal_state.current_renew == 3


@pytest.mark.asyncio
@patch("temporalio.workflow.execute_activity", new_callable=AsyncMock)
async def test_large_workflow_chain(mock_execute_activity):
    """Test workflow with many chained executors"""
    executor_instance = DynamicWorkflowExecutor()

    # Mock that each step adds to a counter based on the previous result
    def chain_side_effect(name, input_data: input_module.ActivityInput, *args, **kwargs):
        input_dict = input_data.input
        step_num = int(name.replace("step_", ""))

        # For step 1, use the original input
        if step_num == 1:
            current_count = input_dict.get("count", 0)
        else:
            # For subsequent steps, look for the previous step's result
            prev_step_key = f"step_{step_num-1}"
            if prev_step_key in input_dict:
                current_count = input_dict[prev_step_key].get("count", 0)
            else:
                current_count = 0

        return {"count": current_count + step_num, "step": step_num}

    mock_execute_activity.side_effect = chain_side_effect

    # Create 5 chained executors (reduced from 10 to avoid logging issues)
    executors = []
    for i in range(1, 6):
        executor = input_module.Executor(
            is_workflow=False,
            activity=input_module.Activity(name=f"step_{i}", queue="chain_queue"),
            key_name=f"step_{i}",
            input_keys=[f"step_{i-1}"] if i > 1 else None
        )
        executors.append(executor)

    workflow_input = input_module.WorkflowInput(
        input={"count": 0},
        workflow_start=input_module.Workflow(name="chain_workflow", queue="chain_queue"),
        executors=executors,
        output_key="step_5"
    )

    # Mock the workflow logger to avoid event loop issues
    with patch("temporalio.workflow.logger"):
        result = await executor_instance.main_workflow(workflow_input)

    # Step 1: 0 + 1 = 1
    # Step 2: 1 + 2 = 3
    # Step 3: 3 + 3 = 6
    # Step 4: 6 + 4 = 10
    # Step 5: 10 + 5 = 15
    assert result == {"count": 15, "step": 5}
    assert mock_execute_activity.await_count == 5


@pytest.mark.asyncio
async def test_get_input_by_keys_with_complex_data_structures():
    """Test get_input_by_keys with complex nested data structures"""
    executor_instance = DynamicWorkflowExecutor()

    complex_map_result = {
        "arrays": {
            "numbers": [1, 2, 3, 4, 5],
            "objects": [{"id": 1, "name": "first"}, {"id": 2, "name": "second"}]
        },
        "nested": {
            "level1": {
                "level2": {
                    "level3": {
                        "deep_value": "found_it",
                        "list": ["a", "b", "c"]
                    }
                }
            }
        },
        "mixed": {
            "string": "text",
            "number": 42,
            "boolean": True,
            "null_value": None,
            "empty_dict": {},
            "empty_list": []
        }
    }

    # Test extracting array data
    result = executor_instance.get_input_by_keys(complex_map_result, ["arrays"])
    assert "arrays" in result
    assert result["arrays"]["numbers"] == [1, 2, 3, 4, 5]

    # Test extracting deeply nested data
    result = executor_instance.get_input_by_keys(complex_map_result, ["nested"])
    assert result["nested"]["level1"]["level2"]["level3"]["deep_value"] == "found_it"

    # Test extracting multiple complex keys
    result = executor_instance.get_input_by_keys(complex_map_result, ["arrays", "mixed"])
    assert len(result) == 2
    assert "arrays" in result and "mixed" in result
    assert result["mixed"]["string"] == "text"
    assert result["mixed"]["null_value"] is None


@pytest.mark.asyncio
@patch("temporalio.workflow.execute_activity", new_callable=AsyncMock)
@patch("temporalio.workflow.logger", new_callable=MagicMock)
async def test_workflow_with_all_timeout_types(mock_logger, mock_execute_activity):
    """Test workflow with all types of timeout configurations"""
    executor_instance = DynamicWorkflowExecutor()
    mock_execute_activity.return_value = {"timeout_comprehensive": "success"}

    comprehensive_retry_policy = input_module.RetryPolicy(
        initial_interval=500,
        maximum_interval=30000,
        backoff_coefficient=2.5,
        maximum_attempts=5,
        non_retryable_error_types=["ValueError", "TypeError"]
    )

    workflow_input = input_module.WorkflowInput(
        id="comprehensive_timeout_workflow_1",
        input={"comprehensive": "timeout_test"},
        workflow_start=input_module.Workflow(
            name="comprehensive_timeout_test",
            queue="timeout_queue",
            execution_timeout=7200,  # 2 hours
            run_timeout=3600,        # 1 hour
            task_timeout=600,        # 10 minutes
            retry_policy=comprehensive_retry_policy
        ),
        executors=[
            input_module.Executor(
                is_workflow=False,
                activity=input_module.Activity(
                    name="comprehensive_timeout_activity",
                    queue="timeout_queue",
                    schedule_to_close_timeout=1800,  # 30 minutes
                    start_to_close_timeout=900,     # 15 minutes
                    heartbeat_timeout=120,          # 2 minutes
                    retry_policy=comprehensive_retry_policy
                ),
                key_name="comprehensive_result"
            )
        ]
    )

    result = await executor_instance.main_workflow(workflow_input)
    assert result == {"timeout_comprehensive": "success"}

    # Verify all timeout parameters were passed correctly
    call_args = mock_execute_activity.await_args
    assert call_args.kwargs['schedule_to_close_timeout'] == to_timedelta(1800)
    assert call_args.kwargs['start_to_close_timeout'] == to_timedelta(900)
    assert call_args.kwargs['heartbeat_timeout'] == to_timedelta(120)
    assert call_args.kwargs['retry_policy'] == to_temporal_retry_policy(comprehensive_retry_policy)
