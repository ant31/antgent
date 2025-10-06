import logging
from typing import TYPE_CHECKING

from agents import TResponseInputItem

from antgent.models.agent import TLLMInput

if TYPE_CHECKING:
    from antgent.agents.base import BaseAgent


logger = logging.getLogger(__name__)


class MessageHandlerMixin:
    """Mixin for handling agent messages."""

    def add_inputs(
        self: "BaseAgent", llm_input: TLLMInput, messages: list[TResponseInputItem] | None
    ) -> list[TResponseInputItem]:
        if messages is None:
            messages = []
        if isinstance(llm_input, list):
            messages.extend(llm_input)
        elif isinstance(llm_input, str) and llm_input:
            messages.append({"content": llm_input, "role": "user"})
        return messages

    def _filter_empty_messages(self: "BaseAgent", messages: list[TResponseInputItem]) -> list[TResponseInputItem]:
        """
        Filters out messages with empty or whitespace-only content.

        Logs a warning for each filtered message, including its position and
        the first 20 characters of the previous non-empty message's content.

        Args:
            messages: List of message items to filter

        Returns:
            Filtered list of messages with empty content removed
        """
        filtered_messages = []
        last_non_empty_content = ""

        for idx, message in enumerate(messages):
            content = message.get("content", "")

            # Check if content is empty or whitespace only
            if content is None or (isinstance(content, str) and not content.strip()):
                # Get preview of previous non-empty message
                preview = last_non_empty_content[:20] if last_non_empty_content else "(no previous message)"
                if len(last_non_empty_content) > 20:
                    preview += "..."

                logger.warning(
                    "[%s] Filtering out empty message at position %s. Previous message content starts with: '%s'",
                    self.name_id,
                    idx,
                    preview,
                )
                continue

            # Keep this message and update last non-empty content
            filtered_messages.append(message)
            if isinstance(content, str):
                last_non_empty_content = content
            elif isinstance(content, list):
                # For content that is a list (like file inputs), use a placeholder
                last_non_empty_content = "[file/media content]"

        return filtered_messages
