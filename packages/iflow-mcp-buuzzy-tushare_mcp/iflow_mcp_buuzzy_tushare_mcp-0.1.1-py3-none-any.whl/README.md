# Tushare MCP

A股数据查询服务，基于 MCP (Model Context Protocol) 协议，支持通过 AI 助手（Claude Desktop、Cursor 等）用自然语言查询股票数据。

## 重要说明

**本项目使用 `tinyshare` SDK，而非官方 `tushare`。**

如果你想用官方 tushare，修改 `server.py` 第 5 行：
```python
# 当前
import tinyshare as ts

# 改为
import tushare as ts
```

同时修改 `requirements.txt`：将 `tinyshare` 替换为 `tushare==版本号`

## 功能

提供 25 个 MCP 工具，覆盖：
- A股、港股基本信息
- 日线行情、财务报表
- 股东信息、指数数据
- 龙虎榜、交易日历

## 快速开始

### 安装

```bash
# 1. 克隆项目
git clone <你的仓库地址>
cd tushare-mcp

# 2. 创建虚拟环境（macOS 必需）
python3 -m venv venv
source venv/bin/activate

# 3. 安装依赖
pip install -r requirements.txt
```

### 配置 Token

启动后，在 AI 助手中调用 `setup_tushare_token` 工具配置。

或手动创建配置文件：
```bash
mkdir -p ~/.tushare_mcp
echo "TUSHARE_TOKEN=你的token" > ~/.tushare_mcp/.env
```

### 启动服务

```bash
python server.py
```

服务运行在 `http://localhost:8000`

- 健康检查: `http://localhost:8000/`
- API 文档: `http://localhost:8000/docs`
- MCP 端点: `http://localhost:8000/sse`

## 使用

### Claude Desktop

编辑配置文件 `~/Library/Application Support/Claude/claude_desktop_config.json`：

```json
{
  "mcpServers": {
    "tushare": {
      "url": "http://localhost:8000/sse"
    }
  }
}
```

重启 Claude Desktop 即可使用。

### Cursor

设置 → MCP Servers → 添加：
- 名称: `tushare`
- URL: `http://localhost:8000/sse`

### HTTP API

```bash
# 配置 Token
curl -X POST http://localhost:8000/tools/setup_tushare_token \
  -H "Content-Type: application/json" \
  -d '{"token": "你的token"}'
```

## 工具列表

### Token 管理
- `setup_tushare_token` - 配置 Token
- `check_token_status` - 检查 Token 状态

### 股票信息
- `get_stock_basic_info` - A股基本信息
- `get_hk_stock_basic` - 港股基本信息
- `search_stocks` - 搜索股票

### 行情数据
- `get_daily_prices` - 日线行情（开高低收）
- `get_daily_metrics` - 换手率、PE/PB
- `get_daily_basic_info` - 股本、市值
- `get_period_price_change` - 区间涨跌幅

### 财务数据
- `get_financial_indicator` - 财务指标
- `get_income_statement` - 利润表
- `get_balance_sheet` - 资产负债表
- `get_cash_flow` - 现金流量表
- `get_fina_mainbz` - 主营业务构成

### 股东信息
- `get_shareholder_count` - 股东户数
- `get_top_holders` - 前十大股东

### 指数数据
- `search_index` - 搜索指数
- `get_index_list` - 指数列表
- `get_index_constituents` - 指数成分股
- `get_global_index_quotes` - 国际指数行情

### 特色数据
- `get_pledge_detail` - 股权质押
- `get_top_list_detail` - 龙虎榜
- `get_top_institution_detail` - 龙虎榜机构席位

### 工具
- `get_trade_calendar` - 交易日历
- `get_start_date_for_n_days` - 计算往前N个交易日

## 数据格式

**日期**: `YYYYMMDD`（如 `20240930`）

**股票代码**:
- A股: `000001.SZ` (深圳) / `600000.SH` (上海)
- 港股: `00700.HK`
- 指数: `000300.SH`

**金额单位**:
- 财务数据: 亿元
- 股本: 万股
- 市值: 万元

## Docker 部署

```bash
docker build -t tushare-mcp .
docker run -d -p 8000:8000 -e TUSHARE_TOKEN=你的token tushare-mcp
```

## 故障排查

### Token 无效
```bash
# 测试 Token（使用 tinyshare）
python3 << EOF
import tinyshare as ts
ts.set_token('你的token')
print(ts.pro_api().stock_basic(ts_code='000001.SZ'))
EOF
```

### 服务无法访问
```bash
# 检查服务状态
ps aux | grep server.py

# 检查端口占用
lsof -i :8000
```

### MCP 连接失败
```bash
# 测试端点
curl http://localhost:8000/
curl http://localhost:8000/sse
```

## License

MIT
