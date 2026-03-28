# Polymarket Bot 项目文档

## 项目概览
一个AI驱动的金融分析系统，结合MCP Server、CFA量化模型和个性化投资分析。

## 用户背景
- 伦敦时装学院高级定制专业，7月底回国
- 零代码基础起步，通过Vibe Coding构建项目
- 正在学习CFA一级（量化方法、经济学已完成）
- 目标：回国后在上海/杭州/深圳找AI相关工作
- 朋友在东方证券研究院做MCP和模型部署项目

## 文件结构
```
~/Desktop/polymarket-bot/
├── ai_scan.py          # Polymarket套利扫描（原始项目）
├── china_market.py     # A股每日简报（定时任务版）
├── china_market_mcp.py # 主MCP Server
├── market_history.json # 贝叶斯历史数据
├── PROJECT.md          # 本文件
└── .env                # API Keys（不上传GitHub）
```

## API Keys（.env文件）
- ANTHROPIC_API_KEY
- TELEGRAM_TOKEN
- TELEGRAM_CHAT_ID
- FINNHUB_API_KEY

## GitHub
https://github.com/habdvgbej914/polymarket-bot

## MCP Server功能（china_market_mcp.py）

### Tools
- `get_china_news()`：从Finnhub抓取中国市场相关新闻
- `get_sharpe_ratio(symbol)`：夏普比率计算（当前用模拟数据）
- `get_pe_analysis(symbol)`：市盈率分析（Finnhub真实数据）
- `get_sentiment_confidence()`：95%置信区间分析
- `get_personalized_analysis()`：个性化投资建议
- `update_market_sentiment(sentiment)`：贝叶斯情绪更新
- `send_telegram(message)`：推送Telegram通知

### Resources
- `market://daily-brief`：今日市场简报

### Prompts
- `analyze-market`：标准市场分析框架

## CFA量化模型应用
- **贝叶斯公式**：P(A|B) = P(A) × P(B|A) / P(B)，每日更新市场情绪概率
- **夏普比率**：(收益率 - 无风险利率) / 标准差，回国后接入AKShare真实数据
- **正态分布置信区间**：均值 ± 1.96 × 标准差，量化判断可靠程度
- **市盈率PE**：Price / EPS，当前使用Finnhub真实数据

## 定时任务
```
0 8 * * * cd ~/Desktop/polymarket-bot && python3 china_market.py >> scan_log.txt 2>&1
```
每天早上8点自动运行，Mac需要开机。

## 技术栈
- Python 3.14
- Claude API（Haiku模型，成本优化）
- Finnhub API（新闻+财务数据）
- MCP Python SDK 1.26.0
- AKShare（已安装，回国后使用）
- Telegram Bot API

## 待完成事项
- [ ] 回国后接入AKShare真实A股数据
- [ ] 夏普比率替换真实历史价格
- [ ] 用户动态画像系统（记录决策历史）
- [ ] 五行思维框架（独立项目，见下）
- [ ] Polymarket历史准确性分析（需要大块时间）
  - 数据源：https://archive.pmxt.dev/Polymarket（每小时更新，Parquet格式）
  - 框架已建立：accuracy_analysis.py
  - 需要：pandas、pyarrow处理大文件，筛选金融类市场，重建价格历史
  - 建议5月6月课程结束后专门处理

## 未来项目：五行二进制市场状态系统

**核心思想**：用邵雍先天易学的二进制结构（一分为二）+ 奇门遁甲的多时间尺度嵌套 + 五行循环规律，构建一个可验证的市场状态预测框架。

**数学地基**：
- 阴=0，阳=1，四个因子形成16种二进制市场状态
- 对应奇门遁甲18局（节气级）、72局（候级）、1080局（时辰级）三个时间尺度
- 状态文件：market_states.json

**四个因子**：
- A：新闻情绪（0=看空，1=看多）
- B：成交量（0=萎缩，1=放大）
- C：价格动量（0=下跌，1=上涨）
- D：波动率（0=高波动，1=低波动）

**循环路径**：0→2→3→7→11→13→14→15→14→13→11→7→5→4→1→0

**待完成**：回国后用AKShare真实历史数据回测每个状态的实际转换规律，用数据验证循环规律是否成立。

**独特性**：古人的结构智慧 + 现代数据验证，目前无人做过。

## 用户投资画像（个性化系统基础数据）
- 资金量：1000英镑
- 经验：有实操（Trading212、MT4），短线亏损后转向长期
- 风险偏好：保本优先，止损3-5%
- 目标：长期增值+学习
- 周期：1-3年
- 市场：美股为主，关注A股和加密货币

## 朋友的技术栈（东方证券研究院）
- 硬件：A800 GPU服务器
- 模型：Qwen（自部署）
- 数据：Wind付费数据 + 内部私有数据
- 需求：独立完成MCP开发能力

## 学习路线
**现在到5月**：每天1小时，继续优化项目
**5月6月**：每天3-4小时冲刺，完成框架搭建
**7月回国**：接入AKShare，开始投递简历

## 重要经验教训
- .env文件不能上传GitHub（已处理）
- bash命令只能在系统Terminal运行，不能在VS Code终端运行
- MCP Server运行时终端不能用于其他命令，需开新终端窗口
- AKShare在英国网络下无法访问，回国后直接可用