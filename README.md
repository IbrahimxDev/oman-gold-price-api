# ⚡ Oman Gold Price API

> Real-time gold pricing API built for developers in Oman

Fast, reliable gold price API powered by CoinGecko. Get prices in Omani Rial for 24k, 22k, 21k, and 18k gold.

---

## Why This API?

- **🚀 Fast** - Lightweight FastAPI backend
- **🔒 Reliable** - CoinGecko PAXG data (tokenized gold)
- **🇴🇲 Local** - Prices in Omani Rial (OMR)
- **💯 Free** - No API keys required
- **📊 Accurate** - Live gold prices updated every 10 minutes

---

## Data Source

| Source | Type | Refresh Rate | Description |
|--------|------|--------------|-------------|
| CoinGecko PAXG | Crypto Exchange | ~1 min | Tokenized gold on Ethereum |

PAXG (Pax Gold) is a crypto token backed by physical gold, making it an excellent real-time price reference.

**Update interval:** Every 1 minute

---

## Quick Start

```bash
# Clone & Run
git clone https://github.com/IbrahimxDev/oman-gold-price-api.git
cd oman-gold-price-api
pip install -r requirements.txt
python main.py
```

API runs on `http://localhost:8080`

---

## Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/` | ❌ | API info |
| GET | `/api/v1/status` | ❌ | System status |
| GET | `/api/v1/gold` | ✅ | All gold prices |
| GET | `/api/v1/gold/{karat}` | ✅ | Specific karat price |
| GET | `/api/v1/history?days=7` | ✅ | Price history |

### Authentication

```bash
curl -H "X-API-Key: demo_key_123" http://localhost:8080/api/v1/gold
```

---

## Example Response

**GET /api/v1/gold**

```json
{
  "last_updated": "2026-03-27T06:07:57Z",
  "next_update": "2026-03-27T06:17:57Z",
  "currency": "OMR",
  "prices": {
    "24k": 55.104,
    "22k": 50.475,
    "21k": 48.216,
    "18k": 41.328
  },
  "price_per_ounce_usd": 4465.00
}
```

---

## Price Calculation

```
1. Fetch XAU/USD from CoinGecko (PAXG)
2. Get live USD→OMR exchange rate
3. Convert ounce → gram (÷ 31.1035)
4. Apply karat purity multiplier
```

| Karat | Purity |
|-------|--------|
| 24K | 100% |
| 22K | 91.6% |
| 21K | 87.5% |
| 18K | 75% |

---

## Configuration

Environment variables (`.env`):

```env
API_KEYS=demo_key_123
DATABASE_URL=sqlite:///./gold_prices.db
UPDATE_INTERVAL_MINUTES=10
```

---

## Tech Stack

- **FastAPI** - Modern async web framework
- **SQLAlchemy** - ORM for SQLite
- **APScheduler** - Background updates
- **httpx** - Async HTTP client

---

## License

Custom license - Free for personal/educational use. Commercial use requires permission.

---

## Author

**Ibrahim** - [@IbrahimxDev](https://github.com/IbrahimxDev)

---

Built for the Omani developer community 🇴🇲
