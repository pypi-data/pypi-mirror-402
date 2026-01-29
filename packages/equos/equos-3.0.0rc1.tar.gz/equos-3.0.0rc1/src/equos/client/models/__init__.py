"""Contains all the data models used in inputs/outputs"""

from .create_document_request import CreateDocumentRequest
from .create_document_response import CreateDocumentResponse
from .create_equos_brain_request import CreateEquosBrainRequest
from .create_equos_character_request import CreateEquosCharacterRequest
from .create_equos_conversation_request import CreateEquosConversationRequest
from .create_equos_conversation_request_prompt_template_vars_type_0 import (
    CreateEquosConversationRequestPromptTemplateVarsType0,
)
from .create_equos_conversation_response import CreateEquosConversationResponse
from .create_equos_face_request import CreateEquosFaceRequest
from .create_equos_face_request_identity import CreateEquosFaceRequestIdentity
from .create_equos_voice_request import CreateEquosVoiceRequest
from .create_equos_voice_request_identity import CreateEquosVoiceRequestIdentity
from .create_knowledge_base_request import CreateKnowledgeBaseRequest
from .equos_brain import EquosBrain
from .equos_character import EquosCharacter
from .equos_conversation import EquosConversation
from .equos_conversation_host import EquosConversationHost
from .equos_conversation_prompt_template_vars_type_0 import EquosConversationPromptTemplateVarsType0
from .equos_conversation_status import EquosConversationStatus
from .equos_conversation_transcript_message import EquosConversationTranscriptMessage
from .equos_conversation_transcript_message_author import EquosConversationTranscriptMessageAuthor
from .equos_conversation_with_character import EquosConversationWithCharacter
from .equos_conversation_with_character_prompt_template_vars_type_0 import (
    EquosConversationWithCharacterPromptTemplateVarsType0,
)
from .equos_conversation_with_character_status import EquosConversationWithCharacterStatus
from .equos_document import EquosDocument
from .equos_face import EquosFace
from .equos_face_identity import EquosFaceIdentity
from .equos_knowledge_base import EquosKnowledgeBase
from .equos_participant_identity import EquosParticipantIdentity
from .equos_voice import EquosVoice
from .equos_voice_identity import EquosVoiceIdentity
from .health_response import HealthResponse
from .list_equos_brains_response import ListEquosBrainsResponse
from .list_equos_characters_response import ListEquosCharactersResponse
from .list_equos_conversations_response import ListEquosConversationsResponse
from .list_equos_faces_response import ListEquosFacesResponse
from .list_equos_knowledge_bases_response import ListEquosKnowledgeBasesResponse
from .list_equos_voices_response import ListEquosVoicesResponse
from .update_equos_character_request import UpdateEquosCharacterRequest

__all__ = (
    "CreateDocumentRequest",
    "CreateDocumentResponse",
    "CreateEquosBrainRequest",
    "CreateEquosCharacterRequest",
    "CreateEquosConversationRequest",
    "CreateEquosConversationRequestPromptTemplateVarsType0",
    "CreateEquosConversationResponse",
    "CreateEquosFaceRequest",
    "CreateEquosFaceRequestIdentity",
    "CreateEquosVoiceRequest",
    "CreateEquosVoiceRequestIdentity",
    "CreateKnowledgeBaseRequest",
    "EquosBrain",
    "EquosCharacter",
    "EquosConversation",
    "EquosConversationHost",
    "EquosConversationPromptTemplateVarsType0",
    "EquosConversationStatus",
    "EquosConversationTranscriptMessage",
    "EquosConversationTranscriptMessageAuthor",
    "EquosConversationWithCharacter",
    "EquosConversationWithCharacterPromptTemplateVarsType0",
    "EquosConversationWithCharacterStatus",
    "EquosDocument",
    "EquosFace",
    "EquosFaceIdentity",
    "EquosKnowledgeBase",
    "EquosParticipantIdentity",
    "EquosVoice",
    "EquosVoiceIdentity",
    "HealthResponse",
    "ListEquosBrainsResponse",
    "ListEquosCharactersResponse",
    "ListEquosConversationsResponse",
    "ListEquosFacesResponse",
    "ListEquosKnowledgeBasesResponse",
    "ListEquosVoicesResponse",
    "UpdateEquosCharacterRequest",
)
