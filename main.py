"""
Oman Gold Price API - Real-time gold pricing for Oman

Fast, reliable gold price API with multi-source validation.
Built by Ibrahim for the Omani developer community.

License: Custom (Free for personal/educational use)
"""
from datetime import datetime, timedelta
from typing import Optional
import asyncio
import logging

from fastapi import FastAPI, Depends, HTTPException, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from sqlalchemy.orm import Session
from sqlalchemy import desc

from config import settings
from database import get_db, init_db
from models import GoldPrice
from schemas import (
    GoldPriceResponse,
    KaratPriceResponse,
    HistoryResponse,
    StatusResponse,
    ErrorResponse
)
from scheduler import start_scheduler, get_update_times

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Oman Gold Price API",
    description="Real-time gold prices in Omani Rial (OMR) for different karats",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# Authentication dependency
async def verify_api_key(x_api_key: str = Header(..., description="Your API key")):
    """Verify API key from header"""
    if x_api_key not in settings.api_keys_list:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key. Please provide a valid X-API-Key header."
        )
    return x_api_key


@app.on_event("startup")
async def startup_event():
    """Initialize database and start scheduler on startup"""
    init_db()
    # Start scheduler in background
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    start_scheduler()
    logger.info("Application started")


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information"""
    return {
        "name": "Oman Gold Price API",
        "version": "1.0.0",
        "description": "Fast gold price API for Oman with multi-source validation",
        "docs": "/docs",
        "github": "https://github.com/IbrahimxDev/oman-gold-price-api",
        "endpoints": {
            "prices": "/api/v1/gold",
            "karat": "/api/v1/gold/{karat}",
            "history": "/api/v1/history",
            "status": "/api/v1/status"
        },
        "author": "Ibrahim"
    }


@app.get(
    "/api/v1/status",
    response_model=StatusResponse,
    tags=["Gold Prices"],
    summary="Get API status"
)
@limiter.limit("60/minute")
async def get_status(request: Request):
    """
    Get the current API status including last and next update times.
    
    No authentication required.
    """
    last_updated, next_update = get_update_times()
    
    return StatusResponse(
        status="ok",
        last_updated=last_updated,
        next_update=next_update,
        update_interval_minutes=settings.update_interval_minutes,
        data_source="CoinGecko",
        currency="OMR"
    )


@app.get(
    "/api/v1/gold",
    response_model=GoldPriceResponse,
    tags=["Gold Prices"],
    summary="Get all gold prices",
    responses={
        401: {"model": ErrorResponse, "description": "Invalid API key"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"}
    }
)
@limiter.limit("60/minute")
async def get_gold_prices(
    request: Request,
    include_raw: bool = False,
    api_key: str = Depends(verify_api_key)
):
    """
    Get current gold prices for all karats in Omani Rial (OMR).
    
    Returns prices per gram for:
    - **24k**: 100% pure gold
    - **22k**: 91.6% gold
    - **21k**: 87.5% gold  
    - **18k**: 75% gold
    
    Requires **X-API-Key** header for authentication.
    Rate limit: 60 requests per minute.
    """
    db: Session = next(get_db())
    
    try:
        latest_price = db.query(GoldPrice).order_by(desc(GoldPrice.timestamp)).first()
        
        if not latest_price:
            raise HTTPException(
                status_code=503,
                detail="No price data available. Please try again in a few minutes."
            )
        
        last_updated, next_update = get_update_times()
        
        prices = {
            "24k": latest_price.price_24k,
            "22k": latest_price.price_22k,
            "21k": latest_price.price_21k,
            "18k": latest_price.price_18k
        }
        
        raw_data = None
        if include_raw:
            raw_data = {
                "gold_price_usd_per_oz": latest_price.gold_price_usd_oz,
                "usd_omr_rate": latest_price.usd_omr_rate
            }
        
        return GoldPriceResponse(
            last_updated=latest_price.timestamp,
            next_update=next_update or (latest_price.timestamp + timedelta(minutes=settings.update_interval_minutes)),
            currency="OMR",
            prices=prices,
            price_per_ounce_usd=latest_price.gold_price_usd_oz,
            raw_data=raw_data
        )
    finally:
        db.close()


@app.get(
    "/api/v1/gold/{karat}",
    response_model=KaratPriceResponse,
    tags=["Gold Prices"],
    summary="Get price for specific karat",
    responses={
        400: {"model": ErrorResponse, "description": "Invalid karat"},
        401: {"model": ErrorResponse, "description": "Invalid API key"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"}
    }
)
@limiter.limit("60/minute")
async def get_karat_price(
    request: Request,
    karat: int,
    api_key: str = Depends(verify_api_key)
):
    """
    Get gold price for a specific karat in Omani Rial (OMR).
    
    Supported karats:
    - **24**: 100% pure gold
    - **22**: 91.6% gold
    - **21**: 87.5% gold
    - **18**: 75% gold
    
    Requires **X-API-Key** header for authentication.
    Rate limit: 60 requests per minute.
    """
    if karat not in settings.karat_purity:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid karat. Supported values: {list(settings.karat_purity.keys())}"
        )
    
    db: Session = next(get_db())
    
    try:
        latest_price = db.query(GoldPrice).order_by(desc(GoldPrice.timestamp)).first()
        
        if not latest_price:
            raise HTTPException(
                status_code=503,
                detail="No price data available. Please try again in a few minutes."
            )
        
        price_map = {
            24: latest_price.price_24k,
            22: latest_price.price_22k,
            21: latest_price.price_21k,
            18: latest_price.price_18k
        }
        
        last_updated, next_update = get_update_times()
        
        return KaratPriceResponse(
            last_updated=latest_price.timestamp,
            next_update=next_update or (latest_price.timestamp + timedelta(minutes=settings.update_interval_minutes)),
            currency="OMR",
            karat=karat,
            price_per_gram=price_map[karat],
            purity_percentage=settings.karat_purity[karat] * 100,
            price_per_ounce_usd=latest_price.gold_price_usd_oz
        )
    finally:
        db.close()


@app.get(
    "/api/v1/history",
    response_model=HistoryResponse,
    tags=["Gold Prices"],
    summary="Get price history",
    responses={
        401: {"model": ErrorResponse, "description": "Invalid API key"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"}
    }
)
@limiter.limit("30/minute")
async def get_price_history(
    request: Request,
    days: int = 7,
    api_key: str = Depends(verify_api_key)
):
    """
    Get historical gold prices for the past N days.
    
    - **days**: Number of days to retrieve (default: 7, max: 30)
    
    Requires **X-API-Key** header for authentication.
    Rate limit: 30 requests per minute.
    """
    days = min(days, 30)  # Cap at 30 days
    
    db: Session = next(get_db())
    
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        prices = db.query(GoldPrice)\
            .filter(GoldPrice.timestamp >= cutoff_date)\
            .order_by(desc(GoldPrice.timestamp))\
            .all()
        
        history = [
            {
                "timestamp": price.timestamp.isoformat(),
                "prices": {
                    "24k": price.price_24k,
                    "22k": price.price_22k,
                    "21k": price.price_21k,
                    "18k": price.price_18k
                }
            }
            for price in prices
        ]
        
        return HistoryResponse(
            count=len(history),
            history=history
        )
    finally:
        db.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
