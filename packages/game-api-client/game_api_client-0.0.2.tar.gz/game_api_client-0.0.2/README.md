# GAME API Client

Simple Python client for the GAME trading API.

## Python Compatibility

- **Python 3.8+** (compatible 3.8 - 3.14)
- **Tested on**: 3.8, 3.9, 3.10, 3.11, 3.12, 3.13, 3.14
- **Recommended**: 3.11+ for best performance

## Installation

### Option 1: pip (recommended)

```bash
pip install game-api-client
```

### Option 2: From source

```bash
git clone https://github.com/groupe-e/game-api-client.git
cd game-api-client
pip install -r requirements.txt
pip install -e .
```

### Option 3: Poetry (for development)

```bash
git clone https://github.com/groupe-e/game-api-client.git
cd game-api-client
poetry install
```

## Quick Start

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your credentials
# GAME_API_TOKEN="your_personal_token"
# GAME_API_URL="https://your-game-api-url.com"
# GAME_API_VERIFY_SSL=false

# Run demo
python demo.py
```

Or programmatically:

```python
import asyncio
from game_client import GameAPI

async def main():
    api = GameAPI(
        token="your_authentik_token",
        base_url="https://your-game-api-url.com"
    )
    
    # Test connection
    if await api.test_connection():
        print("Connected!")
    
    # Get data
    status = await api.get_status()
    trades = await api.get_trades()
    market = await api.get_market_data()

asyncio.run(main())
```

## Environment Variables

Create a `.env` file:

```bash
GAME_API_TOKEN=your_authentik_personal_token
GAME_API_URL=https://your-game-api-url.com
GAME_API_VERIFY_SSL=false
```

## Available Methods

### Connection & Status
- `test_connection()` - Test API connection and authentication
- `get_status()` - Get API status and health information

### Market Data
- `get_market_data()` - Get market data points
- `get_trades(direction=None, duration=None)` - Get trades with optional filters
  - `direction`: "buy" or "sell" (optional)
  - `duration`: Time duration like "15m", "1h" (optional)

### Order Management
- `get_orders(direction=None)` - Get orders with optional filter
  - `direction`: "buy" or "sell" (optional)
- `find_order_by_id(order_id)` - Find specific order by ID
  - `order_id`: Order ID (string or numeric)
- `create_order(order_data)` - Create new order (single or bulk)
  - `order_data`: Order object or `{"orders": [...]}` for bulk
- `delete_order(order_id)` - Delete order by ID
  - `order_id`: Order ID (handles both string and numeric formats)

### Spot Data
- `get_spot_data()` - Get spot market data
- `get_spot_status()` - Get spot API status

## Usage Examples

### Basic Usage
```python
import asyncio
from game_client import GameAPI

async def main():
    api = GameAPI(
        token="your_authentik_token",
        base_url="https://your-game-api-url.com",
        verify_ssl=False  # Set to True for production
    )
    
    # Test connection
    if await api.test_connection():
        print("✅ Connected to API!")
    
    # Get basic data
    status = await api.get_status()
    market_data = await api.get_market_data()
    
    print(f"API Status: {status['status']}")
    print(f"Market data points: {len(market_data)}")

asyncio.run(main())
```

### Order Management
```python
async def order_examples():
    api = GameAPI(token="your_token", base_url="https://api.example.com")
    
    # Get all orders
    orders = await api.get_orders()
    print(f"Found {len(orders)} orders")
    
    # Get only buy orders
    buy_orders = await api.get_orders(direction="buy")
    
    # Create a single order
    from datetime import datetime, timedelta
    future_time = datetime.now() + timedelta(hours=4)
    
    single_order = {
        "side": "buy",
        "price": 100.0,
        "volume": 1.0,
        "date": future_time.strftime("%Y-%m-%d"),
        "start_time": "14:00",
        "end_time": "15:00", 
        "duration": "15m",
        "tz_offset_hours": 0
    }
    
    result = await api.create_order(single_order)
    print(f"Created order: {result['order_id']}")
    
    # Create bulk orders
    bulk_orders = {
        "orders": [
            {
                "side": "buy",
                "price": 100.0,
                "volume": 1.0,
                "date": future_time.strftime("%Y-%m-%d"),
                "start_time": "14:00",
                "end_time": "15:00",
                "duration": "15m",
                "tz_offset_hours": 0
            },
            {
                "side": "sell", 
                "price": 200.0,
                "volume": 0.5,
                "date": future_time.strftime("%Y-%m-%d"),
                "start_time": "14:00",
                "end_time": "15:00",
                "duration": "15m",
                "tz_offset_hours": 0
            }
        ]
    }
    
    bulk_result = await api.create_order(bulk_orders)
    print(f"Created {len(bulk_result['created'])} orders")
    
    # Find specific order
    order = await api.find_order_by_id(result['order_id'])
    if order:
        print(f"Found order: {order['direction']} {order['volume']} @ {order['price']}")
    
    # Delete order
    delete_result = await api.delete_order(result['order_id'])
    print(f"Order deleted: {delete_result['status']}")
```

### Market Data with Filters
```python
async def market_data_examples():
    api = GameAPI(token="your_token", base_url="https://api.example.com")
    
    # Get all trades
    all_trades = await api.get_trades()
    
    # Get only buy trades
    buy_trades = await api.get_trades(direction="buy")
    
    # Get trades with specific duration
    short_trades = await api.get_trades(duration="15m")
    
    # Get spot data
    spot_data = await api.get_spot_data()
    spot_status = await api.get_spot_status()
    
    print(f"Total trades: {len(all_trades)}")
    print(f"Buy trades: {len(buy_trades)}")
    print(f"Short duration trades: {len(short_trades)}")
    print(f"Spot data points: {len(spot_data)}")
    print(f"Spot status: {spot_status['status']}")
```

### Error Handling
```python
async def error_handling_example():
    api = GameAPI(token="your_token", base_url="https://api.example.com")
    
    try:
        # This might fail if order data is invalid
        result = await api.create_order({"invalid": "data"})
    except GameAPIError as e:
        print(f"API Error: {e}")
    
    try:
        # This might fail if order doesn't exist
        await api.delete_order("non_existent_id")
    except GameAPIError as e:
        print(f"Delete failed: {e}")
    
    # Safe order lookup
    order = await api.find_order_by_id("some_id")
    if order is None:
        print("Order not found")
    else:
        print(f"Found order: {order}")
```

## Order Data Format

### Required Fields
All orders must include these required fields:

```python
{
    "side": "buy",           # REQUIRED: "buy" or "sell"
    "price": 100.0,          # REQUIRED: Positive number (> 0)
    "volume": 1.0,           # REQUIRED: Positive number (> 0)  
    "date": "2024-01-15",    # REQUIRED: Future date in YYYY-MM-DD format
    "start_time": "14:00",   # REQUIRED: HH:MM format (future time)
    "end_time": "15:00",     # REQUIRED: HH:MM format (after start_time)
    "duration": "15m",       # REQUIRED: Time duration ("15m", "30m", "1h", etc.)
    "tz_offset_hours": 0     # REQUIRED: Timezone offset from UTC
}
```

### Field Constraints

#### side
- **Values**: `"buy"` or `"sell"` (case-sensitive)
- **Required**: Yes

#### price  
- **Type**: Positive number (float or int)
- **Required**: Yes
- **Constraints**: Must be > 0
- **Example**: `100.0`, `99.5`

#### volume
- **Type**: Positive number (float or int)  
- **Required**: Yes
- **Constraints**: Must be > 0
- **Example**: `1.0`, `0.5`

#### date
- **Type**: String
- **Format**: YYYY-MM-DD
- **Required**: Yes
- **Constraints**: Must be a future date
- **Example**: `"2024-01-15"`

#### start_time / end_time
- **Type**: String
- **Format**: HH:MM (24-hour)
- **Required**: Yes
- **Constraints**: 
  - Must be future times
  - end_time must be after start_time
- **Example**: `"14:00"`, `"15:30"`

#### duration
- **Type**: String
- **Required**: Yes
- **Common values**: `"15m"`, `"30m"`, `"1h"`, `"4h"`
- **Example**: `"15m"` (15 minutes)

#### tz_offset_hours
- **Type**: Integer
- **Required**: Yes
- **Range**: Typically -12 to +14
- **Example**: `0` (UTC), `1` (UTC+1), `-5` (UTC-5)

### Complete Order Examples

#### Valid Buy Order
```python
buy_order = {
    "side": "buy",
    "price": 150.25,
    "volume": 2.5,
    "date": "2024-12-15",
    "start_time": "14:00",
    "end_time": "14:15", 
    "duration": "15m",
    "tz_offset_hours": 1  # CET (UTC+1)
}
```

#### Valid Sell Order
```python
sell_order = {
    "side": "sell",
    "price": 200.0,
    "volume": 1.0,
    "date": "2024-12-15",
    "start_time": "15:30",
    "end_time": "16:00",
    "duration": "30m", 
    "tz_offset_hours": 0  # UTC
}
```

### Time Validation Rules

1. **Date must be in the future** - Past dates will be rejected
2. **Times must be in the future** - Current time already passed will be rejected  
3. **End time > Start time** - Duration must be positive
4. **Duration should match time window** - (end_time - start_time) should equal duration

### Common Validation Errors

```python
# ❌ Missing required field
{"side": "buy", "price": 100}  # Missing volume, date, etc.

# ❌ Invalid side
{"side": "invalid", ...}  # Must be "buy" or "sell"

# ❌ Negative price/volume  
{"side": "buy", "price": -10, "volume": 1.0, ...}

# ❌ Past date
{"side": "buy", "date": "2020-01-01", ...}

# ❌ Invalid time format
{"side": "buy", "start_time": "2:00 PM", ...}  # Must be HH:MM

# ❌ End time before start time
{"side": "buy", "start_time": "15:00", "end_time": "14:00", ...}
```

### Bulk Orders Format

```python
bulk_orders = {
    "orders": [
        # Order 1
        {
            "side": "buy",
            "price": 100.0,
            "volume": 1.0,
            "date": "2024-12-15",
            "start_time": "14:00",
            "end_time": "14:15",
            "duration": "15m",
            "tz_offset_hours": 0
        },
        # Order 2  
        {
            "side": "sell",
            "price": 200.0,
            "volume": 0.5,
            "date": "2024-12-15", 
            "start_time": "14:30",
            "end_time": "15:00",
            "duration": "30m",
            "tz_offset_hours": 0
        },
        # ... more orders (up to API limits)
    ]
}
```

### Helper Function for Order Creation

```python
from datetime import datetime, timedelta

def create_order_data(side, price, volume, hours_in_future=4):
    """Helper to create valid order data"""
    future_time = datetime.now() + timedelta(hours=hours_in_future)
    
    # Round to next quarter hour
    minutes = future_time.minute
    if minutes < 15:
        future_time = future_time.replace(minute=15, second=0, microsecond=0)
    elif minutes < 30:
        future_time = future_time.replace(minute=30, second=0, microsecond=0)
    elif minutes < 45:
        future_time = future_time.replace(minute=45, second=0, microsecond=0)
    else:
        future_time = future_time.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    
    future_end = future_time + timedelta(minutes=15)
    
    return {
        "side": side,
        "price": float(price),
        "volume": float(volume),
        "date": future_time.strftime("%Y-%m-%d"),
        "start_time": future_time.strftime("%H:%M"),
        "end_time": future_end.strftime("%H:%M"),
        "duration": "15m",
        "tz_offset_hours": 0
    }

# Usage
order = create_order_data("buy", 100.0, 1.0)
result = await api.create_order(order)
```

## Response Formats

### Order Creation Response
```python
# Single order
{
    "order_id": "ord_abc123",
    "created_at": "2024-01-15T14:00:00Z",
    "direction": "buy",
    "volume": 1.0,
    "price": 100.0,
    "state": "Displayed",
    "contract": "BASE-QUOTE",
    "trader": "your_trader_name",
    "date": "2024-01-15",
    "start_time": "14:00",
    "end_time": "14:15",
    "duration": "15m",
    "tz_offset_hours": 0,
    "updated_at": "2024-01-15T14:00:00Z"
}

# Bulk orders
{
    "requested": 2,
    "created": [
        {
            "index": 0,
            "result": {
                "order_id": "ord_abc123",
                "created_at": "2024-01-15T14:00:00Z",
                "direction": "buy",
                "volume": 1.0,
                "price": 100.0,
                "state": "Displayed",
                "contract": "BASE-QUOTE",
                "trader": "your_trader_name",
                "date": "2024-01-15",
                "start_time": "14:00",
                "end_time": "14:15",
                "duration": "15m",
                "tz_offset_hours": 0,
                "updated_at": "2024-01-15T14:00:00Z"
            }
        },
        {
            "index": 1,
            "result": {
                "order_id": "ord_def456",
                "created_at": "2024-01-15T14:00:00Z",
                "direction": "sell",
                "volume": 0.5,
                "price": 200.0,
                "state": "Displayed",
                "contract": "BASE-QUOTE",
                "trader": "your_trader_name",
                "date": "2024-01-15",
                "start_time": "14:30",
                "end_time": "15:00",
                "duration": "30m",
                "tz_offset_hours": 0,
                "updated_at": "2024-01-15T14:00:00Z"
            }
        }
    ],
    "failed": [
        {
            "index": 2,
            "error": "Invalid price: must be positive number"
        }
    ]
}
```

### Order Data (from get_orders)
```python
{
    "order_id": 1234,                    # Numeric ID for deletion
    "direction": "buy",                  # "buy" or "sell"
    "volume": 1.0,                       # Order volume
    "price": 100.0,                      # Order price
    "state": "Displayed",                 # Order state
    "contract": "BASE-QUOTE",             # Trading pair
    "trader": "your_trader_name",         # Trader identifier
    "date": "2024-01-15",                # Order date
    "start_time": "14:00",               # Start time
    "end_time": "14:15",                 # End time
    "duration": "15m",                   # Duration
    "tz_offset_hours": 0,                # Timezone offset
    "created_at": "2024-01-15T14:00:00Z", # Creation timestamp
    "updated_at": "2024-01-15T14:00:00Z", # Last update timestamp
    "executed_volume": 0.0,              # Volume already executed (if any)
    "remaining_volume": 1.0,             # Volume remaining to execute
    "average_price": null,               # Average execution price (if executed)
    "execution_count": 0,                # Number of executions
    "total_value": 100.0,                # Total order value (volume × price)
    "fees": 0.0,                         # Trading fees
    "metadata": {}                       # Additional metadata
}
```

### Market Data Response
```python
[
    {
        "timestamp": "2024-01-15T14:00:00Z",
        "contract": "BASE-QUOTE",
        "price": 100.5,
        "volume": 1500.0,
        "bid": 100.4,
        "ask": 100.6,
        "spread": 0.2,
        "high_24h": 105.0,
        "low_24h": 95.0,
        "volume_24h": 50000.0,
        "change_24h": 2.5,
        "change_percent_24h": 2.56
    }
]
```

### Trades Data Response
```python
[
    {
        "trade_id": "trade_abc123",
        "contract": "BASE-QUOTE",
        "direction": "buy",
        "volume": 1.0,
        "price": 100.5,
        "timestamp": "2024-01-15T14:00:00Z",
        "buyer": "buyer_name",
        "seller": "seller_name",
        "fees": 0.25,
        "duration": "15m",
        "execution_time": "2024-01-15T14:07:30Z"
    }
]
```

### Spot Data Response
```python
{
    "contract": "BASE-QUOTE",
    "price": 100.5,
    "volume": 1500.0,
    "bid": 100.4,
    "ask": 100.6,
    "spread": 0.2,
    "high_24h": 105.0,
    "low_24h": 95.0,
    "volume_24h": 50000.0,
    "change_24h": 2.5,
    "change_percent_24h": 2.56,
    "timestamp": "2024-01-15T14:00:00Z",
    "order_book": {
        "bids": [
            {"price": 100.4, "volume": 500.0},
            {"price": 100.3, "volume": 300.0}
        ],
        "asks": [
            {"price": 100.6, "volume": 400.0},
            {"price": 100.7, "volume": 200.0}
        ]
    }
}
```

### API Status Response
```python
{
    "status": "healthy",
    "version": "1.2.3",
    "timestamp": "2024-01-15T14:00:00Z",
    "services": {
        "orders": "operational",
        "trades": "operational", 
        "market_data": "operational",
        "spot": "operational"
    },
    "uptime": 86400,
    "response_time_ms": 45,
    "rate_limit": {
        "requests_per_minute": 1000,
        "requests_remaining": 999,
        "reset_time": "2024-01-15T14:01:00Z"
    }
}
```

### Spot Status Response
```python
{
    "status": "operational",
    "timestamp": "2024-01-15T14:00:00Z",
    "active_contracts": ["BASE-QUOTE", "OTHER-PAIR"],
    "market_open": true,
    "next_update": "2024-01-15T14:01:00Z",
    "last_update": "2024-01-15T13:59:00Z"
}
```

## Error Handling

The client provides comprehensive error handling:

### GameAPIError
All API errors raise `GameAPIError` with descriptive messages:

```python
from game_client import GameAPI, GameAPIError

async def example():
    api = GameAPI(token="token", base_url="https://api.example.com")
    
    try:
        await api.create_order({"invalid": "data"})
    except GameAPIError as e:
        print(f"API Error: {e}")
        # Output: "API Error: Single order: Missing required field 'side'"
```

### Common Errors
- **Authentication**: Invalid token or connection issues
- **Validation**: Missing required fields or invalid values
- **Not Found**: Order ID doesn't exist
- **Network**: Connection timeout or server errors

### Best Practices

1. **Always handle errors**
```python
try:
    result = await api.create_order(order_data)
except GameAPIError as e:
    logger.error(f"Order creation failed: {e}")
    return None
```

2. **Test connection first**
```python
if not await api.test_connection():
    print("Cannot connect to API")
    return
```

3. **Use find_order_by_id for safe lookups**
```python
order = await api.find_order_by_id(order_id)
if order is None:
    print("Order not found")
else:
    print(f"Found: {order}")
```

4. **Validate order data before sending**
```python
# The client validates automatically, but you can pre-validate
required_fields = ["side", "price", "volume", "date", "start_time", "end_time"]
for field in required_fields:
    if field not in order_data:
        raise ValueError(f"Missing required field: {field}")
```

## Advanced Usage

### Custom Timeout and SSL
```python
api = GameAPI(
    token="your_token",
    base_url="https://api.example.com",
    verify_ssl=True,        # Enable SSL verification (production)
    timeout=60              # Custom timeout in seconds
)
```

### Bulk Operations
```python
# Create multiple orders efficiently
bulk_orders = {
    "orders": [
        {"side": "buy", "price": 100, "volume": 1, ...},
        {"side": "sell", "price": 200, "volume": 0.5, ...},
        # ... up to 100 orders
    ]
}

result = await api.create_order(bulk_orders)
print(f"Created: {len(result['created'])}, Failed: {len(result['failed'])}")
```

### Rate Limiting
The client handles rate limiting automatically through token management, but you should implement your own rate limiting for bulk operations:

```python
import asyncio

async def safe_bulk_create(api, orders_list, batch_size=10):
    """Create orders in batches to avoid rate limits"""
    results = []
    
    for i in range(0, len(orders_list), batch_size):
        batch = orders_list[i:i + batch_size]
        bulk_data = {"orders": batch}
        
        try:
            result = await api.create_order(bulk_data)
            results.extend(result.get('created', []))
            
            # Small delay between batches
            if i + batch_size < len(orders_list):
                await asyncio.sleep(1)
                
        except GameAPIError as e:
            print(f"Batch {i//batch_size + 1} failed: {e}")
    
    return results
```

## Testing

```bash
# Install dependencies
pip install -r requirements.txt
pip install -e .

# Install test dependencies
pip install pytest pytest-asyncio pytest-cov

# Run tests
pytest tests/ -v --cov=game_client
```

## Docker

```bash
# Build
docker build -f Dockerfile.demo -t game-api-client .

# Option 1: Run with environment variables (recommended for production)
docker run --rm \
  -e GAME_API_TOKEN="your_token" \
  -e GAME_API_URL="https://your-game-api-url.com" \
  -e GAME_API_VERIFY_SSL=false \
  game-api-client

# Option 2: Run with .env file (for development)
docker run --rm \
  -v $(pwd)/.env:/app/.env:ro \
  game-api-client

# Option 3: Run with custom command
docker run --rm \
  -e GAME_API_TOKEN="your_token" \
  -e GAME_API_URL="https://your-game-api-url.com" \
  -e GAME_API_VERIFY_SSL=false \
  game-api-client python example.py
```

## Development

```bash
# Setup development environment
poetry install

# Run example
python example.py

# Run tests
poetry run pytest tests/ -v
```
