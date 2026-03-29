import akshare as ak
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

def get_domestic_gold_price():
    """
    获取国内黄金价格 (上海黄金交易所 SGE)
    返回实时或最新历史价格信息
    """
    try:
        # 尝试获取实时行情
        df = ak.spot_quotations_sge(symbol="Au99.99")
        if not df.empty:
            latest = df.iloc[-1]
            return {
                'symbol': 'Au99.99 (SGE)',
                'price': float(latest['现价']),
                'unit': 'CNY/g',
                'time': latest['更新时间']
            }
    except Exception:
        pass
    
    try:
        # 如果实时行情失败（如周末），尝试获取最新历史行情
        df_hist = ak.spot_hist_sge(symbol="Au99.99")
        if not df_hist.empty:
            latest = df_hist.iloc[-1]
            return {
                'symbol': 'Au99.99 (SGE)',
                'price': float(latest['close']),
                'unit': 'CNY/g',
                'time': f"{latest['date']} (收盘价)"
            }
    except Exception as e:
        print(f"获取国内历史金价失败: {e}")
        
    # Fallback to an "unavailable" state if both real-time and historical fail
    return {
        'symbol': 'Au99.99 (SGE)',
        'price': None,
        'unit': 'CNY/g',
        'time': '数据无法获取'
    }

def get_international_gold_price():
    """
    获取国际黄金价格 (COMEX 黄金期货 GC=F)
    """
    try:
        # 使用 yfinance 获取黄金期货实时数据
        gold = yf.Ticker("GC=F")
        data = gold.history(period="1d", interval="1m")
        if not data.empty:
            latest_price = data['Close'].iloc[-1]
            time_str = data.index[-1].strftime('%Y-%m-%d %H:%M:%S')
            return {
                'symbol': 'Gold Futures (GC=F)',
                'price': round(latest_price, 2),
                'unit': 'USD/oz',
                'time': time_str
            }
        return None
    except Exception as e:
        print(f"获取国际金价失败: {e}")
        # Fallback to an "unavailable" state
        return {
            'symbol': 'Gold Futures (GC=F)',
            'price': None,
            'unit': 'USD/oz',
            'time': '数据无法获取'
        }

def get_historical_gold_data(days=30):
    """
    获取历史金价数据用于预测
    """
    try:
        # 获取国际金价历史数据
        gold = yf.Ticker("GC=F")
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        df = gold.history(start=start_date.strftime('%Y-%m-%d'), end=end_date.strftime('%Y-%m-%d'))
        return df
    except Exception as e:
        print(f"获取历史数据失败: {e}")
        return None

if __name__ == "__main__":
    print("正在测试获取实时金价...")
    domestic = get_domestic_gold_price()
    if domestic:
        print(f"国内金价: {domestic['price']} {domestic['unit']} (时间: {domestic['time']})")
    
    international = get_international_gold_price()
    if international:
        print(f"国际金价: {international['price']} {international['unit']} (时间: {international['time']})")
