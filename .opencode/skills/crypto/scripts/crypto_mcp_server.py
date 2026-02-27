"""
CryptoView MCP Server

将 crypto_data 模块暴露为 MCP 工具，供 Agent 直接调用。

启动方式:
    python crypto_mcp_server.py

配置方式 (在 .opencode/mcp.json 中添加):
    {
        "mcpServers": {
            "crypto": {
                "command": "python",
                "args": ["D:/Crypto/.opencode/skills/crypto/scripts/crypto_mcp_server.py"]
            }
        }
    }
"""

import json
import sys
from typing import Any

# 导入你的数据模块
from crypto_data import (
    get_okx_candles,
    get_okx_funding_rate,
    get_okx_open_interest,
    get_long_short_ratio,
    get_okx_liquidation,
    get_top_trader_long_short_position_ratio,
    get_option_open_interest_volume_ratio,
    get_fear_greed_index
)

# 导入技术分析模块
from technical_analysis import TechnicalAnalysis, _analyze_single_asset


# ==============================================================================
# MCP Protocol Implementation
# ==============================================================================

# ==============================================================================
# K线数据缓存：key = (inst_id, bar)，value = List[Dict] (records格式)
# 当 get_candles 被调用后自动填充，供后续分析工具复用，避免重复请求
# ==============================================================================
_candles_cache: dict = {}


def send_response(response: dict) -> None:
    """发送 JSON-RPC 响应"""
    output = json.dumps(response) + "\n"
    sys.stdout.write(output)
    sys.stdout.flush()


def handle_initialize(request_id: Any) -> dict:
    """处理初始化请求"""
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            },
            "serverInfo": {
                "name": "crypto-data-server",
                "version": "1.0.0"
            }
        }
    }


def handle_tools_list(request_id: Any) -> dict:
    """返回可用工具列表"""
    tools = [
        {
            "name": "get_candles",
            "description": "获取 OKX 交易对的 K 线数据。支持 BTC-USDT, ETH-USDT, BNB-USDT, ZEC-USDT 等。",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "inst_id": {
                        "type": "string",
                        "description": "交易对，如 'BTC-USDT', 'ETH-USDT'"
                    },
                    "bar": {
                        "type": "string",
                        "description": "K线周期: '1m', '5m', '15m', '30m', '1H', '4H', '1D', '1W'",
                        "default": "1H"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "返回数据条数，最大 100",
                        "default": 100
                    }
                },
                "required": ["inst_id"]
            }
        },
        {
            "name": "get_funding_rate",
            "description": "获取永续合约的资金费率。用于判断市场多空情绪。",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "inst_id": {
                        "type": "string",
                        "description": "永续合约交易对，如 'BTC-USDT-SWAP', 'ETH-USDT-SWAP'"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "历史数据条数",
                        "default": 100
                    }
                },
                "required": ["inst_id"]
            }
        },
        {
            "name": "get_open_interest",
            "description": "获取未平仓合约量 (Open Interest)，包含美元价值。用于分析市场杠杆情况。",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "inst_id": {
                        "type": "string",
                        "description": "永续合约交易对，如 'BTC-USDT-SWAP'"
                    },
                    "period": {
                        "type": "string",
                        "description": "时间粒度: '5m', '1H', '1D'",
                        "default": "1H"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "历史数据条数",
                        "default": 100
                    }
                },
                "required": ["inst_id"]
            }
        },
        {
            "name": "get_long_short_ratio",
            "description": "获取精英交易员多空持仓人数比。用于判断散户情绪。",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "ccy": {
                        "type": "string",
                        "description": "币种，如 'BTC', 'ETH'"
                    },
                    "period": {
                        "type": "string",
                        "description": "时间粒度: '5m', '1H', '1D'",
                        "default": "1H"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "返回数据条数",
                        "default": 100
                    }
                },
                "required": ["ccy"]
            }
        },
        {
            "name": "get_liquidation",
            "description": "获取 OKX 交易对的历史爆仓数据统计。用于分析市场强制平仓情况和极端行情。",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "inst_id": {
                        "type": "string",
                        "description": "交易对，如 'BTC-USDT-SWAP', 'ETH-USDT-SWAP'"
                    },
                    "state": {
                        "type": "string",
                        "description": "订单状态: 'filled' (已成交), 'unfilled' (未成交)",
                        "default": "filled"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "返回数据条数，最大 100",
                        "default": 100
                    }
                },
                "required": ["inst_id"]
            }
        },
        {
            "name": "get_top_trader_position_ratio",
            "description": "获取精英交易员合约多空持仓仓位比。精英交易员指持仓价值前5%的用户。用于判断大户持仓方向。",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "inst_id": {
                        "type": "string",
                        "description": "产品ID，如 'BTC-USDT-SWAP', 'ETH-USDT-SWAP' (仅适用于交割/永续)"
                    },
                    "period": {
                        "type": "string",
                        "description": "时间粒度: '5m', '15m', '30m', '1H', '2H', '4H', '6H', '12H', '1D'",
                        "default": "5m"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "返回数据条数，最大 100",
                        "default": 100
                    }
                },
                "required": ["inst_id"]
            }
        },
        {
            "name": "get_option_oi_volume_ratio",
            "description": "获取看涨/看跌期权合约的持仓总量比和交易总量比。用于分析期权市场情绪。oiRatio > 1 表示看涨期权持仓多于看跌。",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "ccy": {
                        "type": "string",
                        "description": "币种，如 'BTC', 'ETH'"
                    },
                    "period": {
                        "type": "string",
                        "description": "时间粒度: '8H' 或 '1D'",
                        "default": "8H"
                    }
                },
                "required": ["ccy"]
            }
        },
        {
            "name": "get_fear_greed_index",
            "description": "获取 Fear and Greed Index (恐惧贪婪指数)。0-24: 极度恐惧, 25-49: 恐惧, 50-74: 贪婪, 75-100: 极度贪婪。",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "获取过去多少天的数据",
                        "default": 7
                    }
                },
                "required": []
            }
        },
        {
            "name": "get_analysis_summary",
            "description": "获取交易对的技术分析摘要，包含：当前价格、MA5/MA20、RSI14、MACD_DIF、ADX、斐波那契回撤位、区间涨跌幅%。适合快速判断趋势方向和强度。",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "inst_id": {
                        "type": "string",
                        "description": "交易对，如 'BTC-USDT', 'ETH-USDT'"
                    },
                    "bar": {
                        "type": "string",
                        "description": "K线周期: '1m','5m','15m','30m','1H','4H','1D','1W'",
                        "default": "1D"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "用于计算的K线数量，建议 ≥ 50",
                        "default": 100
                    }
                },
                "required": ["inst_id"]
            }
        },
        {
            "name": "get_all_indicators",
            "description": "获取交易对完整技术指标序列，包含：MA5/10/20/50、EMA12/26、RSI6/14、MACD(DIF/DEA/柱)、KDJ(K/D/J)、DMI(+DI/-DI/ADX)、布林带(上/中/下轨/带宽)、ATR14、OBV、价格变化%(1/5/20周期)、成交量变化%。通过 last_n 控制返回行数避免数据过多。",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "inst_id": {
                        "type": "string",
                        "description": "交易对，如 'BTC-USDT', 'ETH-USDT'"
                    },
                    "bar": {
                        "type": "string",
                        "description": "K线周期: '1m','5m','15m','30m','1H','4H','1D','1W'",
                        "default": "1D"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "获取的K线数量，最大100，建议 ≥ 50 保证指标准确",
                        "default": 100
                    },
                    "last_n": {
                        "type": "integer",
                        "description": "只返回最新的 N 行结果，默认 10",
                        "default": 10
                    }
                },
                "required": ["inst_id"]
            }
        },
        {
            "name": "get_support_resistance",
            "description": "获取交易对的支撑位列表、阻力位列表，以及斐波那契回撤关键价位(0/0.236/0.382/0.5/0.618/0.786/1.0)。适合判断买卖价格区间。",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "inst_id": {
                        "type": "string",
                        "description": "交易对，如 'BTC-USDT'"
                    },
                    "bar": {
                        "type": "string",
                        "description": "K线周期",
                        "default": "1D"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "K线数量",
                        "default": 100
                    },
                    "window": {
                        "type": "integer",
                        "description": "判断极值点的窗口大小，越大筛选越严格",
                        "default": 5
                    }
                },
                "required": ["inst_id"]
            }
        }
    ]
    
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": {"tools": tools}
    }


# ==============================================================================
# 数据清洗工具函数
# ==============================================================================

import math

def _clean_value(v):
    """将任意值转为 JSON 可序列化的 Python 原生类型，NaN/Inf 转 None"""
    if v is None:
        return None
    # pandas Timestamp / datetime
    if hasattr(v, 'isoformat'):
        return v.isoformat()
    # numpy bool
    if hasattr(v, 'item'):
        v = v.item()
    if isinstance(v, float):
        if math.isnan(v) or math.isinf(v):
            return None
        return round(v, 8)
    if isinstance(v, (int, str, bool)):
        return v
    # 兜底：转字符串
    return str(v)


def _clean_record(record: dict) -> dict:
    """清洗单行 dict"""
    return {k: _clean_value(v) for k, v in record.items()}


def _clean_df_to_records(df) -> list:
    """DataFrame → list[dict]，完整清洗"""
    return [_clean_record(row) for row in df.to_dict(orient="records")]


def _clean_any(obj):
    """递归清洗任意嵌套结构（dict/list/scalar）"""
    if isinstance(obj, dict):
        return {k: _clean_any(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_clean_any(i) for i in obj]
    return _clean_value(obj)


def handle_tool_call(request_id: Any, params: dict) -> dict:
    """执行工具调用"""
    tool_name = params.get("name")
    arguments = params.get("arguments", {})
    
    try:
        if tool_name == "get_candles":
            inst_id = arguments["inst_id"]
            bar     = arguments.get("bar", "1H")
            df = get_okx_candles(
                inst_id=inst_id,
                bar=bar,
                limit=arguments.get("limit", 100),
                use_proxy=False
            )
            if df is not None:
                # 转换为 JSON 友好格式
                result = df.to_dict(orient="records")
                # 将 datetime 转为字符串
                for row in result:
                    row["datetime"] = str(row["datetime"])
                # ---- 存入缓存，供后续分析工具复用 ----
                _candles_cache[(inst_id, bar)] = result
                content = json.dumps(result, indent=2)
            else:
                content = "Error: Failed to fetch candle data"
                
        elif tool_name == "get_funding_rate":
            df = get_okx_funding_rate(
                inst_id=arguments["inst_id"],
                limit=arguments.get("limit", 100),
                use_proxy=False
            )
            if df is not None:
                result = df.to_dict(orient="records")
                for row in result:
                    row["datetime"] = str(row["datetime"])
                content = json.dumps(result, indent=2)
            else:
                content = "Error: Failed to fetch funding rate data"
                
        elif tool_name == "get_open_interest":
            df = get_okx_open_interest(
                inst_id=arguments["inst_id"],
                period=arguments.get("period", "1H"),
                limit=arguments.get("limit", 100),
                use_proxy=False
            )
            if df is not None:
                result = df.to_dict(orient="records")
                for row in result:
                    row["datetime"] = str(row["datetime"])
                content = json.dumps(result, indent=2)
            else:
                content = "Error: Failed to fetch open interest data"
                
        elif tool_name == "get_long_short_ratio":
            df = get_long_short_ratio(
                ccy=arguments["ccy"],
                period=arguments.get("period", "1H"),
                limit=arguments.get("limit", 100),
                use_proxy=False
            )
            if df is not None:
                result = df.to_dict(orient="records")
                for row in result:
                    row["datetime"] = str(row["datetime"])
                content = json.dumps(result, indent=2)
            else:
                content = "Error: Failed to fetch long/short ratio data"
                
        elif tool_name == "get_liquidation":
            df = get_okx_liquidation(
                inst_id=arguments["inst_id"],
                state=arguments.get("state", "filled"),
                limit=arguments.get("limit", 100),
                use_proxy=False
            )
            if df is not None:
                result = df.to_dict(orient="records")
                for row in result:
                    row["datetime"] = str(row["datetime"])
                content = json.dumps(result, indent=2)
            else:
                content = "Error: Failed to fetch liquidation data"
                
        elif tool_name == "get_top_trader_position_ratio":
            df = get_top_trader_long_short_position_ratio(
                inst_id=arguments["inst_id"],
                period=arguments.get("period", "5m"),
                limit=arguments.get("limit", 100),
                use_proxy=False
            )
            if df is not None:
                result = df.to_dict(orient="records")
                for row in result:
                    row["datetime"] = str(row["datetime"])
                content = json.dumps(result, indent=2)
            else:
                content = "Error: Failed to fetch top trader position ratio data"
                
        elif tool_name == "get_option_oi_volume_ratio":
            df = get_option_open_interest_volume_ratio(
                ccy=arguments["ccy"],
                period=arguments.get("period", "8H"),
                use_proxy=False
            )
            if df is not None:
                result = df.to_dict(orient="records")
                for row in result:
                    row["datetime"] = str(row["datetime"])
                content = json.dumps(result, indent=2)
            else:
                content = "Error: Failed to fetch option OI/volume ratio data"
                
        elif tool_name == "get_fear_greed_index":
            df = get_fear_greed_index(
                days=arguments.get("days", 7),
                use_proxy=False
            )
            if df is not None:
                result = df.to_dict(orient="records")
                content = json.dumps(result, indent=2)
            else:
                content = "Error: Failed to fetch fear and greed index data"
                
        elif tool_name == "get_analysis_summary":
            inst_id = arguments["inst_id"]
            bar     = arguments.get("bar", "1D")
            limit   = int(arguments.get("limit", 100))

            cached = _candles_cache.get((inst_id, bar))
            if cached is not None:
                ta = TechnicalAnalysis(kline_data=cached)
                ta.inst_id = inst_id
                ta.bar = bar
            else:
                ta = TechnicalAnalysis(inst_id=inst_id, bar=bar, limit=limit, use_proxy=False)
            if ta.data.empty:  # type: ignore
                content = f"Error: 无法获取 {inst_id} 的K线数据"
            else:
                result = _analyze_single_asset(ta, inst_id)
                if result is None:
                    content = "Error: 分析失败，数据不足"
                else:
                    content = json.dumps(_clean_any(result), indent=2, ensure_ascii=False)

        elif tool_name == "get_all_indicators":
            inst_id = arguments["inst_id"]
            bar     = arguments.get("bar", "1D")
            limit   = int(arguments.get("limit", 100))
            last_n  = int(arguments.get("last_n", 10))

            cached = _candles_cache.get((inst_id, bar))
            if cached is not None:
                ta = TechnicalAnalysis(kline_data=cached)
                ta.inst_id = inst_id
                ta.bar = bar
            else:
                ta = TechnicalAnalysis(inst_id=inst_id, bar=bar, limit=limit, use_proxy=False)
            if ta.data.empty: # type: ignore
                content = f"Error: 无法获取 {inst_id} 的K线数据"
            else:
                df = ta.get_all_indicators()
                if last_n > 0:
                    df = df.tail(last_n)
                records = _clean_df_to_records(df)
                content = json.dumps(records, indent=2, ensure_ascii=False)

        elif tool_name == "get_support_resistance":
            inst_id = arguments["inst_id"]
            bar     = arguments.get("bar", "1D")
            limit   = int(arguments.get("limit", 100))
            window  = int(arguments.get("window", 5))

            cached = _candles_cache.get((inst_id, bar))
            if cached is not None:
                ta = TechnicalAnalysis(kline_data=cached)
                ta.inst_id = inst_id
                ta.bar = bar
            else:
                ta = TechnicalAnalysis(inst_id=inst_id, bar=bar, limit=limit, use_proxy=False)
            if ta.data.empty: # type: ignore
                content = f"Error: 无法获取 {inst_id} 的K线数据"
            else:
                support, resistance = ta.find_support_resistance(window=window)
                high_price  = float(ta.data['high'].max())  # type: ignore
                low_price   = float(ta.data['low'].min())  # type: ignore
                curr_price  = float(ta.data['close'].iloc[-1])  # type: ignore
                fib         = ta.calculate_fibonacci_retracement(high_price, low_price)

                result = {
                    "inst_id": inst_id,
                    "bar": bar,
                    "current_price":     _clean_value(curr_price),
                    "support_levels":    [_clean_value(v) for v in sorted(support,     reverse=True)],
                    "resistance_levels": [_clean_value(v) for v in sorted(resistance,  reverse=True)],
                    "fibonacci_retracement": {k: _clean_value(v) for k, v in fib.items()},
                    "price_range": {
                        "high": _clean_value(high_price),
                        "low":  _clean_value(low_price)
                    }
                }
                content = json.dumps(result, indent=2, ensure_ascii=False)

        else:
            content = f"Error: Unknown tool '{tool_name}'"
            
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": content
                    }
                ]
            }
        }
        
    except Exception as e:
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": -32603,
                "message": str(e)
            }
        }


def main():
    """MCP Server 主循环"""
    # 禁用 crypto_data 模块的 print 输出 (会干扰 JSON-RPC)
    import io
    import contextlib
    
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
                
            request = json.loads(line.strip())
            method = request.get("method")
            request_id = request.get("id")
            params = request.get("params", {})
            
            if method == "initialize":
                response = handle_initialize(request_id)
            elif method == "notifications/initialized":
                continue  # 无需响应
            elif method == "tools/list":
                response = handle_tools_list(request_id)
            elif method == "tools/call":
                # 静默执行，捕获 print 输出
                with contextlib.redirect_stdout(io.StringIO()):
                    with contextlib.redirect_stderr(io.StringIO()):
                        response = handle_tool_call(request_id, params)
            else:
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }
            
            send_response(response)
            
        except json.JSONDecodeError:
            continue
        except Exception as e:
            error_response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32603,
                    "message": str(e)
                }
            }
            send_response(error_response)


if __name__ == "__main__":
    main()