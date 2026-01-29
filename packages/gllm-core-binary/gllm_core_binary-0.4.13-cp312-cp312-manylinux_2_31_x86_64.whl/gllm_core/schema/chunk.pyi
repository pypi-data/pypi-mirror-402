from gllm_core.utils import get_value_repr as get_value_repr
from pydantic import BaseModel
from typing import Any

class Chunk(BaseModel, arbitrary_types_allowed=True):
    """Represents a chunk of content retrieved from a vector store.

    Attributes:
        id (str): A unique identifier for the chunk. Defaults to a random UUID.
        content (str | bytes): The content of the chunk, either text or binary.
        metadata (dict[str, Any]): Additional metadata associated with the chunk. Defaults to an empty dictionary.
        score (float | None): Similarity score of the chunk (if available). Defaults to None.
    """
    id: str
    content: str | bytes
    metadata: dict[str, Any]
    score: float | None
    @classmethod
    def validate_content(cls, value: str | bytes) -> str | bytes:
        """Validate the content of the Chunk.

        This is a class method required by Pydantic validators. As such, it follows its signature and conventions.

        Args:
            value (str | bytes): The content to validate.

        Returns:
            str | bytes: The validated content.

        Raises:
            ValueError: If the content is empty or not a string or bytes.
        """
    def is_text(self) -> bool:
        """Check if the content is text.

        Returns:
            bool: True if the content is text, False otherwise.
        """
    def is_binary(self) -> bool:
        """Check if the content is binary.

        Returns:
            bool: True if the content is binary, False otherwise.
        """
