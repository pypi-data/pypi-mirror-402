from dataclasses import dataclass

from equos.client.client import AuthenticatedClient

# Import generated API groups
from equos.client.api.brain import BrainApi
from equos.client.api.character import CharacterApi
from equos.client.api.conversation import ConversationApi
from equos.client.api.face import FaceApi
from equos.client.api.health import HealthApi
from equos.client.api.knowledge_base import KnowledgeBaseApi
from equos.client.api.organization import OrganizationApi
from equos.client.api.voice import VoiceApi


DEFAULT_VERSION = "v3"
DEFAULT_ENDPOINT = f"https://api.equos.ai/{DEFAULT_VERSION}"


@dataclass
class EquosOptions:
    """
    Options for configuring the Equos client.
    """

    endpoint: str | None = None


class EquosClient:
    """
    Main Equos SDK client (Python).

    Thin wrapper around the generated OpenAPI client, mirroring the TS SDK API.
    """

    def __init__(self, api_key: str, options: EquosOptions | None = None):
        endpoint = options.endpoint if options and options.endpoint else DEFAULT_ENDPOINT

        self._base_url = endpoint

        # Create authenticated OpenAPI client
        self._client = AuthenticatedClient(
            base_url=self._base_url,
            token=api_key,
            auth_header_name="x-api-key",
            prefix="",  # IMPORTANT: API key, not Bearer
        )

        # API instances (mirrors TS SDK)
        self.brains = BrainApi(self._client)
        self.characters = CharacterApi(self._client)
        self.faces = FaceApi(self._client)
        self.health = HealthApi(self._client)
        self.knowledge_bases = KnowledgeBaseApi(self._client)
        self.voices = VoiceApi(self._client)
        self.conversations = ConversationApi(self._client)
        self.organizations = OrganizationApi(self._client)

    @classmethod
    def create(cls, api_key: str, options: EquosOptions | None = None) -> "EquosClient":
        """
        Create a new Equos client instance.

        :param api_key: Your Equos API key
        :param options: Optional client configuration
        """
        return cls(api_key, options)

    @property
    def base_url(self) -> str:
        """
        Get the base URL used by this client.
        """
        return self._base_url
