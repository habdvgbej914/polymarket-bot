# Polymarket 套利监控机器人

一个自动扫描 Polymarket 预测市场、识别跨市场定价矛盾并通过 Telegram 推送套利机会的 AI 工具。

## 项目功能

- 每2小时自动抓取实时财经新闻（Finnhub 主力 + Reuters RSS 辅助）
- 使用 Claude AI（Haiku 模型）分析跨市场价格逻辑矛盾
- 自动识别违反基本概率规律的定价异常
- 通过 Telegram 推送结构化套利建议

## 实际输出示例
```
🤖 AI发现跨市场机会！

[市场10] vs [市场29]: Ethereum价格矛盾
市场10认为跌至$2,000概率仅2.2%
市场29认为高于$2,100概率高达99.95%
→ 建议: 买市场10 YES

[市场1/3/8/9]: 连续价位定价异常
Kill Over 80.5/81.5/82.5/83.5价格完全相同
违反基本概率递减规律
→ 建议: 逐级买入81.5-83.5档位
```

## 技术栈

- Python
- Claude API（Anthropic）
- Finnhub API
- Reuters RSS
- Telegram Bot API

## 核心逻辑

1. 定时抓取多源新闻和市场数据
2. AI 模型扫描同类市场之间的隐含概率冲突
3. 筛选出违反概率递减规律或逻辑自洽性的定价错误
4. 生成优先级排序的套利建议并推送通知




---

# A股每日简报机器人

自动监控中国市场相关财经新闻，每日生成A股市场分析简报并推送至Telegram。

## 项目功能

- 从 Finnhub 抓取中国市场相关实时财经新闻
- 使用 Claude AI（Haiku 模型）生成结构化市场分析
- 自动推送每日简报至 Telegram，内容包括：
  - 整体市场情绪判断（看多/看空/中性）
  - 最值得关注的新闻及原因
  - A股短期影响判断
  - 建议关注的板块或个股
  - 风险提示

## 与 Polymarket 套利机器人的关系

两个项目共用同一数据来源（Finnhub），但方向完全不同：Polymarket 项目面向国际预测市场的套利机会识别，本项目完全针对中国A股市场的舆情分析与投资参考。

## 技术栈

- Python
- Claude API（Anthropic）
- Finnhub API
- Telegram Bot API