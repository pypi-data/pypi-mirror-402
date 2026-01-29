from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.equos_voice_identity import EquosVoiceIdentity
from ..types import UNSET, Unset

T = TypeVar("T", bound="EquosVoice")


@_attrs_define
class EquosVoice:
    """
    Attributes:
        id (str):
        organization_id (str):
        identity (EquosVoiceIdentity):
        created_at (datetime.datetime):
        updated_at (datetime.datetime):
        client (None | str | Unset):
        instructions (None | str | Unset):
    """

    id: str
    organization_id: str
    identity: EquosVoiceIdentity
    created_at: datetime.datetime
    updated_at: datetime.datetime
    client: None | str | Unset = UNSET
    instructions: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        organization_id = self.organization_id

        identity = self.identity.value

        created_at = self.created_at.isoformat()

        updated_at = self.updated_at.isoformat()

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
                "id": id,
                "organizationId": organization_id,
                "identity": identity,
                "createdAt": created_at,
                "updatedAt": updated_at,
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
        id = d.pop("id")

        organization_id = d.pop("organizationId")

        identity = EquosVoiceIdentity(d.pop("identity"))

        created_at = isoparse(d.pop("createdAt"))

        updated_at = isoparse(d.pop("updatedAt"))

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

        equos_voice = cls(
            id=id,
            organization_id=organization_id,
            identity=identity,
            created_at=created_at,
            updated_at=updated_at,
            client=client,
            instructions=instructions,
        )

        equos_voice.additional_properties = d
        return equos_voice

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
