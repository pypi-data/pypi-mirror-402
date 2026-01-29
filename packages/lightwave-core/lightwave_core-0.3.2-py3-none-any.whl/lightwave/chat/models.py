"""Base chat models for AI-powered conversations.

These are abstract models that should be extended in your project:

    from lightwave.chat import BaseChatSession, BaseChatMessage

    class Chat(BaseChatSession):
        # Add project-specific fields
        agent_type = models.CharField(...)

    class ChatMessage(BaseChatMessage):
        chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name="messages")
"""

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from lightwave.utils.models import BaseModel


class ChatTypes(models.TextChoices):
    """Types of chat sessions."""

    CHAT = "chat", _("Chat")
    AGENT = "agent", _("Agent")


class MessageTypes(models.TextChoices):
    """Types of messages in a chat."""

    HUMAN = "HUMAN", _("Human")
    AI = "AI", _("AI")
    SYSTEM = "SYSTEM", _("System")


class BaseChatSession(BaseModel):
    """
    Abstract base model for a chat session.

    Extend this in your project and add project-specific fields.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="%(class)s_sessions",
    )
    chat_type = models.CharField(max_length=30, choices=ChatTypes.choices, default=ChatTypes.CHAT)
    name = models.CharField(max_length=100, default="Unnamed Chat")

    class Meta:
        abstract = True

    def __str__(self):
        return f"{self.name} ({self.user})"

    def get_openai_messages(self) -> list[dict]:
        """Return a list of messages ready to pass to the OpenAI ChatCompletion API."""
        return [m.to_openai_dict() for m in self.messages.all()]


class BaseChatMessage(BaseModel):
    """
    Abstract base model for a message in a chat.

    Extend this in your project and add a ForeignKey to your Chat model:

        class ChatMessage(BaseChatMessage):
            chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name="messages")
    """

    message_type = models.CharField(max_length=10, choices=MessageTypes.choices)
    content = models.TextField()

    class Meta:
        abstract = True
        ordering = ["created_at"]

    @property
    def is_ai_message(self) -> bool:
        """Check if this is an AI message."""
        return self.message_type == MessageTypes.AI

    @property
    def is_human_message(self) -> bool:
        """Check if this is a human message."""
        return self.message_type == MessageTypes.HUMAN

    def to_openai_dict(self) -> dict:
        """Convert to OpenAI API message format."""
        return {
            "role": self.get_openai_role(),
            "content": self.content,
        }

    def get_openai_role(self) -> str:
        """Get the OpenAI API role for this message type."""
        if self.message_type == MessageTypes.HUMAN:
            return "user"
        elif self.message_type == MessageTypes.AI:
            return "assistant"
        return "system"
