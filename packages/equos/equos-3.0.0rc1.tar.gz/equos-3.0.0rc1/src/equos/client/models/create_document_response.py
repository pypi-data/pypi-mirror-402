from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

if TYPE_CHECKING:
    from ..models.equos_document import EquosDocument


T = TypeVar("T", bound="CreateDocumentResponse")


@_attrs_define
class CreateDocumentResponse:
    """
    Attributes:
        document (EquosDocument):
        upload_url (str):
        expire_at (datetime.datetime):
    """

    document: EquosDocument
    upload_url: str
    expire_at: datetime.datetime
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        document = self.document.to_dict()

        upload_url = self.upload_url

        expire_at = self.expire_at.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "document": document,
                "uploadUrl": upload_url,
                "expireAt": expire_at,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.equos_document import EquosDocument

        d = dict(src_dict)
        document = EquosDocument.from_dict(d.pop("document"))

        upload_url = d.pop("uploadUrl")

        expire_at = isoparse(d.pop("expireAt"))

        create_document_response = cls(
            document=document,
            upload_url=upload_url,
            expire_at=expire_at,
        )

        create_document_response.additional_properties = d
        return create_document_response

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
