"""Items endpoint for RED9 API."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class Item(BaseModel):
    """Represents an item in the RED9 system."""

    id: int
    name: str
    description: str


class ItemResponse(BaseModel):
    """Response model for items endpoint."""

    items: list[Item]


# Sample data - in a real application this would come from a database
ITEMS = [
    Item(id=1, name="Agent Alpha", description="Primary AI agent for code generation"),
    Item(id=2, name="Agent Beta", description="Secondary AI agent for review and validation"),
    Item(id=3, name="Agent Gamma", description="Specialized agent for security analysis"),
    Item(id=4, name="Agent Delta", description="Performance optimization agent"),
    Item(id=5, name="Agent Epsilon", description="Documentation generation agent"),
]


@router.get("/items", response_model=ItemResponse, tags=["data"])
async def get_items(skip: int = 0, limit: int = 10) -> ItemResponse:
    """Get a list of items with optional pagination."""
    # Ensure limit is reasonable
    if limit > 100:
        limit = 100

    # Apply pagination
    paginated_items = ITEMS[skip : skip + limit]

    return ItemResponse(items=paginated_items)
