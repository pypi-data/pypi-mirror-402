from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.create_equos_face_request_identity import CreateEquosFaceRequestIdentity
from ..types import UNSET, Unset

T = TypeVar("T", bound="CreateEquosFaceRequest")


@_attrs_define
class CreateEquosFaceRequest:
    """
    Attributes:
        identity (CreateEquosFaceRequestIdentity): Identity of the face in Equos Gallery.
        client (None | str | Unset): Client identifier associated with the face. This is useful to segment resources by
            client.
    """

    identity: CreateEquosFaceRequestIdentity
    client: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        identity = self.identity.value

        client: None | str | Unset
        if isinstance(self.client, Unset):
            client = UNSET
        else:
            client = self.client

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "identity": identity,
            }
        )
        if client is not UNSET:
            field_dict["client"] = client

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        identity = CreateEquosFaceRequestIdentity(d.pop("identity"))

        def _parse_client(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        client = _parse_client(d.pop("client", UNSET))

        create_equos_face_request = cls(
            identity=identity,
            client=client,
        )

        create_equos_face_request.additional_properties = d
        return create_equos_face_request

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
