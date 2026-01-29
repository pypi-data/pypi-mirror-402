"""Vibe class - the main browser automation interface."""

import base64
from typing import Optional

from .client import BiDiClient
from .clicker import ClickerProcess
from .element import BoundingBox, Element, ElementInfo


class Vibe:
    """Main browser automation interface.

    Provides methods to navigate, interact with elements, and take screenshots.
    """

    def __init__(self, client: BiDiClient, process: Optional[ClickerProcess] = None):
        self._client = client
        self._process = process
        self._context: Optional[str] = None

    async def _get_context(self) -> str:
        """Get the browsing context ID."""
        if self._context:
            return self._context

        result = await self._client.send("browsingContext.getTree", {})
        contexts = result.get("contexts", [])
        if not contexts:
            raise RuntimeError("No browsing context available")

        self._context = contexts[0]["context"]
        return self._context

    async def go(self, url: str) -> None:
        """Navigate to a URL.

        Args:
            url: The URL to navigate to.
        """
        context = await self._get_context()
        await self._client.send(
            "browsingContext.navigate",
            {
                "context": context,
                "url": url,
                "wait": "complete",
            },
        )

    async def screenshot(self) -> bytes:
        """Capture a screenshot of the viewport.

        Returns:
            PNG image data as bytes.
        """
        context = await self._get_context()
        result = await self._client.send(
            "browsingContext.captureScreenshot",
            {"context": context},
        )
        return base64.b64decode(result["data"])

    async def find(self, selector: str, timeout: Optional[int] = None) -> Element:
        """Find an element by CSS selector.

        Waits for the element to exist before returning.

        Args:
            selector: CSS selector.
            timeout: Timeout in milliseconds (default: 30000).

        Returns:
            An Element instance.
        """
        context = await self._get_context()

        params = {
            "context": context,
            "selector": selector,
        }
        if timeout is not None:
            params["timeout"] = timeout

        result = await self._client.send("vibium:find", params)

        box_data = result["box"]
        info = ElementInfo(
            tag=result["tag"],
            text=result["text"],
            box=BoundingBox(
                x=box_data["x"],
                y=box_data["y"],
                width=box_data["width"],
                height=box_data["height"],
            ),
        )

        return Element(self._client, context, selector, info)

    async def quit(self) -> None:
        """Close the browser and clean up resources."""
        await self._client.close()
        if self._process:
            await self._process.stop()
