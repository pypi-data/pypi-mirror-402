from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.equos_brain import EquosBrain


T = TypeVar("T", bound="ListEquosBrainsResponse")


@_attrs_define
class ListEquosBrainsResponse:
    """
    Attributes:
        skip (float):
        take (float):
        total (float):
        brains (list[EquosBrain]):
    """

    skip: float
    take: float
    total: float
    brains: list[EquosBrain]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        skip = self.skip

        take = self.take

        total = self.total

        brains = []
        for brains_item_data in self.brains:
            brains_item = brains_item_data.to_dict()
            brains.append(brains_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "skip": skip,
                "take": take,
                "total": total,
                "brains": brains,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.equos_brain import EquosBrain

        d = dict(src_dict)
        skip = d.pop("skip")

        take = d.pop("take")

        total = d.pop("total")

        brains = []
        _brains = d.pop("brains")
        for brains_item_data in _brains:
            brains_item = EquosBrain.from_dict(brains_item_data)

            brains.append(brains_item)

        list_equos_brains_response = cls(
            skip=skip,
            take=take,
            total=total,
            brains=brains,
        )

        list_equos_brains_response.additional_properties = d
        return list_equos_brains_response

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
