"""Configuration settings for Oman Gold Price API"""
import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import field_validator
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """Application settings"""
    
    # Authentication
    api_keys: str = "demo_key_123"  # Comma-separated string
    
    # Database
    database_url: str = "sqlite:///./gold_prices.db"
    
    # Scheduler
    update_interval_minutes: int = 1
    
    # Gold purity percentages
    karat_purity: dict = {
        24: 1.0,      # 100% gold
        22: 0.916,    # 91.6% gold
        21: 0.875,    # 87.5% gold
        18: 0.75,     # 75% gold
    }
    
    # Troy ounce to grams conversion
    troy_ounce_grams: float = 31.1035
    
    @property
    def api_keys_list(self) -> List[str]:
        """Parse comma-separated API keys into a list"""
        return [key.strip() for key in self.api_keys.split(",")]
    
    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
