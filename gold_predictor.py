import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from gold_data import get_historical_gold_data

def predict_next_day_price(df):
    """
    使用简单的线性回归预测下一日的收盘价
    """
    if df is None or len(df) < 5:
        return None
    
    # 使用过去 20 天的数据
    data = df.tail(20).copy()
    data['Days'] = range(len(data))
    
    X = data[['Days']].values
    y = data['Close'].values
    
    model = LinearRegression()
    model.fit(X, y)
    
    # 预测下一天 (第 20 天)
    next_day = np.array([[len(data)]])
    prediction = model.predict(next_day)[0]
    
    # 计算趋势 (斜率)
    slope = model.coef_[0]
    trend = "上涨" if slope > 0 else "下跌"
    
    return {
        'prediction': round(prediction, 2),
        'trend': trend,
        'confidence_score': round(abs(slope) / y.mean() * 1000, 2) # 一个简化的置信度指标
    }

def calculate_rsi(df, window=14):
    if df is None or len(df) < window:
        return np.nan
    
    diff = df['Close'].diff()
    gain = diff.mask(diff < 0, 0)
    loss = -diff.mask(diff > 0, 0)
    
    avg_gain = gain.ewm(com=window - 1, min_periods=window).mean()
    avg_loss = loss.ewm(com=window - 1, min_periods=window).mean()
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1]

def calculate_macd(df, short_window=12, long_window=26, signal_window=9):
    if df is None or len(df) < long_window + signal_window:
        return {'macd': np.nan, 'signal': np.nan, 'hist': np.nan}
    
    exp1 = df['Close'].ewm(span=short_window, adjust=False).mean()
    exp2 = df['Close'].ewm(span=long_window, adjust=False).mean()
    macd = exp1 - exp2
    signal = macd.ewm(span=signal_window, adjust=False).mean()
    hist = macd - signal
    
    return {'macd': macd.iloc[-1], 'signal': signal.iloc[-1], 'hist': hist.iloc[-1]}

def calculate_indicators(df):
    """
    计算技术指标: MA5, MA20
    """
    if df is None or len(df) < 20:
        return None
    
    ma5 = df['Close'].rolling(window=5).mean().iloc[-1]
    ma20 = df['Close'].rolling(window=20).mean().iloc[-1]
    latest_close = df['Close'].iloc[-1]
    
    rsi = calculate_rsi(df)
    macd_res = calculate_macd(df)
    macd_line = macd_res['macd']
    macd_signal = macd_res['signal']
    macd_hist = macd_res['hist']

    signal = "观望"
    # 综合 MA, RSI, MACD 给出建议
    bullish_score = 0
    bearish_score = 0

    # MA 信号
    if latest_close > ma5 > ma20:
        bullish_score += 1
    elif latest_close < ma5 < ma20:
        bearish_score += 1

    # RSI 信号
    if rsi < 30: # 超卖
        bullish_score += 1
    elif rsi > 70: # 超买
        bearish_score += 1

    # MACD 信号
    if macd_line > macd_signal and macd_hist > 0: # 金叉且动能向上
        bullish_score += 1
    elif macd_line < macd_signal and macd_hist < 0: # 死叉且动能向下
        bearish_score += 1

    if bullish_score >= 2: # 至少两个指标看多
        signal = "强烈看多"
    elif bearish_score >= 2: # 至少两个指标看空
        signal = "强烈看空"
    elif bullish_score == 1 and bearish_score == 0: # 1个看多，0个看空
        signal = "看多"
    elif bearish_score == 1 and bullish_score == 0: # 1个看空，0个看多
        signal = "看空"
    
    return {
        'ma5': round(ma5, 2),
        'ma20': round(ma20, 2),
        'rsi': round(rsi, 2) if not np.isnan(rsi) else None,
        'macd': round(macd_line, 2) if not np.isnan(macd_line) else None,
        'macd_signal': round(macd_signal, 2) if not np.isnan(macd_signal) else None,
        'macd_hist': round(macd_hist, 2) if not np.isnan(macd_hist) else None,
        'signal': signal
    }

if __name__ == "__main__":
    print("正在获取历史数据进行预测...")
    hist_data = get_historical_gold_data(60)
    if hist_data is not None:
        prediction_res = predict_next_day_price(hist_data)
        indicators = calculate_indicators(hist_data)
        
        print(f"预测结果: 下一个交易日预期价格约为 {prediction_res['prediction']} USD/oz")
        print(f"趋势分析: {prediction_res['trend']}")
        print(f"MA5: {indicators['ma5']}, MA20: {indicators['ma20']}")
        if indicators['rsi'] is not None:
            print(f"RSI: {indicators['rsi']}")
        if indicators['macd'] is not None:
            print(f"MACD: {indicators['macd']}, Signal: {indicators['macd_signal']}, Hist: {indicators['macd_hist']}")
        print(f"操作信号建议: {indicators['signal']}")

