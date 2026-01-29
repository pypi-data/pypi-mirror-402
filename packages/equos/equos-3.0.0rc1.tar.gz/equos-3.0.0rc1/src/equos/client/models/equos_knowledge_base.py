from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.equos_document import EquosDocument


T = TypeVar("T", bound="EquosKnowledgeBase")


@_attrs_define
class EquosKnowledgeBase:
    """
    Attributes:
        id (str):
        organization_id (str):
        name (str):
        description (str):
        documents (list[EquosDocument]):
        created_at (datetime.datetime):
        updated_at (datetime.datetime):
        client (str | Unset):
    """

    id: str
    organization_id: str
    name: str
    description: str
    documents: list[EquosDocument]
    created_at: datetime.datetime
    updated_at: datetime.datetime
    client: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        organization_id = self.organization_id

        name = self.name

        description = self.description

        documents = []
        for documents_item_data in self.documents:
            documents_item = documents_item_data.to_dict()
            documents.append(documents_item)

        created_at = self.created_at.isoformat()

        updated_at = self.updated_at.isoformat()

        client = self.client

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "organizationId": organization_id,
                "name": name,
                "description": description,
                "documents": documents,
                "createdAt": created_at,
                "updatedAt": updated_at,
            }
        )
        if client is not UNSET:
            field_dict["client"] = client

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.equos_document import EquosDocument

        d = dict(src_dict)
        id = d.pop("id")

        organization_id = d.pop("organizationId")

        name = d.pop("name")

        description = d.pop("description")

        documents = []
        _documents = d.pop("documents")
        for documents_item_data in _documents:
            documents_item = EquosDocument.from_dict(documents_item_data)

            documents.append(documents_item)

        created_at = isoparse(d.pop("createdAt"))

        updated_at = isoparse(d.pop("updatedAt"))

        client = d.pop("client", UNSET)

        equos_knowledge_base = cls(
            id=id,
            organization_id=organization_id,
            name=name,
            description=description,
            documents=documents,
            created_at=created_at,
            updated_at=updated_at,
            client=client,
        )

        equos_knowledge_base.additional_properties = d
        return equos_knowledge_base

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
