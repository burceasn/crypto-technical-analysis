#!/usr/bin/env python3
"""
技术分析模块 - 统一的技术指标计算和分析类
整合了所有技术指标计算功能

数据接口: 使用 crypto_data.py 获取实时市场数据
"""

import json
import os
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Union

# 从 crypto_data 导入数据获取函数
from crypto_data import (
    get_okx_candles,
    get_okx_funding_rate,
    get_okx_open_interest,
    get_long_short_ratio,
    get_okx_liquidation
)


class TechnicalAnalysis:
    """技术分析类 - 统一入口
    
    支持两种数据获取方式:
    1. 直接传入K线数据 (原有方式)
    2. 通过API实时获取数据 (推荐)
    """
    
    def __init__(self, kline_data: Optional[List[Dict]] = None, 
                 inst_id: Optional[str] = None,
                 bar: str = '1D',
                 limit: int = 100,
                 use_proxy: bool = True):
        """
        初始化
        
        Args:
            kline_data: 直接传入K线数据列表 (与inst_id二选一)
            inst_id: 交易对代码，如 'BTC-USDT' (与kline_data二选一)
            bar: K线周期，如 '1m', '5m', '15m', '30m', '1H', '4H', '1D', '1W'
            limit: 获取数据条数
            use_proxy: 是否使用代理
        """
        self.inst_id = inst_id
        self.bar = bar
        self.limit = limit
        self.use_proxy = use_proxy
        self.data = pd.DataFrame()

        # 情况1: 直接传入数据
        if kline_data is not None:
            self.data = pd.DataFrame(kline_data)
            self._process_dataframe()
        # 情况2: 通过inst_id从API获取数据
        elif inst_id is not None:
            print(f"正在从API获取 {inst_id} 的K线数据 (周期: {bar})...")
            self.data = get_okx_candles(inst_id, bar=bar, limit=limit, use_proxy=use_proxy)
            if self.data is None:
                print(f"错误: 无法获取 {inst_id} 的数据")
                self.data = pd.DataFrame()
            else:
                print(f"成功获取 {len(self.data)} 条K线数据")
        else:
            print("错误: 必须提供 kline_data 或 inst_id 之一")


    def _process_dataframe(self):
        """处理DataFrame，确保数据格式正确"""
        if self.data is not None and not self.data.empty:
            self.data['datetime'] = pd.to_datetime(self.data['datetime'])
            self.data = self.data.sort_values('datetime').reset_index(drop=True)
            # 确保数值列为float类型
            for col in ['open', 'high', 'low', 'close', 'vol']:
                if col in self.data.columns:
                    self.data[col] = pd.to_numeric(self.data[col], errors='coerce')
    
    @classmethod
    def from_api(cls, inst_id: str, bar: str = '1D', limit: int = 100, use_proxy: bool = True):
        """
        类方法: 从API创建TechnicalAnalysis实例 (推荐方式)
        
        Args:
            inst_id: 交易对代码，如 'BTC-USDT'
            bar: K线周期
            limit: 数据条数
            use_proxy: 是否使用代理
            
        Returns:
            TechnicalAnalysis实例
        """
        return cls(inst_id=inst_id, bar=bar, limit=limit, use_proxy=use_proxy)
    
    @staticmethod
    def fetch_kline_data(inst_id: str, bar: str = '1D', limit: int = 100, use_proxy: bool = True) -> Optional[pd.DataFrame]:
        """
        静态方法: 直接从API获取K线数据
        
        Args:
            inst_id: 交易对代码，如 'BTC-USDT'
            bar: K线周期
            limit: 数据条数
            use_proxy: 是否使用代理
            
        Returns:
            包含K线数据的DataFrame，失败返回None
        """
        return get_okx_candles(inst_id, bar=bar, limit=limit, use_proxy=use_proxy)
    
    @staticmethod
    def fetch_funding_rate(inst_id: str, limit: int = 100, use_proxy: bool = True) -> Optional[pd.DataFrame]:
        """
        静态方法: 获取资金费率数据
        
        Args:
            inst_id: 永续合约交易对，如 'BTC-USDT-SWAP'
            limit: 数据条数
            use_proxy: 是否使用代理
            
        Returns:
            包含资金费率的DataFrame，失败返回None
        """
        return get_okx_funding_rate(inst_id, limit=limit, use_proxy=use_proxy)
    
    @staticmethod
    def fetch_open_interest(inst_id: str, period: str = '1H', limit: int = 100, use_proxy: bool = True) -> Optional[pd.DataFrame]:
        """
        静态方法: 获取持仓量数据
        
        Args:
            inst_id: 永续合约交易对，如 'BTC-USDT-SWAP'
            period: 时间粒度
            limit: 数据条数
            use_proxy: 是否使用代理
            
        Returns:
            包含持仓量数据的DataFrame，失败返回None
        """
        return get_okx_open_interest(inst_id, period=period, limit=limit, use_proxy=use_proxy)
    
    @staticmethod
    def fetch_long_short_ratio(ccy: str, period: str = '1H', limit: int = 100, use_proxy: bool = True) -> Optional[pd.DataFrame]:
        """
        静态方法: 获取多空比数据
        
        Args:
            ccy: 币种，如 'BTC', 'ETH'
            period: 时间粒度
            limit: 数据条数
            use_proxy: 是否使用代理
            
        Returns:
            包含多空比数据的DataFrame，失败返回None
        """
        return get_long_short_ratio(ccy, period=period, limit=limit, use_proxy=use_proxy)
    
    @staticmethod
    def fetch_liquidation(inst_id: str, state: str = 'filled', limit: int = 100, use_proxy: bool = True) -> Optional[pd.DataFrame]:
        """
        静态方法: 获取爆仓数据
        
        Args:
            inst_id: 永续合约交易对，如 'BTC-USDT-SWAP'
            state: 订单状态
            limit: 数据条数
            use_proxy: 是否使用代理
            
        Returns:
            包含爆仓数据的DataFrame，失败返回None
        """
        return get_okx_liquidation(inst_id, state=state, limit=limit, use_proxy=use_proxy)
    
    # ==================== 趋势指标 ====================
    
    def calculate_ma(self, period: int) -> pd.Series:
        """计算简单移动平均线"""
        return self.data['close'].rolling(window=period).mean() # type: ignore
    
    def calculate_ema(self, period: int) -> pd.Series:
        """计算指数移动平均线"""
        return self.data['close'].ewm(span=period, adjust=False).mean() # type: ignore
    
    def calculate_dmi(self, period: int = 14) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """计算DMI指标，返回+DI, -DI, ADX"""
        high = self.data['high'] # type: ignore
        low = self.data['low'] # type: ignore
        close = self.data['close'] # type: ignore
        
        plus_dm = high.diff()
        minus_dm = -low.diff()
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm < 0] = 0
        plus_dm[plus_dm <= minus_dm] = 0
        minus_dm[minus_dm <= plus_dm] = 0
        
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        
        plus_di = 100 * plus_dm.rolling(window=period).mean() / atr
        minus_di = 100 * minus_dm.rolling(window=period).mean() / atr
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(window=period).mean()
        
        return plus_di, minus_di, adx
    
    # ==================== 动量指标 ====================
    
    def calculate_rsi(self, period: int = 14) -> pd.Series:
        """计算RSI指标"""
        delta = self.data['close'].diff() # type: ignore
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def calculate_macd(self, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """计算MACD指标，返回DIF, DEA, MACD柱"""
        exp1 = self.data['close'].ewm(span=fast, adjust=False).mean() # type: ignore
        exp2 = self.data['close'].ewm(span=slow, adjust=False).mean() # type: ignore
        dif = exp1 - exp2
        dea = dif.ewm(span=signal, adjust=False).mean()
        histogram = (dif - dea) * 2
        return dif, dea, histogram
    
    def calculate_kdj(self, n: int = 9, m1: int = 3, m2: int = 3) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """计算KDJ指标，返回K, D, J"""
        low_list = self.data['low'].rolling(window=n, min_periods=n).min() # type: ignore
        high_list = self.data['high'].rolling(window=n, min_periods=n).max() # type: ignore
        rsv = (self.data['close'] - low_list) / (high_list - low_list) * 100 # type: ignore
        k = rsv.ewm(com=m1-1, adjust=False).mean()
        d = k.ewm(com=m2-1, adjust=False).mean()
        j = 3 * k - 2 * d
        return k, d, j
    
    # ==================== 波动率指标 ====================
    
    def calculate_bollinger_bands(self, period: int = 20, std_dev: int = 2) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """计算布林带，返回上轨、中轨、下轨"""
        middle = self.data['close'].rolling(window=period).mean() # type: ignore
        std = self.data['close'].rolling(window=period).std() # type: ignore
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)
        return upper, middle, lower
    
    def calculate_atr(self, period: int = 14) -> pd.Series:
        """计算ATR（平均真实波幅）"""
        high_low = self.data['high'] - self.data['low'] # type: ignore
        high_close = abs(self.data['high'] - self.data['close'].shift()) # type: ignore
        low_close = abs(self.data['low'] - self.data['close'].shift()) # type: ignore
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        return true_range.rolling(window=period).mean()
    
    # ==================== 成交量指标 ====================
    
    def calculate_obv(self) -> pd.Series:
        """计算OBV（能量潮）"""
        obv = pd.Series(index=self.data.index, dtype=float) # type: ignore
        obv.iloc[0] = self.data['vol'].iloc[0] # type: ignore
        for i in range(1, len(self.data)): # type: ignore
            if self.data['close'].iloc[i] > self.data['close'].iloc[i-1]: # type: ignore
                obv.iloc[i] = obv.iloc[i-1] + self.data['vol'].iloc[i] # type: ignore
            elif self.data['close'].iloc[i] < self.data['close'].iloc[i-1]: # type: ignore
                obv.iloc[i] = obv.iloc[i-1] - self.data['vol'].iloc[i] # type: ignore
            else:
                obv.iloc[i] = obv.iloc[i-1]
        return obv
    
    # ==================== 价格结构指标 ====================
    
    def calculate_fibonacci_retracement(self, high: float, low: float) -> Dict[str, float]:
        """计算斐波那契回撤位"""
        diff = high - low
        return {
            '0.0': high,
            '0.236': high - diff * 0.236,
            '0.382': high - diff * 0.382,
            '0.5': high - diff * 0.5,
            '0.618': high - diff * 0.618,
            '0.786': high - diff * 0.786,
            '1.0': low
        }
    
    def find_support_resistance(self, window: int = 5) -> Tuple[List[float], List[float]]:
        """寻找支撑阻力位"""
        highs = self.data['high'] # type: ignore
        lows = self.data['low'] # type: ignore
        
        resistance_levels = []
        for i in range(window, len(highs) - window):
            if all(highs.iloc[i] >= highs.iloc[i-j] for j in range(1, window+1)) and \
               all(highs.iloc[i] >= highs.iloc[i+j] for j in range(1, window+1)):
                resistance_levels.append(highs.iloc[i])
        
        support_levels = []
        for i in range(window, len(lows) - window):
            if all(lows.iloc[i] <= lows.iloc[i-j] for j in range(1, window+1)) and \
               all(lows.iloc[i] <= lows.iloc[i+j] for j in range(1, window+1)):
                support_levels.append(lows.iloc[i])
        
        return support_levels, resistance_levels
    
    def get_all_indicators(self) -> pd.DataFrame:
        """计算所有技术指标并返回包含指标的DataFrame"""
        if self.data.empty: # type: ignore
            return pd.DataFrame()
        
        close = self.data['close'] # type: ignore
        high = self.data['high'] # type: ignore
        low = self.data['low'] # type: ignore
        volume = self.data['vol'] # type: ignore
        
        # 创建新的DataFrame存储指标
        indicators = pd.DataFrame(index=self.data.index) # type: ignore
        indicators['datetime'] = self.data['datetime'] # type: ignore
        
        # 价格数据
        indicators['open'] = self.data['open'] # type: ignore
        indicators['high'] = self.data['high']# type: ignore
        indicators['low'] = self.data['low'] # type: ignore
        indicators['close'] = self.data['close'] # type: ignore
        indicators['volume'] = self.data['vol'] # type: ignore

        # 趋势指标 - 移动平均线
        indicators['ma5'] = self.calculate_ma(5)
        indicators['ma10'] = self.calculate_ma(10)
        indicators['ma20'] = self.calculate_ma(20)
        indicators['ma50'] = self.calculate_ma(50)
        indicators['ema12'] = self.calculate_ema(12)
        indicators['ema26'] = self.calculate_ema(26)
        
        # 动量指标 - RSI
        indicators['rsi14'] = self.calculate_rsi(14)
        indicators['rsi6'] = self.calculate_rsi(6)
        
        # 动量指标 - MACD
        dif, dea, macd_hist = self.calculate_macd()
        indicators['macd_dif'] = dif
        indicators['macd_dea'] = dea
        indicators['macd_hist'] = macd_hist
        
        # 动量指标 - KDJ
        k, d, j = self.calculate_kdj()
        indicators['kdj_k'] = k
        indicators['kdj_d'] = d
        indicators['kdj_j'] = j
        
        # 趋势强度 - DMI
        plus_di, minus_di, adx = self.calculate_dmi()
        indicators['dmi_plus_di'] = plus_di
        indicators['dmi_minus_di'] = minus_di
        indicators['dmi_adx'] = adx
        
        # 波动率指标 - 布林带
        bb_upper, bb_middle, bb_lower = self.calculate_bollinger_bands()
        indicators['bb_upper'] = bb_upper
        indicators['bb_middle'] = bb_middle
        indicators['bb_lower'] = bb_lower
        indicators['bb_width'] = (bb_upper - bb_lower) / bb_middle
        
        # 波动率指标 - ATR
        indicators['atr14'] = self.calculate_atr(14)
        
        # 成交量指标 - OBV
        indicators['obv'] = self.calculate_obv()
        
        # 价格变化百分比
        indicators['price_change_1'] = close.pct_change(periods=1) * 100
        indicators['price_change_5'] = close.pct_change(periods=5) * 100
        indicators['price_change_20'] = close.pct_change(periods=20) * 100
        
        # 成交量变化
        indicators['volume_change'] = volume.pct_change() * 100
        indicators['volume_sma20'] = volume.rolling(window=20).mean()
        
        return indicators


def analyze_all_assets(data_file: Optional[str] = None, 
                       inst_ids: Optional[List[str]] = None,
                       bar: str = '1D',
                       limit: int = 100,
                       use_proxy: bool = True):
    """
    分析所有资产
    
    支持两种方式:
    1. 从JSON文件读取数据 (data_file参数)
    2. 直接从API获取数据 (inst_ids参数)
    
    Args:
        data_file: JSON数据文件路径 (与inst_ids二选一)
        inst_ids: 交易对列表，如 ['BTC-USDT', 'ETH-USDT'] (与data_file二选一)
        bar: K线周期
        limit: 数据条数
        use_proxy: 是否使用代理
        
    Returns:
        分析结果字典
    """
    results = {}
    
    # 方式1: 从JSON文件读取
    if data_file:
        try:
            with open(data_file, 'r', encoding='utf-8') as f:
                all_data = json.load(f)
        except FileNotFoundError:
            print(f"错误: 找不到文件 {data_file}")
            return {}
        
        for asset, data in all_data.items():
            print(f"\n{'='*40}\n分析 {asset}\n{'='*40}")
            kline_data = data.get('kline_1d', [])
            if not kline_data:
                continue
            
            ta = TechnicalAnalysis(kline_data)
            result = _analyze_single_asset(ta, asset)
            if result:
                results[asset] = result
                print(f"  ✓ {asset} 分析完成")
    
    # 方式2: 直接从API获取
    elif inst_ids:
        for inst_id in inst_ids:
            print(f"\n{'='*40}\n分析 {inst_id}\n{'='*40}")
            
            # 从API获取数据
            ta = TechnicalAnalysis.from_api(inst_id, bar=bar, limit=limit, use_proxy=use_proxy)
            
            if ta.data.empty: # type: ignore
                print(f"  ✗ {inst_id} 数据获取失败，跳过")
                continue
            
            result = _analyze_single_asset(ta, inst_id)
            if result:
                results[inst_id] = result
                print(f"  ✓ {inst_id} 分析完成")
    else:
        print("错误: 必须提供 data_file 或 inst_ids 之一")
        return {}
    
    # 保存结果到 result 文件夹，使用带时间戳的文件名
    result_dir = 'result'
    if not os.path.exists(result_dir):
        os.makedirs(result_dir)
    
    # 生成带时间戳的文件名
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = os.path.join(result_dir, f'technical_analysis_{timestamp}.json')
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n结果已保存至: {output_file}")
    return results


def _analyze_single_asset(ta: 'TechnicalAnalysis', asset: str) -> Optional[Dict]:
    """
    分析单个资产
    
    Args:
        ta: TechnicalAnalysis实例
        asset: 资产名称
        
    Returns:
        分析结果字典，失败返回None
    """
    if ta.data.empty: # type: ignore
        return None
    
    indicators = {}
    
    # 1. 趋势
    indicators['MA5'] = ta.calculate_ma(5).iloc[-1] if len(ta.data) >= 5 else None # type: ignore
    indicators['MA20'] = ta.calculate_ma(20).iloc[-1] if len(ta.data) >= 20 else None # type: ignore
    plus_di, minus_di, adx = ta.calculate_dmi(14)
    indicators['ADX'] = adx.iloc[-1] if not adx.empty else None
    
    # 2. 动量
    rsi = ta.calculate_rsi(14)
    indicators['RSI'] = rsi.iloc[-1] if not rsi.empty else None
    dif, dea, hist = ta.calculate_macd()
    indicators['MACD_DIF'] = dif.iloc[-1] if not dif.empty else None
    
    # 3. 价格结构
    high_price = ta.data['high'].max() # type: ignore
    low_price = ta.data['low'].min() # type: ignore
    current_price = ta.data['close'].iloc[-1] # type: ignore
    
    indicators['Fib_Levels'] = ta.calculate_fibonacci_retracement(high_price, low_price)
    indicators['Current_Price'] = current_price
    indicators['Price_Change_%'] = ((current_price - ta.data['close'].iloc[0]) / ta.data['close'].iloc[0] * 100) # type: ignore
    
    # 结果打包
    return {
        'asset': asset,
        'indicators': indicators,
        'data_summary': {
            'total_candles': len(ta.data), # type: ignore
            'date_range': {
                'start': ta.data['datetime'].iloc[0].isoformat() if len(ta.data) > 0 else None, # type: ignore
                'end': ta.data['datetime'].iloc[-1].isoformat() if len(ta.data) > 0 else None # type: ignore
            }
        }
    }


if __name__ == '__main__':
    pass