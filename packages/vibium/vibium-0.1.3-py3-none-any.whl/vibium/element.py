"""Element class for interacting with page elements."""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .client import BiDiClient


@dataclass
class BoundingBox:
    """Bounding box of an element."""

    x: float
    y: float
    width: float
    height: float


@dataclass
class ElementInfo:
    """Information about an element."""

    tag: str
    text: str
    box: BoundingBox


class Element:
    """Represents a DOM element that can be interacted with."""

    def __init__(
        self,
        client: "BiDiClient",
        context: str,
        selector: str,
        info: ElementInfo,
    ):
        self._client = client
        self._context = context
        self._selector = selector
        self.info = info

    async def click(self, timeout: Optional[int] = None) -> None:
        """Click the element.

        Waits for element to be visible, stable, receive events, and enabled.

        Args:
            timeout: Timeout in milliseconds (default: 30000).
        """
        params = {
            "context": self._context,
            "selector": self._selector,
        }
        if timeout is not None:
            params["timeout"] = timeout

        await self._client.send("vibium:click", params)

    async def type(self, text: str, timeout: Optional[int] = None) -> None:
        """Type text into the element.

        Waits for element to be visible, stable, receive events, enabled, and editable.

        Args:
            text: The text to type.
            timeout: Timeout in milliseconds (default: 30000).
        """
        params = {
            "context": self._context,
            "selector": self._selector,
            "text": text,
        }
        if timeout is not None:
            params["timeout"] = timeout

        await self._client.send("vibium:type", params)

    async def text(self) -> str:
        """Get the text content of the element.

        Returns:
            The trimmed text content.
        """
        result = await self._client.send(
            "script.callFunction",
            {
                "functionDeclaration": """(selector) => {
                    const el = document.querySelector(selector);
                    return el ? (el.textContent || '').trim() : null;
                }""",
                "target": {"context": self._context},
                "arguments": [{"type": "string", "value": self._selector}],
                "awaitPromise": False,
                "resultOwnership": "root",
            },
        )

        if result.get("result", {}).get("type") == "null":
            raise ValueError(f"Element not found: {self._selector}")

        return result.get("result", {}).get("value", "")

    async def get_attribute(self, name: str) -> Optional[str]:
        """Get an attribute value from the element.

        Args:
            name: The attribute name.

        Returns:
            The attribute value, or None if not present.
        """
        result = await self._client.send(
            "script.callFunction",
            {
                "functionDeclaration": """(selector, attrName) => {
                    const el = document.querySelector(selector);
                    return el ? el.getAttribute(attrName) : null;
                }""",
                "target": {"context": self._context},
                "arguments": [
                    {"type": "string", "value": self._selector},
                    {"type": "string", "value": name},
                ],
                "awaitPromise": False,
                "resultOwnership": "root",
            },
        )

        if result.get("result", {}).get("type") == "null":
            return None

        return result.get("result", {}).get("value")
