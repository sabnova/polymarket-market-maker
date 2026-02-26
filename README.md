# Polymarket market maker

Polymarket market-making infrastructure focused on one thing: helping a serious trader run disciplined, testable, and risk-aware execution.

## What This Bot Actually Does

- Streams live market and user data over websockets
- Maintains two-sided liquidity with inventory-aware quoting
- Re-prices and resizes orders as microstructure changes
- Applies stop-loss, volatility filters, and risk-off cooldown logic
- Merges opposing YES/NO inventory when possible to free capital

## Trading Logic Director (New Architecture)

The codebase now includes a dedicated execution coordinator:

- `poly_data/trading_logic_director.py`

This director is a central orchestrator between market events and `perform_trade()` decisions.

Why this matters to traders:

- **Less noise-chasing:** bursty websocket updates are coalesced into controlled decision cycles
- **No duplicated market decision loops:** only one in-flight trade cycle per market
- **Fresher intent:** if new events arrive mid-cycle, the director schedules an immediate follow-up cycle
- **Cleaner accountability:** each cycle records trigger reasons (`book_snapshot`, `price_change`, `trade_matched`, etc.)

The practical outcome is tighter control over when and why your strategy reacts.

## Experimental Analysis Framework

Profitability is not a claim; it is an experiment you must verify. Use this framework to judge edge:

### 1) Hypothesis

Example:
"On selected high-liquidity event markets, inventory-aware quoting with volatility/risk-off filters produces positive expectancy after fees and slippage."

### 2) Test Design

- Sample: at least 100-200 completed trades across multiple market regimes
- Keep one configuration fixed for the full sample window
- Log every fill, cancel, inventory change, and risk-off trigger
- Separate results by regime: calm, trending, headline shock

### 3) Core Metrics (Trader View)

- Net PnL (USDC)
- Realized spread capture per fill
- Adverse selection rate (fills followed by immediate unfavorable move)
- Inventory utilization and time-in-risk
- Max drawdown and drawdown duration
- Stop-loss frequency and post-stop performance

### 4) Acceptance Criteria Before Scaling

- Positive net PnL after fees over the full sample
- Profitability not concentrated in one outlier market
- Drawdown within pre-defined risk budget
- Stable performance across at least two market regimes

If these are not met, reduce size and tune parameters instead of adding more capital.

## Repository Structure

- `main.py`: runtime bootstrap, websocket lifecycle, periodic state refresh
- `trading.py`: quote placement, position logic, risk checks, merge operations
- `poly_data/data_processing.py`: event handlers and trade scheduling via director
- `poly_data/trading_logic_director.py`: event-to-decision orchestration layer
- `poly_data`: core data state, clients, websocket handlers, market utilities
- `poly_merger`: merge helper utilities
- `poly_stats`: account/stat tracking
- `data_updater`: market discovery and sheet refresh tooling

## Requirements

- Python 3.9.10+
- Node.js (for `poly_merger`)
- Google Sheets API credentials
- Polymarket account credentials

## Installation

```bash
uv sync
```

Install merger dependencies:

```bash
cd poly_merger
npm install
cd ..
```

Create env file:

```bash
cp .env.example .env
```

Set required values in `.env`:

- `PK`
- `BROWSER_ADDRESS`
- `SPREADSHEET_URL`

## Runbook

Refresh market universe:

```bash
uv run python update_markets.py
```

Start bot:

```bash
uv run python main.py
```

Update stats:

```bash
uv run python update_stats.py
```

## Risk and Deployment Discipline

- Trade small until your own live sample confirms edge
- Keep hard size caps per market and per account
- Track drawdown daily; if breached, stop and review
- Do not treat backtests or short windows as proof

## License

MIT
