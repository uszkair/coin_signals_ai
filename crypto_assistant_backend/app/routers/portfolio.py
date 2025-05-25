from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional

from app.models.schema import PortfolioItem, PortfolioSummary

router = APIRouter()

@router.get("/", response_model=PortfolioSummary)
async def get_portfolio():
    """
    Portfólió összegzés lekérése.
    Ez az endpoint későbbre van tervezve.
    """
    # Placeholder a jövőbeli implementációhoz
    return PortfolioSummary(
        total_value=10000.0,
        profit_loss=500.0,
        profit_loss_percentage=5.0,
        assets=[
            PortfolioItem(
                symbol="BTCUSDT",
                amount=0.5,
                value=8000.0,
                purchase_price=7500.0,
                current_price=16000.0,
                profit_loss=500.0,
                profit_loss_percentage=6.67
            ),
            PortfolioItem(
                symbol="ETHUSDT",
                amount=1.0,
                value=2000.0,
                purchase_price=2000.0,
                current_price=2000.0,
                profit_loss=0.0,
                profit_loss_percentage=0.0
            )
        ]
    )