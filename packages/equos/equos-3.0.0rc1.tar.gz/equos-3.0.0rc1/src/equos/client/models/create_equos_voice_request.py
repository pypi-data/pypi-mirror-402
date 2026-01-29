from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.create_equos_voice_request_identity import CreateEquosVoiceRequestIdentity
from ..types import UNSET, Unset

T = TypeVar("T", bound="CreateEquosVoiceRequest")


@_attrs_define
class CreateEquosVoiceRequest:
    """
    Attributes:
        identity (CreateEquosVoiceRequestIdentity):
        client (None | str | Unset): Client identifier associated with the voice. This is useful to segment resources by
            client.
        instructions (None | str | Unset): Instructions for the voice such as tone, rythm, etc.
    """

    identity: CreateEquosVoiceRequestIdentity
    client: None | str | Unset = UNSET
    instructions: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        identity = self.identity.value

        client: None | str | Unset
        if isinstance(self.client, Unset):
            client = UNSET
        else:
            client = self.client

        instructions: None | str | Unset
        if isinstance(self.instructions, Unset):
            instructions = UNSET
        else:
            instructions = self.instructions

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "identity": identity,
            }
        )
        if client is not UNSET:
            field_dict["client"] = client
        if instructions is not UNSET:
            field_dict["instructions"] = instructions

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        identity = CreateEquosVoiceRequestIdentity(d.pop("identity"))

        def _parse_client(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        client = _parse_client(d.pop("client", UNSET))

        def _parse_instructions(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        instructions = _parse_instructions(d.pop("instructions", UNSET))

        create_equos_voice_request = cls(
            identity=identity,
            client=client,
            instructions=instructions,
        )

        create_equos_voice_request.additional_properties = d
        return create_equos_voice_request

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
