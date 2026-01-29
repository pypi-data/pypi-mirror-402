from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.equos_conversation_with_character import EquosConversationWithCharacter


T = TypeVar("T", bound="CreateEquosConversationResponse")


@_attrs_define
class CreateEquosConversationResponse:
    """
    Attributes:
        conversation (EquosConversationWithCharacter):
        remote_agent_access_token (None | str | Unset):
        consumer_access_token (None | str | Unset):
    """

    conversation: EquosConversationWithCharacter
    remote_agent_access_token: None | str | Unset = UNSET
    consumer_access_token: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        conversation = self.conversation.to_dict()

        remote_agent_access_token: None | str | Unset
        if isinstance(self.remote_agent_access_token, Unset):
            remote_agent_access_token = UNSET
        else:
            remote_agent_access_token = self.remote_agent_access_token

        consumer_access_token: None | str | Unset
        if isinstance(self.consumer_access_token, Unset):
            consumer_access_token = UNSET
        else:
            consumer_access_token = self.consumer_access_token

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "conversation": conversation,
            }
        )
        if remote_agent_access_token is not UNSET:
            field_dict["remoteAgentAccessToken"] = remote_agent_access_token
        if consumer_access_token is not UNSET:
            field_dict["consumerAccessToken"] = consumer_access_token

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.equos_conversation_with_character import EquosConversationWithCharacter

        d = dict(src_dict)
        conversation = EquosConversationWithCharacter.from_dict(d.pop("conversation"))

        def _parse_remote_agent_access_token(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        remote_agent_access_token = _parse_remote_agent_access_token(d.pop("remoteAgentAccessToken", UNSET))

        def _parse_consumer_access_token(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        consumer_access_token = _parse_consumer_access_token(d.pop("consumerAccessToken", UNSET))

        create_equos_conversation_response = cls(
            conversation=conversation,
            remote_agent_access_token=remote_agent_access_token,
            consumer_access_token=consumer_access_token,
        )

        create_equos_conversation_response.additional_properties = d
        return create_equos_conversation_response

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
