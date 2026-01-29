from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.create_equos_conversation_request_prompt_template_vars_type_0 import (
        CreateEquosConversationRequestPromptTemplateVarsType0,
    )
    from ..models.equos_conversation_host import EquosConversationHost
    from ..models.equos_participant_identity import EquosParticipantIdentity


T = TypeVar("T", bound="CreateEquosConversationRequest")


@_attrs_define
class CreateEquosConversationRequest:
    """
    Attributes:
        name (str):
        character_id (str):
        client (None | str | Unset):
        host (EquosConversationHost | None | Unset):
        remote_agent (EquosParticipantIdentity | None | Unset):
        consumer (EquosParticipantIdentity | None | Unset):
        max_seconds (float | None | Unset):
        prompt_ctx (None | str | Unset):
        prompt_template_vars (CreateEquosConversationRequestPromptTemplateVarsType0 | None | Unset):
    """

    name: str
    character_id: str
    client: None | str | Unset = UNSET
    host: EquosConversationHost | None | Unset = UNSET
    remote_agent: EquosParticipantIdentity | None | Unset = UNSET
    consumer: EquosParticipantIdentity | None | Unset = UNSET
    max_seconds: float | None | Unset = UNSET
    prompt_ctx: None | str | Unset = UNSET
    prompt_template_vars: CreateEquosConversationRequestPromptTemplateVarsType0 | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.create_equos_conversation_request_prompt_template_vars_type_0 import (
            CreateEquosConversationRequestPromptTemplateVarsType0,
        )
        from ..models.equos_conversation_host import EquosConversationHost
        from ..models.equos_participant_identity import EquosParticipantIdentity

        name = self.name

        character_id = self.character_id

        client: None | str | Unset
        if isinstance(self.client, Unset):
            client = UNSET
        else:
            client = self.client

        host: dict[str, Any] | None | Unset
        if isinstance(self.host, Unset):
            host = UNSET
        elif isinstance(self.host, EquosConversationHost):
            host = self.host.to_dict()
        else:
            host = self.host

        remote_agent: dict[str, Any] | None | Unset
        if isinstance(self.remote_agent, Unset):
            remote_agent = UNSET
        elif isinstance(self.remote_agent, EquosParticipantIdentity):
            remote_agent = self.remote_agent.to_dict()
        else:
            remote_agent = self.remote_agent

        consumer: dict[str, Any] | None | Unset
        if isinstance(self.consumer, Unset):
            consumer = UNSET
        elif isinstance(self.consumer, EquosParticipantIdentity):
            consumer = self.consumer.to_dict()
        else:
            consumer = self.consumer

        max_seconds: float | None | Unset
        if isinstance(self.max_seconds, Unset):
            max_seconds = UNSET
        else:
            max_seconds = self.max_seconds

        prompt_ctx: None | str | Unset
        if isinstance(self.prompt_ctx, Unset):
            prompt_ctx = UNSET
        else:
            prompt_ctx = self.prompt_ctx

        prompt_template_vars: dict[str, Any] | None | Unset
        if isinstance(self.prompt_template_vars, Unset):
            prompt_template_vars = UNSET
        elif isinstance(self.prompt_template_vars, CreateEquosConversationRequestPromptTemplateVarsType0):
            prompt_template_vars = self.prompt_template_vars.to_dict()
        else:
            prompt_template_vars = self.prompt_template_vars

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "characterId": character_id,
            }
        )
        if client is not UNSET:
            field_dict["client"] = client
        if host is not UNSET:
            field_dict["host"] = host
        if remote_agent is not UNSET:
            field_dict["remoteAgent"] = remote_agent
        if consumer is not UNSET:
            field_dict["consumer"] = consumer
        if max_seconds is not UNSET:
            field_dict["maxSeconds"] = max_seconds
        if prompt_ctx is not UNSET:
            field_dict["promptCtx"] = prompt_ctx
        if prompt_template_vars is not UNSET:
            field_dict["promptTemplateVars"] = prompt_template_vars

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.create_equos_conversation_request_prompt_template_vars_type_0 import (
            CreateEquosConversationRequestPromptTemplateVarsType0,
        )
        from ..models.equos_conversation_host import EquosConversationHost
        from ..models.equos_participant_identity import EquosParticipantIdentity

        d = dict(src_dict)
        name = d.pop("name")

        character_id = d.pop("characterId")

        def _parse_client(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        client = _parse_client(d.pop("client", UNSET))

        def _parse_host(data: object) -> EquosConversationHost | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                host_type_1 = EquosConversationHost.from_dict(data)

                return host_type_1
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(EquosConversationHost | None | Unset, data)

        host = _parse_host(d.pop("host", UNSET))

        def _parse_remote_agent(data: object) -> EquosParticipantIdentity | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                remote_agent_type_1 = EquosParticipantIdentity.from_dict(data)

                return remote_agent_type_1
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(EquosParticipantIdentity | None | Unset, data)

        remote_agent = _parse_remote_agent(d.pop("remoteAgent", UNSET))

        def _parse_consumer(data: object) -> EquosParticipantIdentity | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                consumer_type_1 = EquosParticipantIdentity.from_dict(data)

                return consumer_type_1
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(EquosParticipantIdentity | None | Unset, data)

        consumer = _parse_consumer(d.pop("consumer", UNSET))

        def _parse_max_seconds(data: object) -> float | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(float | None | Unset, data)

        max_seconds = _parse_max_seconds(d.pop("maxSeconds", UNSET))

        def _parse_prompt_ctx(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        prompt_ctx = _parse_prompt_ctx(d.pop("promptCtx", UNSET))

        def _parse_prompt_template_vars(
            data: object,
        ) -> CreateEquosConversationRequestPromptTemplateVarsType0 | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                prompt_template_vars_type_0 = CreateEquosConversationRequestPromptTemplateVarsType0.from_dict(data)

                return prompt_template_vars_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(CreateEquosConversationRequestPromptTemplateVarsType0 | None | Unset, data)

        prompt_template_vars = _parse_prompt_template_vars(d.pop("promptTemplateVars", UNSET))

        create_equos_conversation_request = cls(
            name=name,
            character_id=character_id,
            client=client,
            host=host,
            remote_agent=remote_agent,
            consumer=consumer,
            max_seconds=max_seconds,
            prompt_ctx=prompt_ctx,
            prompt_template_vars=prompt_template_vars,
        )

        create_equos_conversation_request.additional_properties = d
        return create_equos_conversation_request

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
