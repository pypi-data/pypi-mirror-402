from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.post_api_v1_datasets_by_dataset_slug_items_body_items_item_content_conversation_context import (
        PostApiV1DatasetsByDatasetSlugItemsBodyItemsItemContentConversationContext,
    )
    from ..models.post_api_v1_datasets_by_dataset_slug_items_body_items_item_content_custom_attributes import (
        PostApiV1DatasetsByDatasetSlugItemsBodyItemsItemContentCustomAttributes,
    )
    from ..models.post_api_v1_datasets_by_dataset_slug_items_body_items_item_content_evaluation_context import (
        PostApiV1DatasetsByDatasetSlugItemsBodyItemsItemContentEvaluationContext,
    )
    from ..models.post_api_v1_datasets_by_dataset_slug_items_body_items_item_content_parameters_passed import (
        PostApiV1DatasetsByDatasetSlugItemsBodyItemsItemContentParametersPassed,
    )
    from ..models.post_api_v1_datasets_by_dataset_slug_items_body_items_item_content_trace_data import (
        PostApiV1DatasetsByDatasetSlugItemsBodyItemsItemContentTraceData,
    )


T = TypeVar("T", bound="PostApiV1DatasetsByDatasetSlugItemsBodyItemsItemContent")


@_attrs_define
class PostApiV1DatasetsByDatasetSlugItemsBodyItemsItemContent:
    """
    Attributes:
        agent_name (str | Unset):
        agent_role (str | Unset):
        agent_task (str | Unset):
        agent_response (str | Unset):
        system_prompt (str | Unset):
        user_id (str | Unset):
        session_id (str | Unset):
        turn_id (str | Unset):
        ground_truth (str | Unset):
        expected_tool_call (str | Unset):
        tools_available (list[Any] | Unset):
        tool_calls (list[Any] | Unset):
        tool_call_results (list[Any] | Unset):
        parameters_passed (PostApiV1DatasetsByDatasetSlugItemsBodyItemsItemContentParametersPassed | Unset):
        retrieval_query (list[Any] | Unset):
        retrieved_context (list[Any] | Unset):
        exit_status (str | Unset):
        agent_exit (str | Unset):
        trace_data (PostApiV1DatasetsByDatasetSlugItemsBodyItemsItemContentTraceData | Unset):
        conversation_id (str | Unset):
        speaker (str | Unset):
        message (str | Unset):
        conversation_context (PostApiV1DatasetsByDatasetSlugItemsBodyItemsItemContentConversationContext | Unset):
        input_text (str | Unset):
        output_text (str | Unset):
        expected_output (str | Unset):
        evaluation_context (PostApiV1DatasetsByDatasetSlugItemsBodyItemsItemContentEvaluationContext | Unset):
        criteria (str | Unset):
        quality_score (float | Unset):
        validation_status (str | Unset):
        validation_errors (list[Any] | Unset):
        tags (list[Any] | Unset):
        custom_attributes (PostApiV1DatasetsByDatasetSlugItemsBodyItemsItemContentCustomAttributes | Unset):
    """

    agent_name: str | Unset = UNSET
    agent_role: str | Unset = UNSET
    agent_task: str | Unset = UNSET
    agent_response: str | Unset = UNSET
    system_prompt: str | Unset = UNSET
    user_id: str | Unset = UNSET
    session_id: str | Unset = UNSET
    turn_id: str | Unset = UNSET
    ground_truth: str | Unset = UNSET
    expected_tool_call: str | Unset = UNSET
    tools_available: list[Any] | Unset = UNSET
    tool_calls: list[Any] | Unset = UNSET
    tool_call_results: list[Any] | Unset = UNSET
    parameters_passed: PostApiV1DatasetsByDatasetSlugItemsBodyItemsItemContentParametersPassed | Unset = UNSET
    retrieval_query: list[Any] | Unset = UNSET
    retrieved_context: list[Any] | Unset = UNSET
    exit_status: str | Unset = UNSET
    agent_exit: str | Unset = UNSET
    trace_data: PostApiV1DatasetsByDatasetSlugItemsBodyItemsItemContentTraceData | Unset = UNSET
    conversation_id: str | Unset = UNSET
    speaker: str | Unset = UNSET
    message: str | Unset = UNSET
    conversation_context: PostApiV1DatasetsByDatasetSlugItemsBodyItemsItemContentConversationContext | Unset = UNSET
    input_text: str | Unset = UNSET
    output_text: str | Unset = UNSET
    expected_output: str | Unset = UNSET
    evaluation_context: PostApiV1DatasetsByDatasetSlugItemsBodyItemsItemContentEvaluationContext | Unset = UNSET
    criteria: str | Unset = UNSET
    quality_score: float | Unset = UNSET
    validation_status: str | Unset = UNSET
    validation_errors: list[Any] | Unset = UNSET
    tags: list[Any] | Unset = UNSET
    custom_attributes: PostApiV1DatasetsByDatasetSlugItemsBodyItemsItemContentCustomAttributes | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        agent_name = self.agent_name

        agent_role = self.agent_role

        agent_task = self.agent_task

        agent_response = self.agent_response

        system_prompt = self.system_prompt

        user_id = self.user_id

        session_id = self.session_id

        turn_id = self.turn_id

        ground_truth = self.ground_truth

        expected_tool_call = self.expected_tool_call

        tools_available: list[Any] | Unset = UNSET
        if not isinstance(self.tools_available, Unset):
            tools_available = self.tools_available

        tool_calls: list[Any] | Unset = UNSET
        if not isinstance(self.tool_calls, Unset):
            tool_calls = self.tool_calls

        tool_call_results: list[Any] | Unset = UNSET
        if not isinstance(self.tool_call_results, Unset):
            tool_call_results = self.tool_call_results

        parameters_passed: dict[str, Any] | Unset = UNSET
        if not isinstance(self.parameters_passed, Unset):
            parameters_passed = self.parameters_passed.to_dict()

        retrieval_query: list[Any] | Unset = UNSET
        if not isinstance(self.retrieval_query, Unset):
            retrieval_query = self.retrieval_query

        retrieved_context: list[Any] | Unset = UNSET
        if not isinstance(self.retrieved_context, Unset):
            retrieved_context = self.retrieved_context

        exit_status = self.exit_status

        agent_exit = self.agent_exit

        trace_data: dict[str, Any] | Unset = UNSET
        if not isinstance(self.trace_data, Unset):
            trace_data = self.trace_data.to_dict()

        conversation_id = self.conversation_id

        speaker = self.speaker

        message = self.message

        conversation_context: dict[str, Any] | Unset = UNSET
        if not isinstance(self.conversation_context, Unset):
            conversation_context = self.conversation_context.to_dict()

        input_text = self.input_text

        output_text = self.output_text

        expected_output = self.expected_output

        evaluation_context: dict[str, Any] | Unset = UNSET
        if not isinstance(self.evaluation_context, Unset):
            evaluation_context = self.evaluation_context.to_dict()

        criteria = self.criteria

        quality_score = self.quality_score

        validation_status = self.validation_status

        validation_errors: list[Any] | Unset = UNSET
        if not isinstance(self.validation_errors, Unset):
            validation_errors = self.validation_errors

        tags: list[Any] | Unset = UNSET
        if not isinstance(self.tags, Unset):
            tags = self.tags

        custom_attributes: dict[str, Any] | Unset = UNSET
        if not isinstance(self.custom_attributes, Unset):
            custom_attributes = self.custom_attributes.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if agent_name is not UNSET:
            field_dict["agent_name"] = agent_name
        if agent_role is not UNSET:
            field_dict["agent_role"] = agent_role
        if agent_task is not UNSET:
            field_dict["agent_task"] = agent_task
        if agent_response is not UNSET:
            field_dict["agent_response"] = agent_response
        if system_prompt is not UNSET:
            field_dict["system_prompt"] = system_prompt
        if user_id is not UNSET:
            field_dict["user_id"] = user_id
        if session_id is not UNSET:
            field_dict["session_id"] = session_id
        if turn_id is not UNSET:
            field_dict["turn_id"] = turn_id
        if ground_truth is not UNSET:
            field_dict["ground_truth"] = ground_truth
        if expected_tool_call is not UNSET:
            field_dict["expected_tool_call"] = expected_tool_call
        if tools_available is not UNSET:
            field_dict["tools_available"] = tools_available
        if tool_calls is not UNSET:
            field_dict["tool_calls"] = tool_calls
        if tool_call_results is not UNSET:
            field_dict["tool_call_results"] = tool_call_results
        if parameters_passed is not UNSET:
            field_dict["parameters_passed"] = parameters_passed
        if retrieval_query is not UNSET:
            field_dict["retrieval_query"] = retrieval_query
        if retrieved_context is not UNSET:
            field_dict["retrieved_context"] = retrieved_context
        if exit_status is not UNSET:
            field_dict["exit_status"] = exit_status
        if agent_exit is not UNSET:
            field_dict["agent_exit"] = agent_exit
        if trace_data is not UNSET:
            field_dict["trace_data"] = trace_data
        if conversation_id is not UNSET:
            field_dict["conversation_id"] = conversation_id
        if speaker is not UNSET:
            field_dict["speaker"] = speaker
        if message is not UNSET:
            field_dict["message"] = message
        if conversation_context is not UNSET:
            field_dict["conversation_context"] = conversation_context
        if input_text is not UNSET:
            field_dict["input_text"] = input_text
        if output_text is not UNSET:
            field_dict["output_text"] = output_text
        if expected_output is not UNSET:
            field_dict["expected_output"] = expected_output
        if evaluation_context is not UNSET:
            field_dict["evaluation_context"] = evaluation_context
        if criteria is not UNSET:
            field_dict["criteria"] = criteria
        if quality_score is not UNSET:
            field_dict["quality_score"] = quality_score
        if validation_status is not UNSET:
            field_dict["validation_status"] = validation_status
        if validation_errors is not UNSET:
            field_dict["validation_errors"] = validation_errors
        if tags is not UNSET:
            field_dict["tags"] = tags
        if custom_attributes is not UNSET:
            field_dict["custom_attributes"] = custom_attributes

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.post_api_v1_datasets_by_dataset_slug_items_body_items_item_content_conversation_context import (
            PostApiV1DatasetsByDatasetSlugItemsBodyItemsItemContentConversationContext,
        )
        from ..models.post_api_v1_datasets_by_dataset_slug_items_body_items_item_content_custom_attributes import (
            PostApiV1DatasetsByDatasetSlugItemsBodyItemsItemContentCustomAttributes,
        )
        from ..models.post_api_v1_datasets_by_dataset_slug_items_body_items_item_content_evaluation_context import (
            PostApiV1DatasetsByDatasetSlugItemsBodyItemsItemContentEvaluationContext,
        )
        from ..models.post_api_v1_datasets_by_dataset_slug_items_body_items_item_content_parameters_passed import (
            PostApiV1DatasetsByDatasetSlugItemsBodyItemsItemContentParametersPassed,
        )
        from ..models.post_api_v1_datasets_by_dataset_slug_items_body_items_item_content_trace_data import (
            PostApiV1DatasetsByDatasetSlugItemsBodyItemsItemContentTraceData,
        )

        d = dict(src_dict)
        agent_name = d.pop("agent_name", UNSET)

        agent_role = d.pop("agent_role", UNSET)

        agent_task = d.pop("agent_task", UNSET)

        agent_response = d.pop("agent_response", UNSET)

        system_prompt = d.pop("system_prompt", UNSET)

        user_id = d.pop("user_id", UNSET)

        session_id = d.pop("session_id", UNSET)

        turn_id = d.pop("turn_id", UNSET)

        ground_truth = d.pop("ground_truth", UNSET)

        expected_tool_call = d.pop("expected_tool_call", UNSET)

        tools_available = cast(list[Any], d.pop("tools_available", UNSET))

        tool_calls = cast(list[Any], d.pop("tool_calls", UNSET))

        tool_call_results = cast(list[Any], d.pop("tool_call_results", UNSET))

        _parameters_passed = d.pop("parameters_passed", UNSET)
        parameters_passed: PostApiV1DatasetsByDatasetSlugItemsBodyItemsItemContentParametersPassed | Unset
        if isinstance(_parameters_passed, Unset):
            parameters_passed = UNSET
        else:
            parameters_passed = PostApiV1DatasetsByDatasetSlugItemsBodyItemsItemContentParametersPassed.from_dict(
                _parameters_passed
            )

        retrieval_query = cast(list[Any], d.pop("retrieval_query", UNSET))

        retrieved_context = cast(list[Any], d.pop("retrieved_context", UNSET))

        exit_status = d.pop("exit_status", UNSET)

        agent_exit = d.pop("agent_exit", UNSET)

        _trace_data = d.pop("trace_data", UNSET)
        trace_data: PostApiV1DatasetsByDatasetSlugItemsBodyItemsItemContentTraceData | Unset
        if isinstance(_trace_data, Unset):
            trace_data = UNSET
        else:
            trace_data = PostApiV1DatasetsByDatasetSlugItemsBodyItemsItemContentTraceData.from_dict(_trace_data)

        conversation_id = d.pop("conversation_id", UNSET)

        speaker = d.pop("speaker", UNSET)

        message = d.pop("message", UNSET)

        _conversation_context = d.pop("conversation_context", UNSET)
        conversation_context: PostApiV1DatasetsByDatasetSlugItemsBodyItemsItemContentConversationContext | Unset
        if isinstance(_conversation_context, Unset):
            conversation_context = UNSET
        else:
            conversation_context = PostApiV1DatasetsByDatasetSlugItemsBodyItemsItemContentConversationContext.from_dict(
                _conversation_context
            )

        input_text = d.pop("input_text", UNSET)

        output_text = d.pop("output_text", UNSET)

        expected_output = d.pop("expected_output", UNSET)

        _evaluation_context = d.pop("evaluation_context", UNSET)
        evaluation_context: PostApiV1DatasetsByDatasetSlugItemsBodyItemsItemContentEvaluationContext | Unset
        if isinstance(_evaluation_context, Unset):
            evaluation_context = UNSET
        else:
            evaluation_context = PostApiV1DatasetsByDatasetSlugItemsBodyItemsItemContentEvaluationContext.from_dict(
                _evaluation_context
            )

        criteria = d.pop("criteria", UNSET)

        quality_score = d.pop("quality_score", UNSET)

        validation_status = d.pop("validation_status", UNSET)

        validation_errors = cast(list[Any], d.pop("validation_errors", UNSET))

        tags = cast(list[Any], d.pop("tags", UNSET))

        _custom_attributes = d.pop("custom_attributes", UNSET)
        custom_attributes: PostApiV1DatasetsByDatasetSlugItemsBodyItemsItemContentCustomAttributes | Unset
        if isinstance(_custom_attributes, Unset):
            custom_attributes = UNSET
        else:
            custom_attributes = PostApiV1DatasetsByDatasetSlugItemsBodyItemsItemContentCustomAttributes.from_dict(
                _custom_attributes
            )

        post_api_v1_datasets_by_dataset_slug_items_body_items_item_content = cls(
            agent_name=agent_name,
            agent_role=agent_role,
            agent_task=agent_task,
            agent_response=agent_response,
            system_prompt=system_prompt,
            user_id=user_id,
            session_id=session_id,
            turn_id=turn_id,
            ground_truth=ground_truth,
            expected_tool_call=expected_tool_call,
            tools_available=tools_available,
            tool_calls=tool_calls,
            tool_call_results=tool_call_results,
            parameters_passed=parameters_passed,
            retrieval_query=retrieval_query,
            retrieved_context=retrieved_context,
            exit_status=exit_status,
            agent_exit=agent_exit,
            trace_data=trace_data,
            conversation_id=conversation_id,
            speaker=speaker,
            message=message,
            conversation_context=conversation_context,
            input_text=input_text,
            output_text=output_text,
            expected_output=expected_output,
            evaluation_context=evaluation_context,
            criteria=criteria,
            quality_score=quality_score,
            validation_status=validation_status,
            validation_errors=validation_errors,
            tags=tags,
            custom_attributes=custom_attributes,
        )

        post_api_v1_datasets_by_dataset_slug_items_body_items_item_content.additional_properties = d
        return post_api_v1_datasets_by_dataset_slug_items_body_items_item_content

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
