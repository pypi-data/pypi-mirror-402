"""Gemini Vertex AI provider implementation using LangChain."""

from __future__ import annotations

from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel

from ai_code_review.models.config import Config
from ai_code_review.providers.gemini import GeminiProvider
from ai_code_review.utils.exceptions import AIProviderError


class VertexGeminiProvider(GeminiProvider):
    """Google Gemini AI provider implementation via Vertex AI."""

    def __init__(self, config: Config) -> None:
        """Initialize Vertex Gemini provider."""
        super().__init__(config)

    def _create_client(self) -> BaseChatModel:
        """Create Gemini Vertex AI client instance."""
        try:
            # Import logger here to avoid circular imports
            import structlog

            logger = structlog.get_logger()

            # Use Vertex AI via unified ChatGoogleGenerativeAI
            from langchain_google_genai import ChatGoogleGenerativeAI

            logger.info(
                "Creating Vertex AI Gemini client via unified interface",
                model=self.model_name,
                project=self.config.vertex_project_id,
                location=self.config.vertex_location,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                timeout=self.config.llm_timeout,
                max_retries=self.config.llm_max_retries,
            )

            return ChatGoogleGenerativeAI(
                model=self.model_name,
                # Use Vertex AI mode with project and location parameters
                vertexai=True,
                project=self.config.vertex_project_id,
                location=self.config.vertex_location,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                timeout=self.config.llm_timeout,
                max_retries=self.config.llm_max_retries,
            )
        except Exception as e:
            raise AIProviderError(
                f"Failed to create Gemini Vertex AI client: {e}", "gemini-vertex"
            ) from e

    def is_available(self) -> bool:
        """Check if Gemini Vertex AI is available."""
        if self.config.dry_run:
            return True

        # For Vertex AI, check if we have project ID and authentication
        return bool(self.config.vertex_project_id)

    async def health_check(self) -> dict[str, Any]:
        """Perform health check on Gemini Vertex AI service."""
        if self.config.dry_run:
            return {
                "status": "healthy",
                "dry_run": True,
                "model": self.model_name,
                "provider": "gemini-vertex",
            }

        try:
            # Basic validation - check required authentication for Vertex AI
            if not self.config.vertex_project_id:
                return {
                    "status": "unhealthy",
                    "error": "Missing Vertex AI project ID",
                    "provider": "gemini-vertex",
                    "mode": "vertex_ai",
                }

            # Perform actual API health check with a minimal call
            try:
                # Create a minimal prompt to test API connectivity
                from langchain_core.messages import HumanMessage

                test_message = HumanMessage(content="test")

                # Use a very short timeout for health check
                client = self._create_client()

                # Make a minimal API call with short timeout - just to verify connectivity
                # We don't need the actual response, just to verify the call works
                import asyncio

                await asyncio.wait_for(client.ainvoke([test_message]), timeout=10.0)

                return {
                    "status": "healthy",
                    "authentication_configured": True,
                    "api_connectivity": True,
                    "model": self.model_name,
                    "provider": "gemini-vertex",
                    "mode": "vertex_ai",
                }

            except Exception as api_error:
                # API call failed - return specific error information
                return {
                    "status": "unhealthy",
                    "authentication_configured": True,
                    "api_connectivity": False,
                    "error": f"Gemini Vertex AI test failed: {str(api_error)}",
                    "provider": "gemini-vertex",
                    "mode": "vertex_ai",
                }

        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "provider": "gemini-vertex",
            }
