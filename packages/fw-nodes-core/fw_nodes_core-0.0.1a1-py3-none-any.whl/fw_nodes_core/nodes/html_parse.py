"""HTML parsing node using parsel with CSS selectors."""

from typing import Any, Union

from flowire_sdk import BaseNode, BaseNodeOutput, NodeExecutionContext, NodeMetadata
from parsel import Selector
from pydantic import BaseModel, Field


class HTMLParseInput(BaseModel):
    html: str = Field(..., description="HTML content to parse. Use Insert button to reference data from other nodes.")
    selector: str = Field(..., description="CSS selector to extract elements (e.g., 'div.content', 'a.link', 'h1')")


class HTMLParseOutput(BaseNodeOutput):
    elements: Union[str, list[str]] = Field(..., description="Selected HTML as string or list of strings")
    count: int = Field(..., description="Number of elements matched")


class HTMLParseNode(BaseNode):
    """Parse HTML using CSS selectors and extract matching elements."""

    input_schema = HTMLParseInput
    output_schema = HTMLParseOutput

    metadata = NodeMetadata(
        name="Parse HTML",
        description="Parse HTML using CSS selectors and extract matching elements",
        category="data",
        icon="🔍",
        color="#FF5722",
    )

    async def execute_logic(
        self,
        validated_inputs: dict[str, Any],
        context: NodeExecutionContext,
    ) -> dict[str, Any]:
        """Parse HTML and extract elements using CSS selector."""
        html = validated_inputs["html"]
        selector = validated_inputs["selector"]

        if not html:
            raise ValueError("HTML content is required. Provide 'html' field or connect from a previous node.")

        if not selector:
            raise ValueError("CSS selector is required")

        # Parse HTML with parsel
        sel = Selector(text=html)

        # Extract elements using CSS selector
        elements = sel.css(selector).getall()

        # Return as string if single result, list if multiple
        if len(elements) == 0:
            result = ""
        elif len(elements) == 1:
            result = elements[0]
        else:
            result = elements

        # Return Pydantic instance
        return HTMLParseOutput(
            elements=result,
            count=len(elements),
        )
