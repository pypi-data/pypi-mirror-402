from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.equos_face_identity import EquosFaceIdentity
from ..types import UNSET, Unset

T = TypeVar("T", bound="EquosFace")


@_attrs_define
class EquosFace:
    """
    Attributes:
        id (str):
        identity (EquosFaceIdentity):
        organization_id (str):
        created_at (datetime.datetime):
        updated_at (datetime.datetime):
        client (None | str | Unset):
        description (None | str | Unset):
        thumbnail_url (None | str | Unset):
        reference_img_url (None | str | Unset):
    """

    id: str
    identity: EquosFaceIdentity
    organization_id: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    client: None | str | Unset = UNSET
    description: None | str | Unset = UNSET
    thumbnail_url: None | str | Unset = UNSET
    reference_img_url: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        identity = self.identity.value

        organization_id = self.organization_id

        created_at = self.created_at.isoformat()

        updated_at = self.updated_at.isoformat()

        client: None | str | Unset
        if isinstance(self.client, Unset):
            client = UNSET
        else:
            client = self.client

        description: None | str | Unset
        if isinstance(self.description, Unset):
            description = UNSET
        else:
            description = self.description

        thumbnail_url: None | str | Unset
        if isinstance(self.thumbnail_url, Unset):
            thumbnail_url = UNSET
        else:
            thumbnail_url = self.thumbnail_url

        reference_img_url: None | str | Unset
        if isinstance(self.reference_img_url, Unset):
            reference_img_url = UNSET
        else:
            reference_img_url = self.reference_img_url

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "identity": identity,
                "organizationId": organization_id,
                "createdAt": created_at,
                "updatedAt": updated_at,
            }
        )
        if client is not UNSET:
            field_dict["client"] = client
        if description is not UNSET:
            field_dict["description"] = description
        if thumbnail_url is not UNSET:
            field_dict["thumbnailUrl"] = thumbnail_url
        if reference_img_url is not UNSET:
            field_dict["referenceImgUrl"] = reference_img_url

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        identity = EquosFaceIdentity(d.pop("identity"))

        organization_id = d.pop("organizationId")

        created_at = isoparse(d.pop("createdAt"))

        updated_at = isoparse(d.pop("updatedAt"))

        def _parse_client(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        client = _parse_client(d.pop("client", UNSET))

        def _parse_description(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        description = _parse_description(d.pop("description", UNSET))

        def _parse_thumbnail_url(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        thumbnail_url = _parse_thumbnail_url(d.pop("thumbnailUrl", UNSET))

        def _parse_reference_img_url(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        reference_img_url = _parse_reference_img_url(d.pop("referenceImgUrl", UNSET))

        equos_face = cls(
            id=id,
            identity=identity,
            organization_id=organization_id,
            created_at=created_at,
            updated_at=updated_at,
            client=client,
            description=description,
            thumbnail_url=thumbnail_url,
            reference_img_url=reference_img_url,
        )

        equos_face.additional_properties = d
        return equos_face

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
