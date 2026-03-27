"""Test the multi-source gold price fetcher"""
import asyncio
from scheduler import fetch_gold_price_usd, fetch_usd_omr_rate, calculate_karat_prices

async def main():
    print("=" * 60)
    print("TESTING MULTI-SOURCE GOLD PRICE API")
    print("=" * 60)
    
    # Fetch from multiple sources
    print("\nFetching gold prices from multiple sources...")
    gold_data = await fetch_gold_price_usd()
    
    print("\nFetching USD/OMR exchange rate...")
    usd_omr_rate = await fetch_usd_omr_rate()
    
    # Calculate prices
    prices = calculate_karat_prices(gold_data["price"], usd_omr_rate)
    
    # Display results
    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    
    print("\n[Gold Price Sources]")
    for source, price in gold_data.get("sources", {}).items():
        print(f"  {source}: ${price:,.2f}/oz")
    
    print(f"\n[Average Price] ${gold_data['price']:,.2f}/oz")
    print(f"[Variance] {gold_data.get('variance_percent', 0)}%")
    print(f"[Exchange Rate] 1 USD = {usd_omr_rate} OMR")
    
    print("\n[Gold Prices in OMR per gram]")
    print("-" * 40)
    print(f"  24K: {prices['24k']:.3f} OMR")
    print(f"  22K: {prices['22k']:.3f} OMR")
    print(f"  21K: {prices['21k']:.3f} OMR")
    print(f"  18K: {prices['18k']:.3f} OMR")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
