# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Tushare_MCP is an intelligent stock data assistant built on the Model Context Protocol (MCP). It provides comprehensive access to Chinese stock market data through Tushare's financial data API, wrapped in a FastAPI service with MCP tool integration.

## Architecture

### Core Components

**server.py** - Single-file application (1883 lines)
- FastAPI app serving both HTTP API and MCP SSE protocol
- Contains 30 MCP tools for stock data retrieval
- Runs on port 8000 (default) or PORT env var for Cloud Run
- Three endpoint types:
  - `/` - Health check endpoint
  - `/tools/setup_tinyshare_token` - HTTP POST API for token configuration
  - `/sse` - MCP SSE handshake (GET) and `/sse/messages/` (POST) for MCP protocol

### Key Design Patterns

**SSE Workaround for MCP Integration** (lines 1719-1759):
- Uses `SseServerTransport` from `mcp.server.sse` instead of FastMCP's built-in SSE
- Manual routing: GET `/sse` → `handle_mcp_sse_handshake()` → `mcp._mcp_server.run()`
- POST `/sse/messages/` → `sse_transport.handle_post_message`
- This workaround is necessary because FastMCP's `sse_app()` doesn't work correctly when mounted as sub-application

**Financial Report Data Fetching** (lines 75-147):
- `_fetch_latest_report_data()` helper abstracts the pattern:
  1. Query API with filters (ts_code, period, etc.)
  2. Filter results by period field matching
  3. Sort by `ann_date` descending
  4. Return latest announcement for that period
  5. Supports `is_list_result=True` for multi-row results (e.g., top 10 holders)

**Unified Logging & Error Handling**:
- `log_debug()` wrapper (line 35-37) for consistent stderr logging
- `@handle_exception` decorator defined (lines 39-55) but **not used** - all tools use manual try-except
- All tools follow identical error handling pattern (see "Error Handling Pattern" section)

### Token Management

Token is stored at `~/.tushare_mcp/.env` with key `TUSHARE_TOKEN`. Functions:
- `get_tushare_token()` - retrieves token from env file
- `set_tushare_token()` - sets token in env file and initializes `ts.set_token()`
- `init_env_file()` - ensures env file exists and is loaded

## Development Commands

### Setup
```bash
# Create virtual environment (required on macOS with system-managed Python)
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

### Running Locally

```bash
# Start the FastAPI server (listens on 0.0.0.0:8000)
python server.py

# The MCP SSE endpoint will be available at:
# - http://localhost:8000/sse (for MCP clients)
# - http://localhost:8000/docs (FastAPI auto-generated docs)
```

### Docker Deployment

```bash
# Build image
docker build -t tushare-mcp .

# Run container
docker run -p 8080:8080 -e TUSHARE_TOKEN=your_token tushare-mcp

# For Cloud Run deployment, expects PORT env var (defaults to 8080)
```

### Testing MCP Integration

```bash
# Test health endpoint
curl http://localhost:8000/

# Test token setup via HTTP API
curl -X POST http://localhost:8000/tools/setup_tinyshare_token \
  -H "Content-Type: application/json" \
  -d '{"token": "your_tushare_token"}'

# For MCP client testing, configure in your MCP client (e.g., Claude Desktop):
# {
#   "mcpServers": {
#     "tushare": {
#       "url": "http://localhost:8000/sse"
#     }
#   }
# }
```

## MCP Tools Overview

Tools are registered using `@mcp.tool()` decorator and fall into these categories:

### Token Management
- `setup_tushare_token` - Configure API token
- `check_token_status` - Verify token validity

### Basic Stock Info
- `get_stock_basic_info` - A-share basic info by code/name
- `get_hk_stock_basic` - Hong Kong stock listing info
- `search_stocks` - Keyword search across stocks

### Market Data
- `get_daily_prices` - OHLC prices for single day or date range
- `get_daily_metrics` - Volume, turnover rate, PE/PB ratios
- `get_daily_basic_info` - Share capital and market cap data
- `get_period_price_change` - Price change % between dates

### Financial Reports
- `get_financial_indicator` - Comprehensive financial indicators (supports period, ann_date, or date range queries)
- `get_income_statement` - Income statement with YoY growth calculation
- `get_balance_sheet` - Balance sheet main items
- `get_cash_flow` - Cash flow statement data
- `get_fina_mainbz` - Revenue breakdown by product/region/industry
- `get_fina_audit` - Audit opinion data

### Shareholder Info
- `get_shareholder_count` - Number of shareholders by period
- `get_top_holders` - Top 10 shareholders (type 'H') or float shareholders (type 'F')

### Index Data
- `search_index` - Search index by name/market/publisher
- `get_index_list` - Query index list with filters
- `get_index_constituents` - Get constituent stocks and weights for monthly data
- `get_global_index_quotes` - International index quotes

### Special Data
- `get_pledge_detail` - Share pledge statistics
- `get_top_list_detail` - Dragon-Tiger List daily trading details
- `get_top_institution_detail` - Institutional trading on Dragon-Tiger List

### Calendar & Utility
- `get_trade_calendar` - Exchange trading calendar (filters by `is_open=1` for trading days)
- `get_start_date_for_n_days` - Calculate start date N trading days before end_date

## Important Implementation Details

### Date Format
All dates use `YYYYMMDD` format (e.g., `20240930` for Sept 30, 2024)

### Stock Code Format
- A-shares: `000001.SZ` (Shenzhen), `600000.SH` (Shanghai)
- HK stocks: `00700.HK`
- Indices: `000300.SH` (CSI 300), `399300.SZ` (Shenzhen variant)

### Financial Report Fetching Logic
The `_fetch_latest_report_data()` helper:
1. Filters by period (end_date field)
2. Sorts by announcement date descending
3. Returns latest announced report for that period
4. Supports `is_list_result=True` to return all rows for latest ann_date (used for multi-row results like top holders)

### Data Units
- Financial amounts from Tushare are in **Yuan (元)**, tools convert to **亿元 (hundred million yuan)** by dividing by 100,000,000
- Share amounts are in **万股 (10K shares)** or **万元 (10K yuan)**

### Error Handling Pattern
All tools follow this pattern:
```python
token_value = get_tushare_token()
if not token_value:
    return "错误：Tushare token 未配置或无法获取。请使用 setup_tushare_token 配置。"
try:
    # ... tool logic
except Exception as e:
    print(f"DEBUG: ERROR in tool_name: {str(e)}", file=sys.stderr, flush=True)
    traceback.print_exc(file=sys.stderr)
    return f"操作失败：{str(e)}"
```

## Testing & Debugging

- All debug output goes to `sys.stderr` with `flush=True`
- Look for `DEBUG:` prefixed messages in stderr for detailed execution traces
- FastAPI automatic docs available at `http://localhost:8000/docs` when server is running

## Dependencies Highlights

- `tushare` - Financial data API client
- `fastapi` + `uvicorn` - Web framework and ASGI server
- `mcp` - Model Context Protocol SDK
- `pandas` - Data manipulation
- `python-dotenv` - Environment variable management
- `sse-starlette` - Server-Sent Events support (for MCP SSE transport)

## Known Limitations & Issues

### Data Coverage
- No announcement/research report text data
- No minute-level or tick data
- A-share and index data only; no futures, options, or macroeconomic data
- Some financial APIs require higher Tushare point levels for full data access

### Known Bugs
- `get_fina_audit()` (line 1574-1606): **Will crash with KeyError**
  - Line 1591 queries without `audit_fees` field
  - Line 1598 attempts to access `row['audit_fees']`
  - Fix: Add `audit_fees` to fields parameter or remove from output

### Code Quality Issues
- `@handle_exception` decorator (lines 39-55) is defined but never used
- 28 tools all have identical try-except blocks that could use the decorator
- Three similar formatting functions could be consolidated:
  - `_format_indicator_value()` (line 758)
  - `format_bs_value()` (line 1362)
  - `format_cf_value()` (line 1433)
