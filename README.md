# AI-Powered Financial Analysis Toolkit

A collection of MCP Servers and automated tools for financial market analysis, combining quantitative models, AI reasoning, and structured decision frameworks.

AI驱动的金融分析工具集。结合量化模型、AI推理和结构化决策框架的MCP Server与自动化工具。

---

## Projects / 项目

### 1. Contrarian Opportunity Analysis System / 逆向机会分析系统

**`contrarian_analysis_mcp.py`** — MCP Server

An AI reasoning engine that identifies structural mislocations between Form (what has crystallized) and Flow (what is circulating) in any domain — finding opportunities that mainstream narratives undervalue.

识别任何领域中"形"（已成形的事物）与"流"（正在流通的事物）之间的结构性错位——发现被主流叙事低估的机会。

**How it works:**

The system evaluates any domain through **6 criteria** across **3 layers**, each assessed on **5 dimensions**:

| Layer | Criteria | Question |
|-------|----------|----------|
| **Environment (势)** | C1 Trend Alignment | Aligned or misaligned with macro trend? |
| | C2 Energy State | Accumulating or dissipating energy? |
| **Participant (可行性)** | C3 Incumbent Alignment | Are incumbents matched or mismatched? |
| | C4 Personal Sustainability | Can you survive the dormancy period? |
| **Foundation (质)** | C5 Fundamental Solidity | Solid or hollow fundamentals? |
| | C6 Domain Weight | Heavy or light domain? |

Each criterion outputs a binary state (0 or 1). Six bits = **64 possible situational configurations**.

**Core output — Form-Flow Mislocation Detection:**

| State | Meaning | Signal |
|-------|---------|--------|
| `form_without_flow` | Infrastructure exists, no market attention | **Classic undervalued opportunity** |
| `flow_without_form` | Growing demand, no crystallized solution | Bubble risk — validate first |
| `no_mislocation_positive` | Both present | Mainstream — competition active |
| `no_mislocation_negative` | Neither present | Not worth entering |

**Architecture:**

```
User Query
    ↓
Claude (LLM) ← does 5-dimension analysis per criterion
    ↓
MCP Server ← receives 6 binary judgments
    ↓
Analysis Engine
    ├── Layer Synthesis (3 layers × 2 criteria)
    ├── Cross-Layer Matrix (Momentum × Substance)
    └── Form-Flow Mislocation Detection
    ↓
Structured Result → Claude translates to business language
    ↓
Business Recommendation (no framework jargon)
```

Key design: **Claude acts as the LLM layer** — it performs qualitative five-dimension assessment and makes binary judgments. The MCP Server handles structural logic: layer synthesis, cross-layer analysis, mislocation detection. Reasoning (LLM) and structure (code) are separated.

**Quick start with Claude Code:**

```bash
claude mcp add contrarian-analysis python3 contrarian_analysis_mcp.py
claude
# Then ask: "用contrarian analysis框架分析一下[领域名称]"
```

**Available tools:**

| Tool | Description |
|------|-------------|
| `get_framework_guide()` | Returns complete framework structure |
| `quick_scan(domain, ...)` | Fast 6-bit scan with binary inputs |
| `get_analysis_history()` | View past analysis results |

---

### 2. China Market MCP Server / A股市场分析MCP Server

**`china_market_mcp.py`** — MCP Server

Real-time China market analysis combining Bayesian sentiment tracking, CFA quantitative models, and personalized investment advice.

结合贝叶斯情绪追踪、CFA量化模型和个性化投资建议的A股市场实时分析系统。

**Tools:**

| Tool | Description |
|------|-------------|
| `get_china_news()` | Fetch China-related financial news from Finnhub |
| `get_sharpe_ratio(symbol)` | Calculate Sharpe ratio for a stock |
| `get_pe_analysis(symbol)` | P/E ratio and valuation analysis (live data) |
| `get_sentiment_confidence()` | 95% confidence interval on market sentiment |
| `get_personalized_analysis()` | Personalized investment advice based on user profile |
| `update_market_sentiment(sentiment)` | Bayesian update of market sentiment probability |
| `send_telegram(message)` | Push notifications to Telegram |

**CFA quantitative models applied:**
- **Bayesian updating**: P(A|B) = P(A) × P(B|A) / P(B) — daily sentiment probability updates
- **Sharpe ratio**: (Return - Risk-free rate) / Std Dev — risk-adjusted performance
- **Normal distribution confidence intervals**: Mean ± 1.96 × Std Dev — reliability quantification
- **P/E ratio analysis**: Price / EPS — valuation assessment using live Finnhub data

---

### 3. Polymarket Arbitrage Scanner / Polymarket套利扫描器

**`ai_scan.py`**

Automated scanner that identifies cross-market pricing contradictions in prediction markets and pushes arbitrage opportunities via Telegram.

自动扫描预测市场的跨市场定价矛盾，通过Telegram推送套利机会。

**Output example:**
```
🤖 AI发现跨市场机会！

[市场10] vs [市场29]: Ethereum价格矛盾
市场10认为跌至$2,000概率仅2.2%
市场29认为高于$2,100概率高达99.95%
→ 建议: 买市场10 YES
```

---

### 4. Daily Market Brief / 每日市场简报

**`china_market.py`**

Cron job that generates daily A-share market analysis briefs and pushes them to Telegram.

定时任务，每日生成A股市场分析简报并推送至Telegram。

```
0 8 * * * cd ~/Desktop/polymarket-bot && python3 china_market.py >> scan_log.txt 2>&1
```

---

## Project Structure / 项目结构

```
polymarket-bot/
├── contrarian_analysis_mcp.py   # Contrarian Opportunity Analysis MCP Server
├── china_market_mcp.py          # China Market Analysis MCP Server
├── china_market.py              # Daily market brief (cron job)
├── ai_scan.py                   # Polymarket arbitrage scanner
├── analysis_history.json        # Contrarian analysis history (auto-generated)
├── market_history.json          # Bayesian sentiment history
├── PROJECT.md                   # Internal project documentation
├── README.md                    # This file
└── .env                         # API keys (not committed)
```

## Tech Stack / 技术栈

- Python 3.14
- MCP Python SDK 1.26.0
- Claude API (Haiku for cost optimization)
- Claude Code (as MCP client + LLM reasoning layer)
- Finnhub API (news + financial data)
- Telegram Bot API (notifications)
- AKShare (installed, to be activated for live A-share data)

## Setup / 安装

```bash
# Clone
git clone https://github.com/habdvgbej914/polymarket-bot.git
cd polymarket-bot

# Install dependencies
pip install mcp python-dotenv requests anthropic

# Configure API keys
cp .env.example .env
# Edit .env with your keys: ANTHROPIC_API_KEY, FINNHUB_API_KEY, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID

# Register MCP Servers with Claude Code
claude mcp add china-market python3 china_market_mcp.py
claude mcp add contrarian-analysis python3 contrarian_analysis_mcp.py
```

## What This Project Demonstrates / 这个项目展示了什么

1. **MCP Server development** — custom tools, resources, and prompts following the MCP protocol
2. **Framework-driven AI analysis** — structured reasoning beyond simple prompting
3. **LLM + local logic separation** — Claude handles qualitative judgment, code handles structural computation
4. **CFA quantitative models in code** — Bayesian updating, Sharpe ratio, confidence intervals applied to real market analysis
5. **Bilingual system design** — operates natively in English and Chinese

## License

MIT