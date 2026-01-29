from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.equos_character import EquosCharacter


T = TypeVar("T", bound="ListEquosCharactersResponse")


@_attrs_define
class ListEquosCharactersResponse:
    """
    Attributes:
        skip (float):
        take (float):
        total (float):
        characters (list[EquosCharacter]):
    """

    skip: float
    take: float
    total: float
    characters: list[EquosCharacter]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        skip = self.skip

        take = self.take

        total = self.total

        characters = []
        for characters_item_data in self.characters:
            characters_item = characters_item_data.to_dict()
            characters.append(characters_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "skip": skip,
                "take": take,
                "total": total,
                "characters": characters,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.equos_character import EquosCharacter

        d = dict(src_dict)
        skip = d.pop("skip")

        take = d.pop("take")

        total = d.pop("total")

        characters = []
        _characters = d.pop("characters")
        for characters_item_data in _characters:
            characters_item = EquosCharacter.from_dict(characters_item_data)

            characters.append(characters_item)

        list_equos_characters_response = cls(
            skip=skip,
            take=take,
            total=total,
            characters=characters,
        )

        list_equos_characters_response.additional_properties = d
        return list_equos_characters_response

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
