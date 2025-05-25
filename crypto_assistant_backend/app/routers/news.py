from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional

from app.models.schema import NewsItem

router = APIRouter()

@router.get("/", response_model=List[NewsItem])
async def get_news(symbol: Optional[str] = None, limit: int = 10):
    """
    Kriptovalutákkal kapcsolatos hírek lekérése.
    Ez az endpoint későbbre van tervezve.
    """
    # Placeholder a jövőbeli implementációhoz
    return [
        NewsItem(
            id="1",
            title="Placeholder hír",
            content="Ez egy placeholder hír a jövőbeli implementációhoz.",
            source="Placeholder",
            published_at="2023-01-01T00:00:00Z",
            url="https://example.com",
            symbol=symbol or "CRYPTO"
        )
    ]