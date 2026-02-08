"""
LLM Provider Abstraction — Switch between Gemini, OpenAI, and Local models.

Usage:
    from engines.llm_provider import get_llm
    llm = get_llm()  # Uses config to pick provider
    answer = llm.chat("What is the claim amount?", context={...})
"""

import json
from typing import Dict, List, Optional

from config import Config


class BaseLLM:
    """Base class for LLM providers."""

    def chat(self, question: str, system_prompt: str = "", history: List[Dict] = None) -> str:
        raise NotImplementedError


class GeminiLLM(BaseLLM):
    """Google Gemini provider."""

    def __init__(self, api_key: str = None):
        import google.generativeai as genai
        key = api_key or Config.GOOGLE_API_KEY
        genai.configure(api_key=key)
        self.model = genai.GenerativeModel(
            Config.GEMINI_MODEL,
            generation_config={"temperature": 0.3, "max_output_tokens": 1024},
        )

    def chat(self, question: str, system_prompt: str = "", history: List[Dict] = None) -> str:
        parts = []
        if system_prompt:
            parts.append(system_prompt)
        for h in (history or []):
            parts.append(f"{h.get('role', 'user')}: {h.get('content', '')}")
        parts.append(f"user: {question}")
        response = self.model.generate_content("\n\n".join(parts))
        return response.text.strip()


class OpenAILLM(BaseLLM):
    """OpenAI provider (GPT-4o-mini / GPT-4o)."""

    def __init__(self, api_key: str = None):
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("pip install openai — required for OpenAI provider")
        key = api_key or Config.OPENAI_API_KEY
        self.client = OpenAI(api_key=key)
        self.model = Config.OPENAI_MODEL

    def chat(self, question: str, system_prompt: str = "", history: List[Dict] = None) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        for h in (history or []):
            role = h.get("role", "user")
            if role not in ("user", "assistant", "system"):
                role = "user"
            messages.append({"role": role, "content": h.get("content", "")})
        messages.append({"role": "user", "content": question})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.3,
            max_tokens=1024,
        )
        return response.choices[0].message.content.strip()


class LocalLLM(BaseLLM):
    """Local LLM via vLLM/Ollama OpenAI-compatible endpoint."""

    def __init__(self):
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("pip install openai — required for local LLM (OpenAI-compatible API)")
        self.client = OpenAI(
            base_url=Config.LOCAL_LLM_URL,
            api_key="not-needed",  # Local models don't need a key
        )
        self.model = Config.LOCAL_LLM_MODEL

    def chat(self, question: str, system_prompt: str = "", history: List[Dict] = None) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        for h in (history or []):
            role = h.get("role", "user")
            if role not in ("user", "assistant", "system"):
                role = "user"
            messages.append({"role": role, "content": h.get("content", "")})
        messages.append({"role": "user", "content": question})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.3,
            max_tokens=1024,
        )
        return response.choices[0].message.content.strip()


def get_llm(api_key: str = None, provider: str = None) -> BaseLLM:
    """Factory: returns the configured LLM provider.

    Priority: explicit provider > Config.LLM_PROVIDER
    If api_key is provided, overrides the config key for cloud providers.
    """
    prov = (provider or Config.LLM_PROVIDER).lower()

    if prov == "openai":
        return OpenAILLM(api_key=api_key)
    elif prov == "local":
        return LocalLLM()
    else:  # default: gemini
        return GeminiLLM(api_key=api_key)
