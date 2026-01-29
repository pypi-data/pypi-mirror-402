from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

T = TypeVar("T", bound="EquosDocument")


@_attrs_define
class EquosDocument:
    """
    Attributes:
        id (str):
        knowledge_base_id (str):
        name (str):
        description (str):
        size (float):
        status (str):
        created_at (datetime.datetime):
        updated_at (datetime.datetime):
    """

    id: str
    knowledge_base_id: str
    name: str
    description: str
    size: float
    status: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        knowledge_base_id = self.knowledge_base_id

        name = self.name

        description = self.description

        size = self.size

        status = self.status

        created_at = self.created_at.isoformat()

        updated_at = self.updated_at.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "knowledgeBaseId": knowledge_base_id,
                "name": name,
                "description": description,
                "size": size,
                "status": status,
                "createdAt": created_at,
                "updatedAt": updated_at,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        knowledge_base_id = d.pop("knowledgeBaseId")

        name = d.pop("name")

        description = d.pop("description")

        size = d.pop("size")

        status = d.pop("status")

        created_at = isoparse(d.pop("createdAt"))

        updated_at = isoparse(d.pop("updatedAt"))

        equos_document = cls(
            id=id,
            knowledge_base_id=knowledge_base_id,
            name=name,
            description=description,
            size=size,
            status=status,
            created_at=created_at,
            updated_at=updated_at,
        )

        equos_document.additional_properties = d
        return equos_document

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
