from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.equos_face import EquosFace


T = TypeVar("T", bound="ListEquosFacesResponse")


@_attrs_define
class ListEquosFacesResponse:
    """
    Attributes:
        skip (float):
        take (float):
        total (float):
        faces (list[EquosFace]):
    """

    skip: float
    take: float
    total: float
    faces: list[EquosFace]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        skip = self.skip

        take = self.take

        total = self.total

        faces = []
        for faces_item_data in self.faces:
            faces_item = faces_item_data.to_dict()
            faces.append(faces_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "skip": skip,
                "take": take,
                "total": total,
                "faces": faces,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.equos_face import EquosFace

        d = dict(src_dict)
        skip = d.pop("skip")

        take = d.pop("take")

        total = d.pop("total")

        faces = []
        _faces = d.pop("faces")
        for faces_item_data in _faces:
            faces_item = EquosFace.from_dict(faces_item_data)

            faces.append(faces_item)

        list_equos_faces_response = cls(
            skip=skip,
            take=take,
            total=total,
            faces=faces,
        )

        list_equos_faces_response.additional_properties = d
        return list_equos_faces_response

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
