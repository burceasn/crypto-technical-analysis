"""
Crypto Data API 模块

提供从 OKX 和 CoinMarketCap 获取加密货币市场数据的函数集合。

函数列表:
    - get_okx_candles: 获取 OKX K线数据
    - get_fear_greed_index: 获取 CoinMarketCap 恐惧与贪婪指数
    - get_okx_funding_rate: 获取资金费率结构
    - get_okx_open_interest: 获取未平仓合约量 (含美元价值)
    - get_long_short_ratio: 获取精英交易员多空持仓人数比
    - get_okx_liquidation: 获取爆仓订单数据

使用示例:
    from crypto_data import get_okx_candles, get_okx_funding_rate

    df = get_okx_candles("BTC-USDT", bar="1H", limit=100)
    funding_df = get_okx_funding_rate("BTC-USDT-SWAP", limit=50)
"""

import requests
import pandas as pd
import time
from typing import Optional
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ==============================================================================
# 配置常量
# ==============================================================================

DEFAULT_PROXY = {
    "http": "http://127.0.0.1:7890",
    "https": "http://127.0.0.1:7890"
}

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Connection": "close"
}

DEFAULT_TIMEOUT = 10


# ==============================================================================
# 辅助函数
# ==============================================================================

def _create_session(max_retries: int = 3) -> requests.Session:
    """
    创建一个带有重试策略的 requests Session。

    Args:
        max_retries: 最大重试次数

    Returns:
        配置好的 requests.Session 对象
    """
    session = requests.Session()
    retry_strategy = Retry(
        total=max_retries,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


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


# ==============================================================================
# 主要 API 函数
# ==============================================================================

def get_okx_candles(
    inst_id: str,
    bar: str = '1H',
    limit: int = 100,
    use_proxy: bool = True
) -> Optional[pd.DataFrame]:
    """
    获取 OKX 交易对的 K 线数据。

    Args:
        inst_id: 交易对，如 'BTC-USDT', 'ETH-USDT'
        bar: K线周期，可选值: '1m', '5m', '15m', '30m', '1H', '4H', '1D', '1W'
        limit: 返回数据条数，最大 100
        use_proxy: 是否使用代理

    Returns:
        包含以下列的 DataFrame:
            - datetime: 时间
            - open: 开盘价
            - high: 最高价
            - low: 最低价
            - close: 收盘价
            - vol: 成交量
        如果请求失败返回 None

    Example:
        >>> df = get_okx_candles("BTC-USDT", bar="1H", limit=100)
        >>> print(df.head())
    """
    url = "https://www.okx.com/api/v5/market/candles"
    params = {
        "instId": inst_id,
        "bar": bar,
        "limit": limit
    }
    proxies = DEFAULT_PROXY if use_proxy else None

    try:
        print(f"正在获取 {inst_id} K线数据 (周期: {bar})...")
        response = requests.get(
            url,
            params=params,
            proxies=proxies,
            timeout=DEFAULT_TIMEOUT
        )
        response.raise_for_status()
        data = response.json()

        if data['code'] != '0':
            print(f"API 报错: {data['msg']}")
            return None

        candles = data['data']
        df = pd.DataFrame(candles, columns=[
            'ts', 'open', 'high', 'low', 'close', 'vol', 'volCcy', 'volCcyQuote', 'confirm'
        ])

        # 数据处理
        df['datetime'] = pd.to_datetime(pd.to_numeric(df['ts']), unit='ms')
        df = df[['datetime', 'open', 'high', 'low', 'close', 'vol']]

        # 数值类型转换
        for col in ['open', 'high', 'low', 'close', 'vol']:
            df[col] = pd.to_numeric(df[col])

        df = df.sort_values('datetime').reset_index(drop=True)
        return df

    except Exception as e:
        _handle_request_error(e)
        return None


def get_fear_greed_index(
    api_key: str,
    days: int = 7
) -> Optional[pd.DataFrame]:
    """
    获取 CoinMarketCap 的 Fear and Greed Index 历史数据。

    Args:
        api_key: CoinMarketCap Pro API Key
        days: 获取过去多少天的数据 (默认 7 天)

    Returns:
        包含以下列的 DataFrame:
            - date: 日期 (YYYY-MM-DD 格式)
            - value: 指数值 (0-100)
            - value_classification: 分类描述 (如 'Fear', 'Greed' 等)
        如果请求失败返回 None

    Example:
        >>> df = get_fear_greed_index("your-api-key", days=30)
        >>> print(df.head())
    """
    url = 'https://pro-api.coinmarketcap.com/v3/fear-and-greed/historical'
    headers = {
        'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': api_key,
    }
    parameters = {
        'limit': str(days)
    }

    try:
        print(f"正在获取恐惧贪婪指数 (最近 {days} 天)...")
        response = requests.get(url, headers=headers, params=parameters)
        response.raise_for_status()
        data = response.json()

        if 'data' in data and data['data']:
            df = pd.DataFrame(data['data'])
            # 时间戳处理 (CMC 返回的是 Unix 秒级时间戳)
            df['timestamp'] = pd.to_numeric(df['timestamp'], errors='coerce')
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s', utc=True)
            df['date'] = df['timestamp'].dt.strftime('%Y-%m-%d')  # pyright: ignore[reportAttributeAccessIssue]
            # 只保留需要的列
            columns_to_keep = ['date', 'value', 'value_classification']
            final_cols = [col for col in columns_to_keep if col in df.columns]
            return df[final_cols]
        else:
            print(f"API 返回数据为空或结构异常: {data}")
            return None

    except requests.exceptions.HTTPError as err:
        print(f"HTTP 请求错误: {err}")
        try:
            print(f"API 错误详情: {response.json().get('status', {}).get('error_message')}")  # pyright: ignore[reportPossiblyUnboundVariable]
        except:
            pass
        return None
    except Exception as e:
        print(f"处理数据时发生错误: {e}")
        return None


def get_okx_funding_rate(
    inst_id: str,
    limit: int = 100,
    use_proxy: bool = True
) -> Optional[pd.DataFrame]:
    """
    获取 OKX 永续合约的资金费率结构。

    Args:
        inst_id: 永续合约交易对，如 'BTC-USDT-SWAP', 'ETH-USDT-SWAP'
        limit: 历史数据条数
        use_proxy: 是否使用代理

    Returns:
        包含以下列的 DataFrame:
            - datetime: 时间
            - fundingRate: 资金费率
            - realizedRate: 实际结算费率 (第0行为 NaN，因为尚未结算)
            - type: 数据类型 ('Current/Predicted' 或 'Settled')
        第 0 行为当前周期的预测费率，第 1~N 行为已结算的历史费率。
        如果请求失败返回 None

    Example:
        >>> df = get_okx_funding_rate("BTC-USDT-SWAP", limit=50)
        >>> print(df.head())
    """
    url_current = "https://www.okx.com/api/v5/public/funding-rate"
    url_history = "https://www.okx.com/api/v5/public/funding-rate-history"
    proxies = DEFAULT_PROXY if use_proxy else None

    params_history = {
        "instId": inst_id,
        "limit": limit
    }
    params_current = {
        "instId": inst_id
    }

    try:
        print(f"正在获取 {inst_id} 的资金费率数据...")

        # 获取历史已结算费率
        res_hist = requests.get(
            url_history,
            params=params_history,
            proxies=proxies,
            timeout=DEFAULT_TIMEOUT
        )
        res_hist.raise_for_status()
        data_hist = res_hist.json()

        if data_hist['code'] != '0':
            print(f"历史数据 API 报错: {data_hist['msg']}")
            return None

        df_hist = pd.DataFrame(data_hist['data'])
        df_hist = df_hist[['fundingTime', 'fundingRate', 'realizedRate']]
        df_hist['type'] = 'Settled'

        # 获取当前预测/进行中费率
        res_curr = requests.get(
            url_current,
            params=params_current,
            proxies=proxies,
            timeout=DEFAULT_TIMEOUT
        )
        res_curr.raise_for_status()
        data_curr = res_curr.json()

        if data_curr['code'] != '0':
            print(f"当前数据 API 报错: {data_curr['msg']}")
            return None

        # 构建第 0 行数据
        curr_record = data_curr['data'][0]
        row_0 = {
            'fundingTime': curr_record['fundingTime'],
            'fundingRate': curr_record['fundingRate'],
            'realizedRate': None,
            'type': 'Current/Predicted'
        }
        df_curr = pd.DataFrame([row_0])

        # 合并 DataFrame
        df_final = pd.concat([df_curr, df_hist], axis=0, ignore_index=True)

        # 数据清洗与类型转换
        df_final['datetime'] = pd.to_datetime(pd.to_numeric(df_final['fundingTime']), unit='ms')
        df_final['fundingRate'] = pd.to_numeric(df_final['fundingRate'])
        df_final['realizedRate'] = pd.to_numeric(df_final['realizedRate'])
        df_final = df_final[['datetime', 'fundingRate', 'realizedRate', 'type']]

        return df_final

    except Exception as e:
        _handle_request_error(e)
        return None


def get_okx_open_interest(
    inst_id: str,
    period: str = '1H',
    limit: int = 100,
    use_proxy: bool = True
) -> Optional[pd.DataFrame]:
    """
    获取 OKX 交易对的未平仓合约量 (Open Interest)，包含美元价值。

    Args:
        inst_id: 永续合约交易对，如 'BTC-USDT-SWAP'
        period: 时间粒度，可选值: '5m', '1H', '1D'
        limit: 历史数据条数
        use_proxy: 是否使用代理

    Returns:
        包含以下列的 DataFrame:
            - datetime: 时间
            - oiCcy: 持仓币数 (如 BTC 数量)
            - oiUsd: 持仓美元价值
            - type: 数据类型 ('Current (Real-time)' 或 'History')
        第 0 行为当前实时数据，第 1~N 行为历史快照。
        如果请求失败返回 None

    Example:
        >>> df = get_okx_open_interest("BTC-USDT-SWAP", period="1H", limit=24)
        >>> print(df.head())
    """
    timeout_seconds = 30
    max_retries = 3
    proxies = DEFAULT_PROXY if use_proxy else None
    session = _create_session(max_retries)

    url_history = "https://www.okx.com/api/v5/rubik/stat/contracts/open-interest-history"
    url_current_oi = "https://www.okx.com/api/v5/public/open-interest"
    url_mark_price = "https://www.okx.com/api/v5/public/mark-price"

    try:
        print(f"正在获取 {inst_id} 的持仓数据 (周期: {period})...")

        # 1. 获取历史数据 (自带美元价值)
        params_hist = {"instId": inst_id, "period": period, "limit": limit}
        res_hist = session.get(
            url_history,
            params=params_hist,
            proxies=proxies,
            headers=DEFAULT_HEADERS,
            timeout=timeout_seconds
        )
        res_hist.raise_for_status()
        data_hist = res_hist.json()

        if data_hist['code'] != '0':
            print(f"历史数据报错: {data_hist['msg']}")
            return None

        df_hist = pd.DataFrame(data_hist['data'], columns=['ts', 'oi', 'oiCcy', 'oiUsd'])
        df_hist = df_hist[['ts', 'oiCcy', 'oiUsd']]
        df_hist['type'] = 'History'

        # 2. 获取当前实时数据 (需要计算美元价值)
        res_curr = session.get(
            url_current_oi,
            params={"instId": inst_id},
            proxies=proxies,
            headers=DEFAULT_HEADERS,
            timeout=timeout_seconds
        )
        curr_data = res_curr.json()['data'][0]

        # 获取当前标记价格 (用于计算 USD 价值)
        res_price = session.get(
            url_mark_price,
            params={"instId": inst_id},
            proxies=proxies,
            headers=DEFAULT_HEADERS,
            timeout=timeout_seconds
        )
        price_data = res_price.json()['data'][0]

        current_oi_ccy = float(curr_data['oiCcy'])
        current_price = float(price_data['markPx'])
        current_oi_usd = current_oi_ccy * current_price

        # 构建第0行
        row_0 = {
            'ts': curr_data['ts'],
            'oiCcy': curr_data['oiCcy'],
            'oiUsd': current_oi_usd,
            'type': 'Current (Real-time)'
        }
        df_curr = pd.DataFrame([row_0])

        # 3. 合并与清洗
        df_final = pd.concat([df_curr, df_hist], axis=0, ignore_index=True)
        df_final['datetime'] = pd.to_datetime(pd.to_numeric(df_final['ts']), unit='ms')
        df_final['oiCcy'] = pd.to_numeric(df_final['oiCcy'])
        df_final['oiUsd'] = pd.to_numeric(df_final['oiUsd'])
        df_final = df_final[['datetime', 'oiCcy', 'oiUsd', 'type']]

        return df_final

    except Exception as e:
        _handle_request_error(e)
        return None


def get_long_short_ratio(
    ccy: str,
    period: str = '1H',
    limit: int = 100,
    use_proxy: bool = True
) -> Optional[pd.DataFrame]:
    """
    获取 OKX 精英交易员多空持仓人数比。

    Args:
        ccy: 币种，如 'BTC', 'ETH'
        period: 时间粒度，可选值: '5m', '1H', '1D'
        limit: 返回数据条数 (会强制截断到该数量)
        use_proxy: 是否使用代理

    Returns:
        包含以下列的 DataFrame:
            - ts: 时间戳
            - ratio: 多空比
            - datetime: 时间
            - longAccount: 做多人数占比 (如果 API 返回)
            - shortAccount: 做空人数占比 (如果 API 返回)
        按时间降序排列，最新的在最上面。
        如果请求失败返回 None

    Example:
        >>> df = get_long_short_ratio("BTC", period="1H", limit=24)
        >>> print(df.head())
    """
    base_url = "https://www.okx.com/api/v5/rubik/stat/contracts/long-short-account-ratio"
    proxies = DEFAULT_PROXY if use_proxy else None
    all_records = []
    end_ts = None

    print(f"正在获取 {ccy} 多空比数据...")

    # 循环获取 (处理 limit > 100 的情况)
    while len(all_records) < limit:
        params = {
            "ccy": ccy,
            "period": period,
            "limit": 100  # 单次请求最大值
        }
        if end_ts:
            params['end'] = end_ts

        try:
            response = requests.get(
                base_url,
                params=params,
                proxies=proxies,
                timeout=DEFAULT_TIMEOUT
            )
            data = response.json()

            if data['code'] != '0':
                print(f"API 报错: {data['msg']}")
                break

            records = data['data']
            if not records:
                break

            end_ts = records[-1][0]
            all_records.extend(records)

            if len(all_records) >= limit:
                break

            time.sleep(0.1)  # 防止请求过快

        except Exception as e:
            _handle_request_error(e)
            break

    if not all_records:
        return None

    # 创建 DataFrame (动态判断列数)
    cols = ['ts', 'ratio', 'longAccount', 'shortAccount']
    if len(all_records[0]) != 4:
        cols = ['ts', 'ratio']

    df = pd.DataFrame(all_records, columns=cols)

    # 数据清洗
    df['datetime'] = pd.to_datetime(pd.to_numeric(df['ts']), unit='ms')
    df['ratio'] = pd.to_numeric(df['ratio'])
    if 'longAccount' in df.columns:
        df['longAccount'] = pd.to_numeric(df['longAccount'])
        df['shortAccount'] = pd.to_numeric(df['shortAccount'])

    # 排序：最新的在最上面
    df = df.sort_values('datetime', ascending=False).reset_index(drop=True)

    # 强制截断到用户指定的条数
    df = df.iloc[:limit]

    return df


def get_okx_liquidation(
    inst_id: str,
    state: str = 'filled',
    limit: int = 100,
    use_proxy: bool = True
) -> Optional[pd.DataFrame]:
    """
    获取 OKX 永续合约的爆仓订单数据。

    Args:
        inst_id: 永续合约交易对，如 'BTC-USDT-SWAP', 'ETH-USDT-SWAP'
        state: 订单状态，可选值: 'filled' (已成交), 'unfilled' (未成交)
        limit: 返回数据条数，最大 100
        use_proxy: 是否使用代理

    Returns:
        包含以下列的 DataFrame:
            - datetime: 爆仓时间
            - side: 爆仓方向 ('sell': 多头爆仓, 'buy': 空头爆仓)
            - bkPx: 爆仓价格
            - sz: 爆仓数量 (张)
        如果请求失败或无数据返回 None

    Example:
        >>> df = get_okx_liquidation("BTC-USDT-SWAP", limit=50)
        >>> print(df.head())
    """
    url = "https://www.okx.com/api/v5/public/liquidation-orders"

    # 从 inst_id 提取 instFamily (BTC-USDT-SWAP -> BTC-USDT)
    if inst_id.endswith('-SWAP'):
        inst_family = inst_id[:-5]
    else:
        inst_family = inst_id

    params = {
        "instType": "SWAP",
        "instFamily": inst_family,
        "state": state,
        "limit": limit
    }
    proxies = DEFAULT_PROXY if use_proxy else None

    try:
        print(f"正在获取 {inst_id} 爆仓数据...")
        response = requests.get(
            url,
            params=params,
            proxies=proxies,
            timeout=DEFAULT_TIMEOUT
        )
        response.raise_for_status()
        data = response.json()

        if data['code'] != '0':
            print(f"API 报错: {data['msg']}")
            return None

        data_list = data.get('data', [])
        if not data_list:
            print(f"提示：[{inst_family}] 当前没有最近的爆仓单记录。")
            return None

        # 展开 details 数组
        all_details = []
        for item in data_list:
            for detail in item.get('details', []):
                all_details.append({
                    'ts': detail['ts'],
                    'side': detail['side'],
                    'bkPx': detail['bkPx'],
                    'sz': detail['sz']
                })

        if not all_details:
            print(f"提示：[{inst_family}] 爆仓数据 details 为空。")
            return None

        df = pd.DataFrame(all_details)

        # 数据处理
        df['datetime'] = pd.to_datetime(pd.to_numeric(df['ts']), unit='ms')
        df['bkPx'] = pd.to_numeric(df['bkPx'])
        df['sz'] = pd.to_numeric(df['sz'])
        df = df[['datetime', 'side', 'bkPx', 'sz']]

        # 按时间降序排列
        df = df.sort_values('datetime', ascending=False).reset_index(drop=True)
        return df

    except Exception as e:
        _handle_request_error(e)
        return None


# ==============================================================================
# 便捷导出函数
# ==============================================================================

def save_to_csv(df: pd.DataFrame, filename: str) -> None:
    """
    将 DataFrame 保存为 CSV 文件。

    Args:
        df: 要保存的 DataFrame
        filename: 文件名
    """
    if df is not None:
        df.to_csv(filename, index=False)
        print(f"数据已保存到 {filename}")
    else:
        print("DataFrame 为空，无法保存")


# ==============================================================================
# 测试入口
# ==============================================================================

if __name__ == "__main__":
    # 测试示例
    print("=" * 60)
    print("Crypto Data API 模块测试")
    print("=" * 60)

    # 测试 1: K线数据
    print("\n[测试1] 获取 BTC-USDT K线数据...")
    df_candles = get_okx_candles("BTC-USDT", bar="1H", limit=5)
    if df_candles is not None:
        print(df_candles)

    # 测试 2: 资金费率
    print("\n[测试2] 获取 BTC-USDT-SWAP 资金费率...")
    df_funding = get_okx_funding_rate("BTC-USDT-SWAP", limit=5)
    if df_funding is not None:
        print(df_funding)

    # 测试 3: 持仓数据
    print("\n[测试3] 获取 BTC-USDT-SWAP 持仓数据...")
    df_oi = get_okx_open_interest("BTC-USDT-SWAP", period="1H", limit=5)
    if df_oi is not None:
        pd.set_option('display.float_format', lambda x: '%.2f' % x)
        print(df_oi)

    # 测试 4: 多空比
    print("\n[测试4] 获取 BTC 多空比...")
    df_ls = get_long_short_ratio("BTC", period="1H", limit=5)
    if df_ls is not None:
        print(df_ls)

    # 测试 5: 爆仓数据
    print("\n[测试5] 获取 BTC-USDT-SWAP 爆仓数据...")
    df_liq = get_okx_liquidation("BTC-USDT-SWAP", limit=10)
    if df_liq is not None:
        print(df_liq)

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
