---
name: crypto
description: (CryptoView - Skill) 加密货币与贵金属市场数据分析。获取 OKX 交易所的 K线、资金费率、持仓量、多空比等实时数据, 并且进行技术分析的脚本。MUST USE for any crypto/market data queries.
mcp:
  crypto:
    command: python
    args: ["D:/Crypto/.opencode/skills/crypto/scripts/crypto_mcp_server.py"]
    env:
      PYTHONIOENCODING: utf-8
---

# Crypto Data Skill

OKX 交易所实时加密货币市场数据访问能力以及对获得是实时数据进行技术分析的能力. 

---

## Skill Scope & Boundaries

### This Skill PROVIDES (Raw Data Only)
- K-line / Candlestick data
- Funding rate history
- Open interest snapshots
- Long/Short ratio data
- Liquidation records

### This Skill does NOT HANDLE
- Signal interpretation → Refer to `indicators.md` in ` references` flods.
- Trade decisions → Handled by Agent policy (`AGENTS.md`)
- Risk management → Handled by Agent policy (`AGENTS.md`)

**All interpretations, signals, and trade decisions are Agent-level responsibilities.**

---

## Trigger Conditions

**MUST load this Skill when:**

- Querying any crypto price (BTC, ETH, BNB, ZEC, SOL, XAU)
- Technical analysis requests
- Funding rate / Open interest / Long-short ratio queries
- Market sentiment analysis

---

## Available Tools

Call via `skill_mcp(mcp_name="crypto", tool_name="...", arguments={...})`

### 1. get_candles - K-Line Data

| Parameter | Type | Description |
|-----------|------|-------------|
| `inst_id` | string | Trading pair, e.g., "BTC-USDT" |
| `bar` | string | Period: 1m, 5m, 15m, 30m, 1H, 4H, 1D, 1W |
| `limit` | integer | Data count (max 100) |

**Returns**: DataFrame with columns: `datetime`, `open`, `high`, `low`, `close`, `vol`

### 2. get_funding_rate - Funding Rate

| Parameter | Type | Description |
|-----------|------|-------------|
| `inst_id` | string | Perpetual contract, e.g., "BTC-USDT-SWAP" |
| `limit` | integer | Data count (max 100) |

**Returns**: Row 0 = current prediction, subsequent rows = settled history

### 3. get_open_interest - Open Interest

| Parameter | Type | Description |
|-----------|------|-------------|
| `inst_id` | string | Perpetual contract, e.g., "BTC-USDT-SWAP" |
| `period` | string | Granularity: 5m, 1H, 1D |
| `limit` | integer | Data count (max 100) |

**Returns**: Row 0 = realtime data, subsequent rows = historical snapshots

### 4. get_long_short_ratio - Long/Short Ratio

| Parameter | Type | Description |
|-----------|------|-------------|
| `ccy` | string | Currency, e.g., "BTC", "ETH" |
| `period` | string | Granularity: 5m, 1H, 1D |
| `limit` | integer | Data count (max 100) |

### 5. get_liquidation - Liquidation Data

| Parameter | Type | Description |
|-----------|------|-------------|
| `inst_id` | string | Perpetual contract, e.g., "BTC-USDT-SWAP" |
| `state` | string | Order state: "filled" or "unfilled" |
| `limit` | integer | Data count (max 100) |

**Returns**: Columns: `datetime`, `side` (sell=long liquidated, buy=short liquidated), `bkPx`, `sz`

---

## Supported Trading Pairs

| Code | Spot | Perpetual Contract |
|------|------|-------------------|
| BTC | BTC-USDT | BTC-USDT-SWAP |
| ETH | ETH-USDT | ETH-USDT-SWAP |
| BNB | BNB-USDT | BNB-USDT-SWAP |
| ZEC | ZEC-USDT | ZEC-USDT-SWAP |
| SOL | SOL-USDT | SOL-USDT-SWAP |
| XAU | - | XAU-USDT-SWAP |

---

## Usage Examples

```python
# Get BTC 1-hour K-lines
skill_mcp(
  mcp_name="crypto",
  tool_name="get_candles",
  arguments={"inst_id": "BTC-USDT", "bar": "1H", "limit": 100}
)

# Get ETH funding rate
skill_mcp(
  mcp_name="crypto",
  tool_name="get_funding_rate",
  arguments={"inst_id": "ETH-USDT-SWAP", "limit": 50}
)

# Get BTC liquidation data
skill_mcp(
  mcp_name="crypto",
  tool_name="get_liquidation",
  arguments={"inst_id": "BTC-USDT-SWAP", "state": "filled", "limit": 100}
)
```

---

## Technical Analysis Module

**File**: `technical_analysis.py`

For comprehensive technical indicator calculation and analysis, use the Python module directly via `bash` tool.

### TechnicalAnalysis Class

The `TechnicalAnalysis` class provides a unified interface for:
- Real-time data fetching from OKX API
- Full technical indicator calculation
- Batch analysis of multiple assets

---

### Quick Start Examples

#### Method 1: Single Asset Analysis (Recommended)

```python
import sys
sys.path.insert(0, r'D:/Crypto/.opencode/skills/crypto/scripts')
from technical_analysis import TechnicalAnalysis

# Create instance - automatically fetches data from API
ta = TechnicalAnalysis.from_api("BTC-USDT", bar="1H", limit=100)

# Get single indicators
rsi = ta.calculate_rsi(14)
macd_dif, macd_dea, macd_hist = ta.calculate_macd()

# Get ALL indicators at once (returns DataFrame)
all_indicators = ta.get_all_indicators()
```

#### Method 2: Batch Analysis

```python
import sys
sys.path.insert(0, r'D:/Crypto/.opencode/skills/crypto/scripts')
from technical_analysis import analyze_all_assets

# Analyze multiple assets, results saved to result/ folder
results = analyze_all_assets(
    inst_ids=['BTC-USDT', 'ETH-USDT', 'SOL-USDT'],
    bar='1D',
    limit=100
)
```

#### Method 3: Direct Data Fetching (Static Methods)

```python
import sys
sys.path.insert(0, r'D:/Crypto/.opencode/skills/crypto/scripts')
from technical_analysis import TechnicalAnalysis

# Funding rate
funding_df = TechnicalAnalysis.fetch_funding_rate("BTC-USDT-SWAP", limit=50)

# Open interest
oi_df = TechnicalAnalysis.fetch_open_interest("BTC-USDT-SWAP", period="1H", limit=100)

# Long/Short ratio
ls_df = TechnicalAnalysis.fetch_long_short_ratio("BTC", period="1H", limit=50)

# Liquidation data
liq_df = TechnicalAnalysis.fetch_liquidation("BTC-USDT-SWAP", state="filled", limit=100)
```

---

### Available Indicator Methods

#### Trend Indicators

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `calculate_ma(period)` | period: int | pd.Series | Simple Moving Average |
| `calculate_ema(period)` | period: int | pd.Series | Exponential Moving Average |
| `calculate_dmi(period=14)` | period: int | (+DI, -DI, ADX) | Directional Movement Index |

#### Momentum Indicators

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `calculate_rsi(period=14)` | period: int | pd.Series | Relative Strength Index |
| `calculate_macd(fast=12, slow=26, signal=9)` | fast, slow, signal: int | (DIF, DEA, Histogram) | MACD |
| `calculate_kdj(n=9, m1=3, m2=3)` | n, m1, m2: int | (K, D, J) | KDJ Stochastic |

#### Volatility Indicators

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `calculate_bollinger_bands(period=20, std_dev=2)` | period, std_dev: int | (Upper, Middle, Lower) | Bollinger Bands |
| `calculate_atr(period=14)` | period: int | pd.Series | Average True Range |

#### Volume Indicators

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `calculate_obv()` | - | pd.Series | On-Balance Volume |

#### Price Structure

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `calculate_fibonacci_retracement(high, low)` | high, low: float | Dict[str, float] | Fibonacci levels (0.0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0) |
| `find_support_resistance(window=5)` | window: int | (supports[], resistances[]) | Key price levels |

---

### get_all_indicators() Output

Returns a DataFrame with all calculated indicators:

| Category | Columns |
|----------|---------|
| Price | open, high, low, close, volume |
| Moving Averages | ma5, ma10, ma20, ma50, ema12, ema26 |
| RSI | rsi6, rsi14 |
| MACD | macd_dif, macd_dea, macd_hist |
| KDJ | kdj_k, kdj_d, kdj_j |
| DMI | dmi_plus_di, dmi_minus_di, dmi_adx |
| Bollinger | bb_upper, bb_middle, bb_lower, bb_width |
| ATR | atr14 |
| OBV | obv |
| Price Change | price_change_1, price_change_5, price_change_20 |
| Volume Change | volume_change, volume_sma20 |

---

### Agent Execution Protocol

**When user requests technical analysis, Agent MUST:**

1. **Extract parameters from user query**:
   - `inst_id`: Trading pair (e.g., "BTC-USDT", "ETH-USDT")
   - `bar`: Timeframe (e.g., "1H", "4H", "1D")
   - `limit`: Data points (default: 100)

2. **Construct and execute Python code via `bash` tool**:

```bash
python -c "
import sys
sys.path.insert(0, r'D:/Crypto/.opencode/skills/crypto/scripts')
from technical_analysis import TechnicalAnalysis

# === AGENT: Replace with extracted parameters ===
INST_ID = 'BTC-USDT'  # From user query
BAR = '1H'            # From user query  
LIMIT = 100           # Default or user-specified

# Create instance and fetch data
ta = TechnicalAnalysis.from_api(INST_ID, bar=BAR, limit=LIMIT)

if ta.data.empty:
    print('ERROR: Failed to fetch data')
else:
    # Get all indicators
    indicators = ta.get_all_indicators()
    latest = indicators.iloc[-1]
    
    # Print formatted report
    print(f'=== {INST_ID} Technical Report ({BAR}) ===')
    print(f'Price: {latest[\"close\"]:.2f}')
    print(f'RSI(14): {latest[\"rsi14\"]:.2f}')
    print(f'MACD DIF: {latest[\"macd_dif\"]:.4f}')
    print(f'MACD DEA: {latest[\"macd_dea\"]:.4f}')
    print(f'MACD Hist: {latest[\"macd_hist\"]:.4f}')
    print(f'KDJ K: {latest[\"kdj_k\"]:.2f}, D: {latest[\"kdj_d\"]:.2f}, J: {latest[\"kdj_j\"]:.2f}')
    print(f'ADX: {latest[\"dmi_adx\"]:.2f}')
    print(f'+DI: {latest[\"dmi_plus_di\"]:.2f}, -DI: {latest[\"dmi_minus_di\"]:.2f}')
    print(f'BB Upper: {latest[\"bb_upper\"]:.2f}')
    print(f'BB Middle: {latest[\"bb_middle\"]:.2f}')
    print(f'BB Lower: {latest[\"bb_lower\"]:.2f}')
    print(f'ATR(14): {latest[\"atr14\"]:.4f}')
    print(f'MA5: {latest[\"ma5\"]:.2f}, MA20: {latest[\"ma20\"]:.2f}, MA50: {latest[\"ma50\"]:.2f}')
"
```

3. **For batch analysis (multiple assets)**:

```bash
python -c "
import sys
sys.path.insert(0, r'D:/Crypto/.opencode/skills/crypto/scripts')
from technical_analysis import analyze_all_assets

# === AGENT: Replace with extracted parameters ===
INST_IDS = ['BTC-USDT', 'ETH-USDT']  # From user query
BAR = '1D'
LIMIT = 100

results = analyze_all_assets(inst_ids=INST_IDS, bar=BAR, limit=LIMIT)
print(f'Analyzed {len(results)} assets. Results saved to result/ folder.')
"
```

4. **For derivatives data (funding, OI, long/short)**:

```bash
python -c "
import sys
sys.path.insert(0, r'D:/Crypto/.opencode/skills/crypto/scripts')
from technical_analysis import TechnicalAnalysis

# === AGENT: Replace with extracted parameters ===
INST_ID = 'BTC-USDT-SWAP'  # Must be SWAP contract
CCY = 'BTC'                 # Currency code for long/short ratio

# Funding rate
funding = TechnicalAnalysis.fetch_funding_rate(INST_ID, limit=10)
if funding is not None:
    print(f'Current Funding Rate: {funding.iloc[0][\"fundingRate\"]:.6f}')

# Open interest
oi = TechnicalAnalysis.fetch_open_interest(INST_ID, period='1H', limit=10)
if oi is not None:
    print(f'Open Interest (USD): \${oi.iloc[0][\"oiUsd\"]:,.0f}')

# Long/Short ratio
ls = TechnicalAnalysis.fetch_long_short_ratio(CCY, period='1H', limit=10)
if ls is not None:
    print(f'Long/Short Ratio: {ls.iloc[0][\"ratio\"]:.4f}')
"
```

---

### Parameter Extraction Rules

| User Says | Extract As |
|-----------|------------|
| "分析BTC", "看看比特币" | inst_id = "BTC-USDT" |
| "ETH技术分析", "以太坊" | inst_id = "ETH-USDT" |
| "1小时级别", "小时线" | bar = "1H" |
| "4小时", "4H" | bar = "4H" |
| "日线", "日级别" | bar = "1D" |
| "周线" | bar = "1W" |
| "资金费率", "funding" | Use fetch_funding_rate with SWAP contract |
| "持仓量", "OI" | Use fetch_open_interest with SWAP contract |
| "多空比" | Use fetch_long_short_ratio with CCY |

---

### Example Agent Workflow

**User**: "帮我分析一下ETH的4小时级别"

**Agent extracts**:
- inst_id = "ETH-USDT"
- bar = "4H"
- limit = 100 (default)

**Agent executes**:
```bash
python -c "
import sys
sys.path.insert(0, r'D:/Crypto/.opencode/skills/crypto/scripts')
from technical_analysis import TechnicalAnalysis
ta = TechnicalAnalysis.from_api('ETH-USDT', bar='4H', limit=100)
indicators = ta.get_all_indicators()
latest = indicators.iloc[-1]
print(f'=== ETH-USDT Technical Report (4H) ===')
# ... (formatted output)
"
```

**Agent interprets** output using `indicators.md` reference, then provides analysis to user.

---

### Integration Flow

```
┌─────────────────────────────────────────────────────────────┐
│                     SKILL.md (You Are Here)                 │
├─────────────────────────────────────────────────────────────┤
│  1. MCP Tools (get_candles, etc.)  →  Raw market data       │
│  2. technical_analysis.py          →  Indicator calculation │
│  3. references/indicators.md       →  Signal interpretation │
│  4. AGENTS.md                      →  Trade decision policy │
└─────────────────────────────────────────────────────────────┘
```

**Workflow**:
1. **Data Fetch**: Use MCP tools OR TechnicalAnalysis static methods
2. **Calculate**: Use TechnicalAnalysis class methods
3. **Interpret**: Reference `indicators.md` for signal meaning
4. **Decide**: Follow `AGENTS.md` for trade execution rules
