---
name: experience
description: (CryptoView - Skill) OKX 交易所账户持仓管理。获取当前持仓信息和历史持仓记录（近3个月），包含方向、杠杆、收益率、保证金、强平价等关键字段。需要 OKX API Key 认证。MUST USE for any position/holding queries.
---

# Experience (持仓) Skill

OKX 交易所账户持仓数据访问能力。通过私有 API（需认证）获取当前持仓和历史持仓信息。

---

## Skill Scope & Boundaries

### This Skill PROVIDES
- 当前持仓信息（方向、杠杆、未实现收益、收益率、强平价、保证金等）
- 历史持仓记录（近3个月，含已实现收益、开/平仓均价、持仓时长等）

### This Skill does NOT HANDLE
- 技术分析 → 使用 `crypto` skill
- K线 / 资金费率 / 持仓量等市场数据 → 使用 `crypto` skill
- 交易决策 → 由 Agent 策略 (`AGENTS.md`) 处理
- 下单 / 撤单 / 修改订单等交易操作 → 不支持

### 前置条件

项目根目录 `.env` 文件中必须配置以下环境变量：

```
OKX_API_KEY=your_api_key
OKX_SECRET_KEY=your_secret_key
OKX_PASSPHRASE=your_passphrase
```

**缺少任何一项将导致 API 认证失败。**

---

## Trigger Conditions

**MUST load this Skill when:**

- 查询当前持仓（"我现在持仓了什么"、"看看我的仓位"）
- 查询历史持仓（"最近的交易记录"、"历史持仓"）
- 需要收益率 / 盈亏分析
- 需要持仓风险评估（强平价、保证金率）

---

## Available Functions

脚本路径: `D:/Crypto/.opencode/skills/experience/scripts/crypto_hold.py`

### 1. get_positions - 获取当前持仓

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `inst_type` | string | No | 产品类型: `MARGIN`, `SWAP`, `FUTURES`, `OPTION` |
| `inst_id` | string | No | 交易产品ID，如 `BTC-USDT-SWAP`，支持逗号分隔多个 |
| `pos_id` | string | No | 持仓ID，支持多个 |
| `use_proxy` | bool | No | 是否使用代理 (默认 False) |

**Returns**: JSON 字符串（数组），每条记录包含：

| 字段 | 说明 |
|------|------|
| `uniID` | 唯一标识 (MD5 hash) |
| `instId` | 产品ID |
| `保证金模式` | 全仓 / 逐仓 |
| `direction` | 多 / 空 |
| `leverage` | 杠杆倍数 |
| `持仓量` | 持仓数量 |
| `开仓均价` | 开仓均价 |
| `标记价` | 当前标记价格 |
| `未实现收益` | 浮动盈亏 (USDT) |
| `收益率` | 百分比 (如 "12.34%") |
| `强平价` | 预估强制平仓价格 |
| `保证金(U)` | 占用保证金 (USDT) |
| `保证金率` | 保证金比率 |
| `开仓时间` | UTC+8 格式 |
| `更新时间` | UTC+8 格式 |
| `持仓时长` | 中文描述 (如 "2 Day3 Hour") |
| `费用` | 手续费 + 资金费率 |

**无持仓时返回 None。**

### 2. get_positions_history - 获取历史持仓

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `inst_type` | string | No | 产品类型: `MARGIN`, `SWAP`, `FUTURES`, `OPTION` |
| `inst_id` | string | No | 交易产品ID，如 `BTC-USD-SWAP` |
| `mgn_mode` | string | No | 保证金模式: `cross` (全仓) 或 `isolated` (逐仓) |
| `close_type` | string | No | 平仓类型: `1`~`6` |
| `pos_id` | string | No | 持仓ID |
| `after` | string | No | 查询 uTime 之前 (毫秒时间戳) |
| `before` | string | No | 查询 uTime 之后 (毫秒时间戳) |
| `limit` | int | No | 返回数量 (默认 100，最大 100) |
| `use_proxy` | bool | No | 是否使用代理 (默认 False) |

**Returns**: JSONL 字符串（每行一个 JSON），每条记录包含：

| 字段 | 说明 |
|------|------|
| `uniID` | 唯一标识 (MD5 hash) |
| `instId` | 产品ID |
| `保证金模式` | 全仓 / 逐仓 |
| `direction` | 多 / 空 |
| `leverage` | 杠杆倍数 |
| `开仓均价` | 开仓价格 |
| `平仓均价` | 平仓价格 |
| `已实现收益` | 已实现盈亏 (USDT) |
| `收益率` | 百分比 (如 "-5.23%") |
| `触发价` | 触发平仓的价格 |
| `保证金(U)` | 初始保证金 (通过 realizedPnl/pnlRatio 反推) |
| `开仓时间` | UTC+8 格式 |
| `更新时间` | UTC+8 格式 |
| `持仓时长` | 中文描述 |
| `费用` | 手续费 + 资金费率 |

**无历史记录时返回 None。**

---

## Agent Execution Protocol

**When user requests position data, Agent MUST:**

1. **Extract parameters from user query**
2. **Construct and execute Python code via `bash` tool**

### 查询当前持仓

```bash
python -c "
import sys
sys.path.insert(0, r'D:/Crypto/.opencode/skills/experience/scripts')
from crypto_hold import get_positions

# 获取所有持仓
result = get_positions()
if result:
    print(result)
else:
    print('当前无持仓')
"
```

### 查询指定产品持仓

```bash
python -c "
import sys
sys.path.insert(0, r'D:/Crypto/.opencode/skills/experience/scripts')
from crypto_hold import get_positions

# === AGENT: Replace with extracted parameters ===
result = get_positions(inst_id='BTC-USDT-SWAP')
if result:
    print(result)
"
```

### 查询永续合约持仓

```bash
python -c "
import sys
sys.path.insert(0, r'D:/Crypto/.opencode/skills/experience/scripts')
from crypto_hold import get_positions

result = get_positions(inst_type='SWAP')
if result:
    print(result)
"
```

### 查询历史持仓

```bash
python -c "
import sys
sys.path.insert(0, r'D:/Crypto/.opencode/skills/experience/scripts')
from crypto_hold import get_positions_history

# === AGENT: Replace with extracted parameters ===
result = get_positions_history(inst_type='SWAP', limit=20)
if result:
    print(result)
"
```

### 综合查询（当前 + 历史）

```bash
python -c "
import sys, json
sys.path.insert(0, r'D:/Crypto/.opencode/skills/experience/scripts')
from crypto_hold import get_positions, get_positions_history

print('=== 当前持仓 ===')
current = get_positions()
if current:
    print(current)
else:
    print('无持仓')

print()
print('=== 最近历史持仓 ===')
history = get_positions_history(limit=10)
if history:
    for line in history.splitlines():
        parsed = json.loads(line)
        pnl = parsed.get('已实现收益', 0)
        symbol = '🟢' if pnl and pnl > 0 else '🔴'
        print(f'{symbol} {parsed[\"instId\"]} {parsed[\"direction\"]} {parsed[\"leverage\"]}x | PnL: {pnl} ({parsed[\"收益率\"]}) | {parsed[\"持仓时长\"]}')
"
```

---

## Parameter Extraction Rules

| User Says | Extract As |
|-----------|------------|
| "我的持仓", "当前仓位", "现在持仓" | `get_positions()` |
| "BTC仓位", "看看BTC" (持仓语境) | `get_positions(inst_id="BTC-USDT-SWAP")` |
| "永续持仓", "合约仓位" | `get_positions(inst_type="SWAP")` |
| "历史持仓", "交易记录", "最近的交易" | `get_positions_history()` |
| "最近10笔", "最近N笔" | `get_positions_history(limit=N)` |
| "全仓持仓" | `get_positions_history(mgn_mode="cross")` |
| "逐仓持仓" | `get_positions_history(mgn_mode="isolated")` |

---

## Integration with Crypto Skill

本 Skill 与 `crypto` Skill 互补：

```
┌─────────────────────────────────────────────────────────────┐
│                      Analysis Workflow                       │
├─────────────────────────────────────────────────────────────┤
│  1. experience skill  →  获取当前持仓 (我持有什么?)          │
│  2. crypto skill      →  技术分析 (市场怎么样?)             │
│  3. AGENTS.md         →  风险评估 & 交易决策                │
└─────────────────────────────────────────────────────────────┘
```

**典型场景**: 用户问 "我的BTC仓位安全吗？"
1. 用 `experience` 获取当前BTC持仓（方向、杠杆、强平价、保证金率）
2. 用 `crypto` 获取BTC当前价格和技术面
3. 综合评估风险

---

## Rate Limits

| API | 限速 |
|-----|------|
| get_positions | 10次 / 2秒 |
| get_positions_history | 10次 / 2秒 |

---

## Error Handling

| 错误 | 原因 | 解决 |
|------|------|------|
| API 认证失败 | .env 未配置或 Key 错误 | 检查 OKX_API_KEY, OKX_SECRET_KEY, OKX_PASSPHRASE |
| 代理连接失败 | VPN 未开启 | 开启代理或设置 `use_proxy=False` |
| SSL 握手失败 | 系统代理冲突 | 检查代理配置 |
| 读取超时 | 网络拥堵 | 更换 VPN 节点 |
