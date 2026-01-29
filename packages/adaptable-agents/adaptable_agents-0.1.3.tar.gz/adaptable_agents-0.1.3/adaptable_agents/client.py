"""Core AdaptableAgent client for interacting with the Adaptable Agents API."""

import requests
from typing import Optional, Dict, Any, Literal
from dataclasses import dataclass


@dataclass
class ContextConfig:
    """Configuration for context generation."""

    similarity_threshold: float = 0.8
    max_items: int = 5


# Strategy type: "vd" for DC (Dynamic Cheatsheet), "kg" for AMEM (Agentic Memory)
StrategyType = Literal["vd", "kg"]


class AdaptableAgent:
    """
    Core client for interacting with the Adaptable Agents API.

    This class handles communication with the Adaptable Agents API to:
    - Fetch context based on user input
    - Store memories after generating outputs

    Example:
        >>> agent = AdaptableAgent(
        ...     api_key="your-api-key",
        ...     api_base_url="http://localhost:8000",
        ...     memory_scope_path="customer-support/billing"
        ... )
        >>> context = agent.get_context("User needs help with payment")
    """

    def __init__(
        self,
        api_key: str,
        api_base_url: str = "http://localhost:8000",
        memory_scope_path: str = "default",
        context_config: Optional[ContextConfig] = None,
        strategy: StrategyType = "vd",
    ):
        """
        Initialize the AdaptableAgent client.

        Args:
            api_key: API key for authenticating with the Adaptable Agents API
            api_base_url: Base URL of the Adaptable Agents API (default: http://localhost:8000)
            memory_scope_path: Memory scope path for organizing memories (default: "default")
            context_config: Configuration for context generation (optional)
            strategy: Strategy to use - "vd" for DC (Dynamic Cheatsheet, default) or "kg" for AMEM (Agentic Memory)
        """
        # Strip whitespace from API key to avoid issues
        self.api_key = (api_key or "").strip()
        self.api_base_url = api_base_url.rstrip("/")
        self.memory_scope_path = memory_scope_path
        self.context_config = context_config or ContextConfig()
        self.strategy = strategy

        # Validate strategy
        if strategy not in ["vd", "kg"]:
            raise ValueError(
                f"Invalid strategy '{strategy}'. Must be 'vd' (DC) or 'kg' (AMEM)."
            )

        # Ensure API key is not empty or None
        if not self.api_key:
            raise ValueError("API key cannot be empty. Please provide a valid API key.")

        self._headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def get_context(self, input_text: str, use_cache: bool = False) -> Optional[str]:
        """
        Fetch context for the given input text.

        Args:
            input_text: The user input/query to generate context for
            use_cache: If True, try to get cached context first (default: False, only works for DC strategy)

        Returns:
            The context text, or None if generation fails
        """
        if self.strategy == "vd":
            return self._get_dc_context(input_text, use_cache)
        elif self.strategy == "kg":
            return self._get_amem_context(input_text)
        else:
            return None

    def load_prior_knowledge(self, input_text: Optional[str] = None) -> Optional[str]:
        """
        Load prior knowledge (context) for the given input text.

        This method retrieves relevant context from the adaptable agents system
        without making any external API calls or storing memories. It's a convenience
        method that wraps get_context.

        Args:
            input_text: The user input/query to generate context for. If None, returns None.

        Returns:
            Context string if available, None otherwise
        """
        if not input_text:
            return None

        try:
            return self.get_context(input_text)
        except Exception:
            # Silently continue if context generation fails
            return None

    def _get_dc_context(
        self, input_text: str, use_cache: bool = False
    ) -> Optional[str]:
        """Get context using DC (Dynamic Cheatsheet) strategy."""
        if use_cache:
            cached = self._get_cached_context()
            if cached:
                return cached

        url = f"{self.api_base_url}/api/v1/dc/generate"
        payload = {
            "memory_scope_path": self.memory_scope_path,
            "input": input_text,
            "similarity_threshold": self.context_config.similarity_threshold,
            "max_items": self.context_config.max_items,
        }

        try:
            response = requests.post(
                url, headers=self._headers, json=payload, timeout=300
            )

            if response.status_code == 200:
                data = response.json()
                return data.get("cheatsheet")
            elif response.status_code == 401:
                api_key_preview = (
                    f"{self.api_key[:8]}..." if len(self.api_key) > 8 else self.api_key
                )
                print(
                    f"Warning: API authentication failed (401). "
                    f"API key used: {api_key_preview}. "
                    f"URL: {url}. "
                    f"Response: {response.text}"
                )
                return None
            else:
                print(
                    f"Warning: Context generation failed with status {response.status_code}. Response: {response.text}"
                )
                return None
        except (requests.RequestException, ValueError) as e:
            print(f"Warning: Error fetching context: {str(e)}")
            return None

    def _get_amem_context(self, input_text: str) -> Optional[str]:
        """Get context using AMEM (Agentic Memory) strategy with evolution and retrieval."""
        url = f"{self.api_base_url}/api/v1/amem/generate"
        payload = {
            "memory_scope_path": self.memory_scope_path,
            "input": input_text,
            "k": self.context_config.max_items,
            "evolve_top_k": 5,  # Evolve top 1 memory by default
        }

        try:
            response = requests.post(
                url, headers=self._headers, json=payload, timeout=300
            )

            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                return self._format_amem_results(results)
            elif response.status_code == 401:
                api_key_preview = (
                    f"{self.api_key[:8]}..." if len(self.api_key) > 8 else self.api_key
                )
                print(
                    f"Warning: API authentication failed (401). "
                    f"API key used: {api_key_preview}. "
                    f"URL: {url}. "
                    f"Response: {response.text}"
                )
                return None
            else:
                print(
                    f"Warning: Context generation failed with status {response.status_code}. Response: {response.text}"
                )
                return None
        except (requests.RequestException, ValueError) as e:
            print(f"Warning: Error fetching context: {str(e)}")
            return None

    def _format_amem_results(self, results: list[Dict[str, Any]]) -> str:
        """Format AMEM search results into a context string."""
        if not results:
            return ""

        formatted_parts = []
        for i, result in enumerate(results, 1):
            content = result.get("content", "")
            context = result.get("context", "")
            keywords = result.get("keywords", [])
            tags = result.get("tags", [])

            parts = [f"Memory {i}:"]
            if content:
                parts.append(f"Content: {content}")
            if context:
                parts.append(f"Context: {context}")
            if keywords:
                parts.append(f"Keywords: {', '.join(keywords)}")
            if tags:
                parts.append(f"Tags: {', '.join(tags)}")

            formatted_parts.append("\n".join(parts))

        return "\n\n---\n\n".join(formatted_parts)

    def _get_cached_context(self) -> Optional[str]:
        """Get cached context for the memory scope (DC strategy only)."""
        if self.strategy != "vd":
            return None

        url = f"{self.api_base_url}/api/v1/dc/{self.memory_scope_path}"
        try:
            response = requests.get(url, headers=self._headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                if data.get("found"):
                    return data.get("cheatsheet")
        except (requests.RequestException, ValueError):
            pass
        return None

    def store_memory(
        self,
        input_text: str,
        output_text: str,
        summarize_input: Optional[bool] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Store a memory in the Adaptable Agents API.

        Args:
            input_text: The input text
            output_text: The output text
            summarize_input: Whether to summarize the input before storage and indexing.
                           If None, uses the default configuration.

        Returns:
            Dictionary with memory_id, or None if storage fails
        """
        url = f"{self.api_base_url}/api/v1/memories"
        payload = {
            "memory_scope_path": self.memory_scope_path,
            "input": input_text,
            "output": output_text,
        }
        if summarize_input is not None:
            payload["summarize_input"] = summarize_input

        try:
            response = requests.post(
                url, headers=self._headers, json=payload, timeout=10
            )

            if response.status_code == 201:
                return response.json()
            elif response.status_code == 401:
                # Log authentication errors for debugging
                print(
                    f"Warning: API authentication failed (401) when storing memory. Check your API key. Response: {response.text}"
                )
                return None
            else:
                print(
                    f"Warning: Memory storage failed with status {response.status_code}. Response: {response.text}"
                )
                return None
        except (requests.RequestException, ValueError) as e:
            # Log request errors for debugging
            print(f"Warning: Error storing memory: {str(e)}")
            return None

    def format_prompt_with_context(
        self, user_prompt: str, context: Optional[str]
    ) -> str:
        """
        Format a user prompt with context content.

        Args:
            user_prompt: The original user prompt
            context: The context content (can be None)

        Returns:
            Formatted prompt with context prepended
        """
        if not context:
            return user_prompt

        formatted = f"""Here's relevant context from past experiences that might help:

{context}

---

User Query: {user_prompt}"""
        return formatted
