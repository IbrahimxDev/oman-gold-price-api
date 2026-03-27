"""Database models for Oman Gold Price API"""
from datetime import datetime
from sqlalchemy import Column, Integer, Float, DateTime, String, JSON
from database import Base


class GoldPrice(Base):
    """Model to store gold price snapshots"""
    __tablename__ = "gold_prices"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Prices per gram in OMR
    price_24k = Column(Float, nullable=False)
    price_22k = Column(Float, nullable=False)
    price_21k = Column(Float, nullable=False)
    price_18k = Column(Float, nullable=False)
    
    # Raw data from APIs
    gold_price_usd_oz = Column(Float, nullable=False)  # Gold price in USD per troy ounce (average)
    usd_omr_rate = Column(Float, nullable=False)       # USD to OMR exchange rate
    
    # Multi-source data (optional)
    sources = Column(JSON, nullable=True)  # Store individual source prices {"currency_api": 4517.32, ...}
    source_count = Column(Integer, default=1)
    variance_percent = Column(Float, nullable=True)


class APIKey(Base):
    """Model to store API keys for authentication"""
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    key_hash = Column(String(64), unique=True, index=True)  # SHA256 hash of API key
    name = Column(String(100), nullable=True)  # Optional name for the key
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Integer, default=1)
