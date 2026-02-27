"""
Crypto Hold (持仓) API 模块

提供从 OKX 获取账户持仓信息的函数集合。
需要 API Key 认证（私有接口）。

函数列表:
    - get_positions: 获取当前持仓信息 (返回 JSON)
    - get_positions_history: 获取历史持仓信息 (返回 JSONL)

使用示例:
    from crypto_hold import get_positions, get_positions_history

    json_str = get_positions()
    jsonl_str = get_positions_history(inst_type="SWAP", limit=20)
"""

import os
import requests
import json
import hmac
import hashlib
import base64
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Optional
from urllib.parse import urlencode
from dotenv import load_dotenv

# ==============================================================================
# 配置常量
# ==============================================================================

DEFAULT_PROXY = {
    "http": "http://127.0.0.1:7890",
    "https": "http://127.0.0.1:7890"
}

DEFAULT_TIMEOUT = 10

# 加载 .env：从脚本自身位置向上定位到项目根目录
# 脚本路径: .opencode/skills/crypto/scripts/crypto_hold.py
# 项目根目录: 向上 4 层
_SCRIPT_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _SCRIPT_DIR.parent.parent.parent.parent  # -> D:\crypto
_ENV_PATH = _PROJECT_ROOT / ".env"
load_dotenv(_ENV_PATH)

apikey = os.getenv("OKX_API_KEY", "")
secretkey = os.getenv("OKX_SECRET_KEY", "")
passphrase = os.getenv("OKX_PASSPHRASE", "")

OKX_BASE_URL = "https://www.okx.com"

# 中文映射
_MGN_MODE = {"cross": "全仓", "isolated": "逐仓"}
_POS_SIDE = {"long": "多", "short": "空", "net": "净"}
_DIRECTION = {"long": "多", "short": "空"}

# 时区 UTC+8
_TZ_CN = timezone(timedelta(hours=8))


# ==============================================================================
# 辅助函数
# ==============================================================================

def _handle_request_error(error: Exception) -> None:
    """统一处理请求异常并打印错误信息。"""
    if isinstance(error, requests.exceptions.ProxyError):
        print("错误：代理连接失败。请检查：\n1. 你的梯子是否开启？\n2. 端口号是否正确？")
    elif isinstance(error, requests.exceptions.ReadTimeout):
        print("错误：读取超时。可能是网络拥堵或被服务器拦截，请尝试更换 VPN 节点。")
    elif isinstance(error, requests.exceptions.SSLError):
        print("错误：SSL 握手失败。请检查是否开启了'系统代理'但未配置Python代理。")
    else:
        print(f"发生错误: {error}")


def _generate_signature(
    timestamp: str,
    method: str,
    request_path: str,
    body: str = ''
) -> str:
    """
    生成 OKX API 签名。

    Args:
        timestamp: ISO 8601 格式时间戳
        method: HTTP 方法 ('GET' 或 'POST')
        request_path: 请求路径 (含查询参数)
        body: 请求体 (GET 请求为空字符串)

    Returns:
        Base64 编码的 HMAC SHA256 签名
    """
    message = timestamp + method + request_path + body
    mac = hmac.new(
        secretkey.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    )
    return base64.b64encode(mac.digest()).decode('utf-8')


def _get_auth_headers(method: str, request_path: str, body: str = '') -> dict:
    """
    生成 OKX API 认证请求头。

    Args:
        method: HTTP 方法 ('GET' 或 'POST')
        request_path: 请求路径 (含查询参数)
        body: 请求体

    Returns:
        包含认证信息的请求头字典
    """
    timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.') + \
        f"{datetime.now(timezone.utc).microsecond // 1000:03d}Z"
    sign = _generate_signature(timestamp, method, request_path, body)

    return {
        "OK-ACCESS-KEY": apikey,
        "OK-ACCESS-SIGN": sign,
        "OK-ACCESS-TIMESTAMP": timestamp,
        "OK-ACCESS-PASSPHRASE": passphrase,
        "Content-Type": "application/json"
    }


def _safe_float(val, default=None):
    """安全转换为 float，空值或异常返回 default。"""
    if val is None or val == '':
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def _ts_to_str(ts_ms) -> str:
    """毫秒时间戳 → 'YYYY-MM-DD HH:MM:SS' (UTC+8)。"""
    try:
        if ts_ms is None or ts_ms == '':
            return ""
        dt = datetime.fromtimestamp(int(ts_ms) / 1000, tz=_TZ_CN)
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except (ValueError, TypeError, OSError):
        return ""


def _calc_duration(c_time_ms, u_time_ms) -> str:
    """根据两个毫秒时间戳计算持续时长，返回中文描述。"""
    try:
        diff_sec = (int(u_time_ms) - int(c_time_ms)) / 1000
        if diff_sec < 0:
            return "未知"

        days = int(diff_sec // 86400)
        hours = int((diff_sec % 86400) // 3600)
        minutes = int((diff_sec % 3600) // 60)

        parts = []
        if days > 0:
            parts.append(f"{days} Day")
        if hours > 0:
            parts.append(f"{hours} Hour")
        if minutes > 0 or not parts:
            parts.append(f"{minutes} min")
        return "".join(parts)
    except (ValueError, TypeError):
        return "未知"


# ==============================================================================
# 主要 API 函数
# ==============================================================================

def get_positions(
    inst_type: Optional[str] = None,
    inst_id: Optional[str] = None,
    pos_id: Optional[str] = None,
    use_proxy: bool = False
) -> Optional[str]:
    """
    获取账户当前持仓信息。

    返回 JSON 字符串 (数组格式)，字段使用中文命名。

    限速：10次/2s

    Args:
        inst_type: 产品类型 ('MARGIN', 'SWAP', 'FUTURES', 'OPTION')
        inst_id: 交易产品ID，如 'BTC-USDT-SWAP'，支持逗号分隔多个
        pos_id: 持仓ID，支持多个
        use_proxy: 是否使用代理

    Returns:
        JSON 字符串，每个持仓包含:
            产品, 保证金模式, 方向, 杠杆, 持仓量, 开仓均价, 标记价,
            未实现收益, 收益率, 强平价, 保证金(U), 保证金率,
            开仓时间, 更新时间, 持仓时长, 费用{手续费, 资金费率}
        如果无持仓或请求失败返回 None

    Example:
        >>> result = get_positions(inst_type="SWAP")
        >>> print(result)
    """
    api_path = "/api/v5/account/positions"
    proxies = DEFAULT_PROXY if use_proxy else None

    # 构建查询参数
    params = {}
    if inst_type:
        params['instType'] = inst_type
    if inst_id:
        params['instId'] = inst_id
    if pos_id:
        params['posId'] = pos_id

    # 签名需要完整的请求路径 (含查询参数)
    query_string = urlencode(params) if params else ''
    request_path = f"{api_path}?{query_string}" if query_string else api_path

    try:
        print(f"正在获取持仓信息...")
        if inst_id:
            print(f"  产品: {inst_id}")
        if inst_type:
            print(f"  类型: {inst_type}")

        headers = _get_auth_headers("GET", request_path)
        url = f"{OKX_BASE_URL}{api_path}"

        response = requests.get(
            url,
            params=params,
            headers=headers,
            proxies=proxies,
            timeout=DEFAULT_TIMEOUT
        )
        response.raise_for_status()
        data = response.json()

        if data['code'] != '0':
            print(f"API 报错: {data['msg']}")
            return None

        positions = data.get('data', [])
        if not positions:
            print("提示：当前没有持仓。")
            return None

        # ── 构建中文字段结果 ──
        results = []
        for item in positions:
            c_time = item.get('cTime', '')
            u_time = item.get('uTime', '')

            # 方向：net 模式下根据 pos 正负判断多空
            pos_side = item.get('posSide', '')
            pos_val = _safe_float(item.get('pos'), 0)
            if pos_side == 'net':
                direction = "多" if pos_val >= 0 else "空"
            else:
                direction = _POS_SIDE.get(pos_side, pos_side)

            # 保证金(U)：notionalUsd / lever
            notional = _safe_float(item.get('notionalUsd'))
            lever = _safe_float(item.get('lever'))
            if notional and lever and lever > 0:
                margin_u = round(notional / lever, 2)
            else:
                margin_u = None

            record = {
                "uniID": hashlib.md5(f"{item.get('instId', '')}_{c_time}".encode()).hexdigest()[:16],
                "instId": item.get('instId', ''),
                "保证金模式": _MGN_MODE.get(item.get('mgnMode', ''), item.get('mgnMode', '')),
                "direction": direction,
                "leverage": _safe_float(item.get('lever')),
                "持仓量": pos_val,
                "开仓均价": _safe_float(item.get('avgPx')),
                "标记价": _safe_float(item.get('markPx')),
                "未实现收益": _safe_float(item.get('upl')),
                "收益率": f"{_safe_float(item.get('uplRatio'), 0) * 100:.2f}%",
                "强平价": _safe_float(item.get('liqPx')),
                "保证金(U)": margin_u,
                "保证金率": _safe_float(item.get('mgnRatio')),
                "开仓时间": _ts_to_str(c_time),
                "更新时间": _ts_to_str(u_time),
                "持仓时长": _calc_duration(c_time, u_time),
                "费用": _safe_float(item.get('fee'), 0) + _safe_float(item.get('fundingFee'), 0)
            }
            results.append(record)

        print(f"获取到 {len(results)} 条持仓记录。")
        return json.dumps(results, ensure_ascii=False, indent=2)

    except Exception as e:
        _handle_request_error(e)
        return None


def get_positions_history(
    inst_type: Optional[str] = None,
    inst_id: Optional[str] = None,
    mgn_mode: Optional[str] = None,
    close_type: Optional[str] = None,
    pos_id: Optional[str] = None,
    after: Optional[str] = None,
    before: Optional[str] = None,
    limit: int = 100,
    use_proxy: bool = False
) -> Optional[str]:
    """
    获取最近3个月有更新的历史持仓信息。

    返回 JSONL 字符串 (每行一个 JSON 对象)，字段使用中文命名。
    按仓位更新时间倒序排列。

    限速：10次/2s

    Args:
        inst_type: 产品类型 ('MARGIN', 'SWAP', 'FUTURES', 'OPTION')
        inst_id: 交易产品ID，如 'BTC-USD-SWAP'
        mgn_mode: 保证金模式，'cross' 或 'isolated'
        close_type: 平仓类型 ('1'~'6')
        pos_id: 持仓ID
        after: 查询 uTime 之前，毫秒时间戳
        before: 查询 uTime 之后，毫秒时间戳
        limit: 返回数量，最大100
        use_proxy: 是否使用代理

    Returns:
        JSONL 字符串 (每行一个 JSON)，每条记录包含:
            产品, 保证金模式, 方向, 杠杆, 开仓均价, 平仓均价,
            已实现收益, 收益率, 触发价, 保证金(U),
            开仓时间, 更新时间, 持仓时长, 费用{手续费, 资金费率}
        如果无数据或请求失败返回 None

    保证金(U) 计算方式:
        通过 realizedPnl / pnlRatio 反推初始保证金。
        当 pnlRatio 为 0 时无法计算，返回 None。

    Example:
        >>> result = get_positions_history(inst_type="SWAP", limit=10)
        >>> for line in result.splitlines():
        ...     print(json.loads(line))
    """
    api_path = "/api/v5/account/positions-history"
    proxies = DEFAULT_PROXY if use_proxy else None

    # 构建查询参数
    params = {}
    if inst_type:
        params['instType'] = inst_type
    if inst_id:
        params['instId'] = inst_id
    if mgn_mode:
        params['mgnMode'] = mgn_mode
    if close_type:
        params['type'] = close_type
    if pos_id:
        params['posId'] = pos_id
    if after:
        params['after'] = after
    if before:
        params['before'] = before
    if limit:
        params['limit'] = str(limit)

    # 签名需要完整的请求路径 (含查询参数)
    query_string = urlencode(params) if params else ''
    request_path = f"{api_path}?{query_string}" if query_string else api_path

    try:
        print(f"正在获取历史持仓信息...")
        if inst_id:
            print(f"  产品: {inst_id}")
        if inst_type:
            print(f"  类型: {inst_type}")

        headers = _get_auth_headers("GET", request_path)
        url = f"{OKX_BASE_URL}{api_path}"

        response = requests.get(
            url,
            params=params,
            headers=headers,
            proxies=proxies,
            timeout=DEFAULT_TIMEOUT
        )
        response.raise_for_status()
        data = response.json()

        if data['code'] != '0':
            print(f"API 报错: {data['msg']}")
            return None

        records = data.get('data', [])
        if not records:
            print("提示：没有历史持仓记录。")
            return None

        # ── 构建中文字段结果 (JSONL) ──
        lines = []
        for item in records:
            c_time = item.get('cTime', '')
            u_time = item.get('uTime', '')

            # 方向：优先用 direction，fallback 到 posSide
            direction_raw = item.get('direction', '')
            pos_side = item.get('posSide', '')
            if direction_raw:
                direction = _DIRECTION.get(direction_raw, direction_raw)
            else:
                direction = _POS_SIDE.get(pos_side, pos_side)

            # 保证金(U)：realizedPnl / pnlRatio 反推
            realized_pnl = _safe_float(item.get('realizedPnl'), 0)
            pnl_ratio = _safe_float(item.get('pnlRatio'), 0)
            if pnl_ratio != 0:
                margin_u = round(abs(realized_pnl / pnl_ratio), 2)
            else:
                margin_u = None

            record = {
                "uniID": hashlib.md5(f"{item.get('instId', '')}_{c_time}".encode()).hexdigest()[:16],
                "instId": item.get('instId', ''),
                "保证金模式": _MGN_MODE.get(item.get('mgnMode', ''), item.get('mgnMode', '')),
                "direction": direction,
                "leverage": _safe_float(item.get('lever')),
                "开仓均价": _safe_float(item.get('openAvgPx')),
                "平仓均价": _safe_float(item.get('closeAvgPx')),
                "已实现收益": _safe_float(item.get('realizedPnl')),
                "收益率": f"{pnl_ratio * 100:.2f}%",
                "触发价": _safe_float(item.get('triggerPx')),
                "保证金(U)": margin_u,
                "开仓时间": _ts_to_str(c_time),
                "更新时间": _ts_to_str(u_time),
                "持仓时长": _calc_duration(c_time, u_time),
                "费用": _safe_float(item.get('fee'), 0) + _safe_float(item.get('fundingFee'), 0)
            }
            lines.append(json.dumps(record, ensure_ascii=False))

        print(f"获取到 {len(lines)} 条历史持仓记录。")
        return "\n".join(lines)

    except Exception as e:
        _handle_request_error(e)
        return None


# ==============================================================================
# 测试入口
# ==============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Crypto Hold (持仓) API 模块测试")
    print("=" * 60)

    # 测试 1: 获取当前持仓 (JSON)
    print("\n[测试1] 获取当前持仓 (JSON)...")
    result = get_positions()
    if result is not None:
        print(result)

    # 测试 2: 获取永续合约持仓
    print("\n[测试2] 获取永续合约持仓...")
    result = get_positions(inst_type="SWAP")
    if result is not None:
        print(result)

    # 测试 3: 获取历史持仓 (JSONL)
    print("\n[测试3] 获取历史持仓 (JSONL)...")
    result = get_positions_history(limit=5)
    if result is not None:
        for line in result.splitlines():
            parsed = json.loads(line)
            print(json.dumps(parsed, ensure_ascii=False, indent=2))
            print("---")

    # 测试 4: 获取永续合约历史持仓
    print("\n[测试4] 获取永续合约历史持仓...")
    result = get_positions_history(inst_type="SWAP", limit=5)
    if result is not None:
        print(result)

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
