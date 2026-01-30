"""Anthropic Vertex AI provider implementation using LangChain integrations."""

from __future__ import annotations

from typing import Any

from ai_code_review.models.config import Config
from ai_code_review.providers.anthropic import AnthropicProvider
from ai_code_review.utils.exceptions import AIProviderError


class VertexAnthropicProvider(AnthropicProvider):
    """Anthropic Claude AI provider implementation via Vertex AI."""

    def __init__(self, config: Config) -> None:
        """Initialize Vertex Anthropic provider."""
        super().__init__(config)

    def _create_client(self) -> Any:
        """Create Anthropic Vertex AI client instance."""
        try:
            # Import logger here to avoid circular imports
            import structlog

            logger = structlog.get_logger()

            logger.info(
                "Creating Anthropic Vertex AI client",
                model=self.model_name,
                project=self.config.vertex_project_id,
                location=self.config.vertex_location,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                timeout=self.config.llm_timeout,
                max_retries=self.config.llm_max_retries,
            )

            if not self.config.vertex_project_id:
                raise AIProviderError(
                    "Vertex AI project ID is required for Anthropic Vertex provider",
                    "anthropic-vertex",
                )

            # Use LangChain's official ChatAnthropicVertex integration
            from langchain_google_vertexai.model_garden import ChatAnthropicVertex

            return ChatAnthropicVertex(
                model=self.model_name,
                project=self.config.vertex_project_id,
                location=self.config.vertex_location,
                max_output_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                timeout=self.config.llm_timeout,
                max_retries=self.config.llm_max_retries,
            )
        except Exception as e:
            raise AIProviderError(
                f"Failed to create Anthropic Vertex AI client: {e}", "anthropic-vertex"
            ) from e

    def is_available(self) -> bool:
        """Check if Anthropic Vertex AI is available."""
        if self.config.dry_run:
            return True

        # For Vertex AI, check if we have project ID and authentication
        return bool(self.config.vertex_project_id)

    async def health_check(self) -> dict[str, Any]:
        """Perform health check on Anthropic Vertex AI service."""
        if self.config.dry_run:
            return {
                "status": "healthy",
                "dry_run": True,
                "model": self.model_name,
                "provider": "anthropic-vertex",
            }

        try:
            # Basic validation - check required authentication for Vertex AI
            if not self.config.vertex_project_id:
                return {
                    "status": "unhealthy",
                    "error": "Missing Vertex AI project ID for Claude",
                    "provider": "anthropic-vertex",
                    "mode": "vertex_ai",
                }

            # Perform actual API health check with a minimal call
            try:
                # Create a minimal prompt to test API connectivity
                from langchain_core.messages import HumanMessage

                test_message = HumanMessage(content="test")

                # Create client and make a minimal API call for health check
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
                    "provider": "anthropic-vertex",
                    "mode": "vertex_ai",
                }

            except Exception as api_error:
                # API call failed - provide detailed diagnostics
                error_msg = str(api_error)
                suggestion = "Unknown error"

                if "Connection error" in error_msg or "connection" in error_msg.lower():
                    suggestion = (
                        "Connection failed. Check: 1) Run 'gcloud auth application-default login', "
                        f"2) Verify project ID '{self.config.vertex_project_id}', "
                        "3) Enable Vertex AI API, 4) Check network connectivity"
                    )
                elif "permission" in error_msg.lower() or "auth" in error_msg.lower():
                    suggestion = (
                        "Authentication failed. Run 'gcloud auth application-default login' "
                        f"and ensure your account has Vertex AI permissions in project '{self.config.vertex_project_id}'"
                    )
                elif "not found" in error_msg.lower():
                    suggestion = f"Model '{self.model_name}' not available in Vertex AI or project ID incorrect"

                return {
                    "status": "unhealthy",
                    "authentication_configured": True,
                    "api_connectivity": False,
                    "error": f"Anthropic Vertex AI test failed: {error_msg}",
                    "suggestion": suggestion,
                    "provider": "anthropic-vertex",
                    "mode": "vertex_ai",
                    "project_id": self.config.vertex_project_id,
                    "region": self.config.vertex_location,
                }

        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "provider": "anthropic-vertex",
            }
