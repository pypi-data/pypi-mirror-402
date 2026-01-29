from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.equos_brain import EquosBrain
    from ..models.equos_face import EquosFace
    from ..models.equos_knowledge_base import EquosKnowledgeBase
    from ..models.equos_voice import EquosVoice


T = TypeVar("T", bound="EquosCharacter")


@_attrs_define
class EquosCharacter:
    """
    Attributes:
        id (str):
        organization_id (str):
        name (str):
        livekit_identity (str):
        search (bool):
        created_at (datetime.datetime):
        updated_at (datetime.datetime):
        client (None | str | Unset):
        elevenlabs_agent_id (None | str | Unset):
        face_id (None | str | Unset):
        voice_id (None | str | Unset):
        brain_id (None | str | Unset):
        knowledge_base_id (None | str | Unset):
        face (EquosFace | None | Unset):
        voice (EquosVoice | None | Unset):
        brain (EquosBrain | None | Unset):
        knowledge_base (EquosKnowledgeBase | None | Unset):
    """

    id: str
    organization_id: str
    name: str
    livekit_identity: str
    search: bool
    created_at: datetime.datetime
    updated_at: datetime.datetime
    client: None | str | Unset = UNSET
    elevenlabs_agent_id: None | str | Unset = UNSET
    face_id: None | str | Unset = UNSET
    voice_id: None | str | Unset = UNSET
    brain_id: None | str | Unset = UNSET
    knowledge_base_id: None | str | Unset = UNSET
    face: EquosFace | None | Unset = UNSET
    voice: EquosVoice | None | Unset = UNSET
    brain: EquosBrain | None | Unset = UNSET
    knowledge_base: EquosKnowledgeBase | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.equos_brain import EquosBrain
        from ..models.equos_face import EquosFace
        from ..models.equos_knowledge_base import EquosKnowledgeBase
        from ..models.equos_voice import EquosVoice

        id = self.id

        organization_id = self.organization_id

        name = self.name

        livekit_identity = self.livekit_identity

        search = self.search

        created_at = self.created_at.isoformat()

        updated_at = self.updated_at.isoformat()

        client: None | str | Unset
        if isinstance(self.client, Unset):
            client = UNSET
        else:
            client = self.client

        elevenlabs_agent_id: None | str | Unset
        if isinstance(self.elevenlabs_agent_id, Unset):
            elevenlabs_agent_id = UNSET
        else:
            elevenlabs_agent_id = self.elevenlabs_agent_id

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

        face: dict[str, Any] | None | Unset
        if isinstance(self.face, Unset):
            face = UNSET
        elif isinstance(self.face, EquosFace):
            face = self.face.to_dict()
        else:
            face = self.face

        voice: dict[str, Any] | None | Unset
        if isinstance(self.voice, Unset):
            voice = UNSET
        elif isinstance(self.voice, EquosVoice):
            voice = self.voice.to_dict()
        else:
            voice = self.voice

        brain: dict[str, Any] | None | Unset
        if isinstance(self.brain, Unset):
            brain = UNSET
        elif isinstance(self.brain, EquosBrain):
            brain = self.brain.to_dict()
        else:
            brain = self.brain

        knowledge_base: dict[str, Any] | None | Unset
        if isinstance(self.knowledge_base, Unset):
            knowledge_base = UNSET
        elif isinstance(self.knowledge_base, EquosKnowledgeBase):
            knowledge_base = self.knowledge_base.to_dict()
        else:
            knowledge_base = self.knowledge_base

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "organizationId": organization_id,
                "name": name,
                "livekitIdentity": livekit_identity,
                "search": search,
                "createdAt": created_at,
                "updatedAt": updated_at,
            }
        )
        if client is not UNSET:
            field_dict["client"] = client
        if elevenlabs_agent_id is not UNSET:
            field_dict["elevenlabsAgentId"] = elevenlabs_agent_id
        if face_id is not UNSET:
            field_dict["faceId"] = face_id
        if voice_id is not UNSET:
            field_dict["voiceId"] = voice_id
        if brain_id is not UNSET:
            field_dict["brainId"] = brain_id
        if knowledge_base_id is not UNSET:
            field_dict["knowledgeBaseId"] = knowledge_base_id
        if face is not UNSET:
            field_dict["face"] = face
        if voice is not UNSET:
            field_dict["voice"] = voice
        if brain is not UNSET:
            field_dict["brain"] = brain
        if knowledge_base is not UNSET:
            field_dict["knowledgeBase"] = knowledge_base

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.equos_brain import EquosBrain
        from ..models.equos_face import EquosFace
        from ..models.equos_knowledge_base import EquosKnowledgeBase
        from ..models.equos_voice import EquosVoice

        d = dict(src_dict)
        id = d.pop("id")

        organization_id = d.pop("organizationId")

        name = d.pop("name")

        livekit_identity = d.pop("livekitIdentity")

        search = d.pop("search")

        created_at = isoparse(d.pop("createdAt"))

        updated_at = isoparse(d.pop("updatedAt"))

        def _parse_client(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        client = _parse_client(d.pop("client", UNSET))

        def _parse_elevenlabs_agent_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        elevenlabs_agent_id = _parse_elevenlabs_agent_id(d.pop("elevenlabsAgentId", UNSET))

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

        def _parse_face(data: object) -> EquosFace | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                face_type_1 = EquosFace.from_dict(data)

                return face_type_1
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(EquosFace | None | Unset, data)

        face = _parse_face(d.pop("face", UNSET))

        def _parse_voice(data: object) -> EquosVoice | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                voice_type_1 = EquosVoice.from_dict(data)

                return voice_type_1
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(EquosVoice | None | Unset, data)

        voice = _parse_voice(d.pop("voice", UNSET))

        def _parse_brain(data: object) -> EquosBrain | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                brain_type_1 = EquosBrain.from_dict(data)

                return brain_type_1
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(EquosBrain | None | Unset, data)

        brain = _parse_brain(d.pop("brain", UNSET))

        def _parse_knowledge_base(data: object) -> EquosKnowledgeBase | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                knowledge_base_type_1 = EquosKnowledgeBase.from_dict(data)

                return knowledge_base_type_1
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(EquosKnowledgeBase | None | Unset, data)

        knowledge_base = _parse_knowledge_base(d.pop("knowledgeBase", UNSET))

        equos_character = cls(
            id=id,
            organization_id=organization_id,
            name=name,
            livekit_identity=livekit_identity,
            search=search,
            created_at=created_at,
            updated_at=updated_at,
            client=client,
            elevenlabs_agent_id=elevenlabs_agent_id,
            face_id=face_id,
            voice_id=voice_id,
            brain_id=brain_id,
            knowledge_base_id=knowledge_base_id,
            face=face,
            voice=voice,
            brain=brain,
            knowledge_base=knowledge_base,
        )

        equos_character.additional_properties = d
        return equos_character

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
