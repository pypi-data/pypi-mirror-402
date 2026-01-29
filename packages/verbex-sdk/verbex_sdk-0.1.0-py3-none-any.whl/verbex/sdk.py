from __future__ import annotations

from .agents.ai_agents import AIAgents
from .agents.postcall_analysis import PostCallAnalysis
from .api_keys.api_keys import APIKeys
from .calls.calls import Calls
from .core.client import CoreClient
from .knowledge_bases.knowledge_bases import KnowledgeBases
from .phone_numbers.phone_numbers import PhoneNumbers
from .prompt_generation.prompt_generation import PromptGeneration
from .public_sharing.public_sharing import PublicSharing
from .tools.builtin_tools import BuiltinTools
from .tools.custom_tools import CustomTools


class VerbexSDK:
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = "https://api.verbex.ai",
        timeout: int | float = 30,
    ) -> None:
        self._client = CoreClient(api_key=api_key, base_url=base_url, timeout=timeout)
        self.ai_agents = AIAgents(self._client)
        self.postcall_analysis = PostCallAnalysis(self._client)
        self.builtin_tools = BuiltinTools(self._client)
        self.custom_tools = CustomTools(self._client)
        self.calls = Calls(self._client)
        self.phone_numbers = PhoneNumbers(self._client)
        self.knowledge_bases = KnowledgeBases(self._client)
        self.prompt_generation = PromptGeneration(self._client)
        self.public_sharing = PublicSharing(self._client)
        self.api_keys = APIKeys(self._client)

    def close(self) -> None:
        self._client.close()
