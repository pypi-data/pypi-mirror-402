from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="CreateEquosCharacterRequest")


@_attrs_define
class CreateEquosCharacterRequest:
    """
    Attributes:
        name (str):
        livekit_identity (str):
        client (None | str | Unset): Client identifier associated with the character. This is useful to segment
            resources by client.
        face_id (None | str | Unset):
        voice_id (None | str | Unset):
        brain_id (None | str | Unset):
        knowledge_base_id (None | str | Unset):
        search (bool | Unset):  Default: False.
        elevenlabs_agent_id (None | str | Unset):
    """

    name: str
    livekit_identity: str
    client: None | str | Unset = UNSET
    face_id: None | str | Unset = UNSET
    voice_id: None | str | Unset = UNSET
    brain_id: None | str | Unset = UNSET
    knowledge_base_id: None | str | Unset = UNSET
    search: bool | Unset = False
    elevenlabs_agent_id: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        livekit_identity = self.livekit_identity

        client: None | str | Unset
        if isinstance(self.client, Unset):
            client = UNSET
        else:
            client = self.client

        face_id: None | str | Unset
        if isinstance(self.face_id, Unset):
            face_id = UNSET
        else:
            face_id = self.face_id

        voice_id: None | str | Unset
        if isinstance(self.voice_id, Unset):
            voice_id = UNSET
        else:
            voice_id = self.voice_id

        brain_id: None | str | Unset
        if isinstance(self.brain_id, Unset):
            brain_id = UNSET
        else:
            brain_id = self.brain_id

        knowledge_base_id: None | str | Unset
        if isinstance(self.knowledge_base_id, Unset):
            knowledge_base_id = UNSET
        else:
            knowledge_base_id = self.knowledge_base_id

        search = self.search

        elevenlabs_agent_id: None | str | Unset
        if isinstance(self.elevenlabs_agent_id, Unset):
            elevenlabs_agent_id = UNSET
        else:
            elevenlabs_agent_id = self.elevenlabs_agent_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "livekitIdentity": livekit_identity,
            }
        )
        if client is not UNSET:
            field_dict["client"] = client
        if face_id is not UNSET:
            field_dict["faceId"] = face_id
        if voice_id is not UNSET:
            field_dict["voiceId"] = voice_id
        if brain_id is not UNSET:
            field_dict["brainId"] = brain_id
        if knowledge_base_id is not UNSET:
            field_dict["knowledgeBaseId"] = knowledge_base_id
        if search is not UNSET:
            field_dict["search"] = search
        if elevenlabs_agent_id is not UNSET:
            field_dict["elevenlabsAgentId"] = elevenlabs_agent_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name")

        livekit_identity = d.pop("livekitIdentity")

        def _parse_client(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        client = _parse_client(d.pop("client", UNSET))

        def _parse_face_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        face_id = _parse_face_id(d.pop("faceId", UNSET))

        def _parse_voice_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        voice_id = _parse_voice_id(d.pop("voiceId", UNSET))

        def _parse_brain_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        brain_id = _parse_brain_id(d.pop("brainId", UNSET))

        def _parse_knowledge_base_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        knowledge_base_id = _parse_knowledge_base_id(d.pop("knowledgeBaseId", UNSET))

        search = d.pop("search", UNSET)

        def _parse_elevenlabs_agent_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        elevenlabs_agent_id = _parse_elevenlabs_agent_id(d.pop("elevenlabsAgentId", UNSET))

        create_equos_character_request = cls(
            name=name,
            livekit_identity=livekit_identity,
            client=client,
            face_id=face_id,
            voice_id=voice_id,
            brain_id=brain_id,
            knowledge_base_id=knowledge_base_id,
            search=search,
            elevenlabs_agent_id=elevenlabs_agent_id,
        )

        create_equos_character_request.additional_properties = d
        return create_equos_character_request

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
