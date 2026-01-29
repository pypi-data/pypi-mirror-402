"""Interaction response resource for responding to slash commands."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from .base import BaseResource


@dataclass
class InteractionResponse:
    """Result of responding to an interaction."""

    success: bool
    interaction_id: str
    message: str


class InteractionsResource(BaseResource):
    """Resource for responding to Discord interactions (slash commands).

    This resource allows SDK clients to send responses to deferred slash
    command interactions.

    Example:
        >>> # Respond to a slash command
        >>> result = client.interactions.respond(
        ...     bot_id=1,
        ...     interaction_id="123456789",
        ...     content="Here's your answer!"
        ... )
        >>> print(f"Response sent: {result.success}")
    """

    def respond(
        self,
        bot_id: int,
        interaction_id: str,
        content: Optional[str] = None,
        embeds: Optional[list[dict[str, Any]]] = None,
        ephemeral: bool = False,
    ) -> InteractionResponse:
        """Send a response to a deferred Discord interaction.

        The bot must have already deferred the interaction response when
        the slash command was invoked. This sends the actual response content.

        Args:
            bot_id: ID of the bot that received the interaction
            interaction_id: Discord interaction ID (from SlashCommandEvent)
            content: Text content of the response (max 2000 chars)
            embeds: List of embed dicts (max 10 embeds)
            ephemeral: If True, only the invoking user sees the response

        Returns:
            InteractionResponse with success status and message

        Raises:
            ValidationError: If neither content nor embeds provided
            NotFoundError: If bot not found or interaction expired
            TimeoutError: If response takes too long
        """
        if not content and not embeds:
            from ..exceptions import ValidationError
            raise ValidationError("Either content or embeds must be provided")

        response = self._http.post(
            f"/interactions/{interaction_id}/respond",
            json={
                "bot_id": bot_id,
                "content": content,
                "embeds": embeds,
                "ephemeral": ephemeral,
            },
        )

        return InteractionResponse(
            success=response.get("success", False),
            interaction_id=response.get("interaction_id", interaction_id),
            message=response.get("message", ""),
        )
