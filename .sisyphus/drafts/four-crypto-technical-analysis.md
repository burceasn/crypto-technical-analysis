# Draft: Four Cryptocurrency Technical Analysis Plan

## User Requirements
**Task**: Perform comprehensive technical analysis for ZEC, BNB, ETH, SOL cryptocurrencies including:

### Data Requirements
1. K-line data analysis (multiple timeframes: 1D, 4H, 1H, 15m)
2. Funding rate data
3. Open interest data (positions)
4. Long-short ratio data

### Technical Indicators Analysis
**Trend Indicators**: MA, EMA, DMI
**Momentum Indicators**: RSI, MACD, KDJ
**Volatility Indicators**: Bollinger Bands, ATR
**Volume Indicators**: OBV
**Price Structure**: Fibonacci retracement, Support/Resistance

### Output Requirements
6. Comprehensive technical analysis report
7. Detailed position recommendations (entry points, stop loss, take profit, leverage)

### Constraints
- Must follow AGENTS.md technical analysis enforcement rules
- Must analyze full set of technical indicators, cannot skip any core indicators
- Must combine multi-timeframe validation (follow major trend, trade minor trend principle)
- Must provide specific, actionable trading recommendations

## Assets to Analyze
1. **ZEC** (Zcash)
   - Spot: ZEC-USDT
   - Perpetual: ZEC-USDT-SWAP

2. **BNB** (Binance Coin)
   - Spot: BNB-USDT
   - Perpetual: Not listed in AGENTS.md

3. **ETH** (Ethereum)
   - Spot: ETH-USDT
   - Perpetual: ETH-USDT-SWAP

4. **SOL** (Solana)
   - Spot: SOL-USDT
   - Perpetual: SOL-USDT-SWAP

## Technical Analysis Framework (from AGENTS.md)

### Multi-timeframe Validation Rules
- 15m timeframe → reference 4H trend
- 1H timeframe → reference 4H, 1D trend
- 4H, 1D timeframe → reference 1D, 1W trend

### Key Technical Indicators Required
1. **Trend Indicators**:
   - MA: MA5, MA10, MA20, MA50, MA200
   - EMA: EMA12, EMA26 (for MACD calculation)
   - DMI: +DI, -DI, ADX (14 period)

2. **Momentum Indicators**:
   - RSI: 14 period
   - MACD: DIF (EMA12-EMA26), DEA (9 period EMA of DIF), Histogram
   - KDJ: K, D, J values (9,3,3 periods)

3. **Volatility Indicators**:
   - Bollinger Bands: MA20 +- 2× standard deviation, %B indicator
   - ATR: 14 period (for stop loss/take profit calculation)

4. **Volume Indicators**:
   - OBV: On Balance Volume

5. **Price Structure**:
   - Fibonacci Retracement: 0.236, 0.382, 0.500, 0.618, 0.786
   - Support/Resistance: Swing highs/lows, Pivot Points

## Open Questions
1. **Time range for data**: How many days of historical data needed? (Default: 100 candles per timeframe)
2. **BNB perpetual contract**: AGENTS.md doesn't list BNB-USDT-SWAP. Should we use spot only or find alternative?
3. **Analysis depth**: Should we include liquidation data mentioned in AGENTS.md?
4. **Report format**: Any specific template or format requirements?
5. **Priority**: Equal priority for all 4 assets or specific focus?

## Initial Planning Thoughts

### Parallel Execution Strategy
**Phase 1: Data Acquisition (Parallel by asset)**
- Wave 1: Fetch data for all 4 assets in parallel
  - Each asset: K-line (4 timeframes), funding rate, open interest, long-short ratio

**Phase 2: Technical Indicators Calculation (Parallel by indicator type)**
- Wave 2: Calculate trend indicators for all assets
- Wave 3: Calculate momentum indicators for all assets
- Wave 4: Calculate volatility indicators for all assets
- Wave 5: Calculate volume indicators for all assets
- Wave 6: Calculate price structure for all assets

**Phase 3: Individual Asset Analysis (Parallel by asset)**
- Wave 7: Generate technical analysis reports for each asset

**Phase 4: Integration and Recommendations (Sequential)**
- Wave 8: Compare analysis results across assets
- Wave 9: Generate consolidated position recommendations
- Wave 10: Create final comprehensive report

### Category and Skills Recommendations
Based on task types:
- **Data fetching**: `unspecified-low` with `crypto` skill (requires MCP access)
- **Technical calculations**: `unspecified-low` with `python-programmer` or `data-scientist` skills
- **Analysis/reporting**: `writing` with relevant domain knowledge