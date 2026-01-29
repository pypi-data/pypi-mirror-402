import os

import verbex
from verbex.api_keys import APIKeys
from verbex.agents import AIAgents, PostCallAnalysis
from verbex.calls import Calls
from verbex.core import CoreClient, HTTPClient, VerbexAPIError, VerbexError
from verbex.knowledge_bases import KnowledgeBases
from verbex.phone_numbers import PhoneNumbers
from verbex.prompt_generation import PromptGeneration
from verbex.public_sharing import PublicSharing
from verbex.tools import BuiltinTools, CustomTools


def test_imports_and_symbols():
    assert verbex.Verbex is not None
    assert APIKeys is not None
    assert AIAgents is not None
    assert PostCallAnalysis is not None
    assert Calls is not None
    assert CoreClient is not None
    assert HTTPClient is not None
    assert VerbexError is not None
    assert VerbexAPIError is not None
    assert KnowledgeBases is not None
    assert PhoneNumbers is not None
    assert PromptGeneration is not None
    assert PublicSharing is not None
    assert BuiltinTools is not None
    assert CustomTools is not None


def test_sdk_initialization_uses_env_key(monkeypatch):
    monkeypatch.setenv('VERBEX_API_KEY', 'test-key')
    client = verbex.Verbex()
    assert client.ai_agents is not None
    assert client.postcall_analysis is not None
    assert client.builtin_tools is not None
    assert client.custom_tools is not None
    assert client.calls is not None
    assert client.phone_numbers is not None
    assert client.knowledge_bases is not None
    assert client.prompt_generation is not None
    assert client.public_sharing is not None
    client.close()
