"""Pydantic schemas for API validation and serialization"""
from datetime import datetime
from typing import Dict, Optional
from pydantic import BaseModel, Field


class GoldPriceResponse(BaseModel):
    """Response schema for gold prices"""
    last_updated: datetime
    next_update: datetime
    currency: str = "OMR"
    prices: Dict[str, float] = Field(
        ...,
        example={
            "24k": 25.50,
            "22k": 23.36,
            "21k": 22.31,
            "18k": 19.12
        }
    )
    price_per_ounce_usd: Optional[float] = Field(
        None,
        description="Gold price per troy ounce in USD",
        example=4458.03
    )
    raw_data: Optional[Dict] = None


class KaratPriceResponse(BaseModel):
    """Response schema for single karat price"""
    last_updated: datetime
    next_update: datetime
    currency: str = "OMR"
    karat: int
    price_per_gram: float
    purity_percentage: float
    price_per_ounce_usd: Optional[float] = Field(
        None,
        description="Gold price per troy ounce in USD",
        example=4458.03
    )


class HistoryResponse(BaseModel):
    """Response schema for price history"""
    count: int
    history: list


class StatusResponse(BaseModel):
    """Response schema for API status"""
    status: str = "ok"
    last_updated: Optional[datetime] = None
    next_update: Optional[datetime] = None
    update_interval_minutes: int
    data_source: str = "GoldAPI.io"
    currency: str = "OMR"


class ErrorResponse(BaseModel):
    """Response schema for errors"""
    error: str
    detail: Optional[str] = None
