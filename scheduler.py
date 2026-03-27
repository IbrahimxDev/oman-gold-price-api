"""Background scheduler for fetching gold prices from CoinGecko"""
import httpx
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import logging

from config import settings
from database import SessionLocal
from models import GoldPrice

logger = logging.getLogger(__name__)

last_update_time: datetime = None
next_update_time: datetime = None


async def fetch_gold_price_usd() -> float:
    """
    Fetch gold price in USD per troy ounce from CoinGecko.
    Uses PAXG (tokenized gold) as price reference.
    """
    try:
        async with httpx.AsyncClient() as client:
            url = "https://api.coingecko.com/api/v3/simple/price?ids=pax-gold&vs_currencies=usd"
            response = await client.get(url, timeout=15, follow_redirects=True)
            if response.status_code == 200:
                data = response.json()
                price = data.get("pax-gold", {}).get("usd")
                if price:
                    logger.info(f"[CoinGecko] Gold: ${price:.2f}/oz")
                    return float(price)
    except Exception as e:
        logger.warning(f"[CoinGecko] Failed: {e}")
    
    logger.error("CoinGecko API failed!")
    return 2950.00


async def fetch_usd_omr_rate() -> float:
    """Fetch live USD to OMR exchange rate"""
    
    async with httpx.AsyncClient() as client:
        try:
            url = "https://open.er-api.com/v6/latest/USD"
            response = await client.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            rate = data.get("rates", {}).get("OMR")
            if rate:
                logger.info(f"[Exchange Rate] 1 USD = {rate} OMR")
                return rate
        except Exception as e:
            logger.warning(f"[Exchange Rate] Failed: {e}")

    logger.warning("Using fixed peg rate")
    return 0.384965


def calculate_karat_prices(gold_price_usd_oz: float, usd_omr_rate: float) -> dict:
    """Calculate gold prices per gram for each karat"""
    price_per_gram_omr = (gold_price_usd_oz / settings.troy_ounce_grams) * usd_omr_rate
    
    prices = {}
    for karat, purity in settings.karat_purity.items():
        prices[f"{karat}k"] = round(price_per_gram_omr * purity, 3)
    
    return prices


async def update_gold_prices():
    """Fetch and store gold prices"""
    global last_update_time, next_update_time
    
    logger.info("Fetching gold prices from CoinGecko...")
    
    try:
        gold_price_usd = await fetch_gold_price_usd()
        usd_omr_rate = await fetch_usd_omr_rate()
        prices = calculate_karat_prices(gold_price_usd, usd_omr_rate)
        
        db: Session = SessionLocal()
        try:
            gold_price = GoldPrice(
                timestamp=datetime.utcnow(),
                price_24k=prices["24k"],
                price_22k=prices["22k"],
                price_21k=prices["21k"],
                price_18k=prices["18k"],
                gold_price_usd_oz=gold_price_usd,
                usd_omr_rate=usd_omr_rate,
                sources={"coingecko_paxg": gold_price_usd},
                source_count=1,
                variance_percent=None
            )
            db.add(gold_price)
            db.commit()
            
            last_update_time = datetime.utcnow()
            next_update_time = last_update_time + timedelta(minutes=settings.update_interval_minutes)
            
            logger.info(f"Updated: 24k={prices['24k']:.3f}, 22k={prices['22k']:.3f}, 21k={prices['21k']:.3f}, 18k={prices['18k']:.3f} OMR/g")
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error: {e}")


def start_scheduler():
    """Start the background scheduler"""
    scheduler = BackgroundScheduler()
    
    scheduler.add_job(
        func=lambda: __import__("asyncio").new_event_loop().run_until_complete(update_gold_prices()),
        trigger=IntervalTrigger(minutes=settings.update_interval_minutes),
        id="update_gold_prices",
        name="Update gold prices from CoinGecko",
        replace_existing=True
    )
    
    scheduler.start()
    logger.info(f"Scheduler started ({settings.update_interval_minutes} min interval)")
    
    # Run initial update in background
    import threading
    thread = threading.Thread(target=lambda: __import__("asyncio").new_event_loop().run_until_complete(update_gold_prices()))
    thread.start()
    
    return scheduler


def get_update_times() -> tuple:
    return last_update_time, next_update_time
