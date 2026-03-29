import streamlit as st
import pandas as pd
from datetime import datetime
import time
from plyer import notification
import plotly.graph_objects as go # New import for Plotly

from gold_data import get_domestic_gold_price, get_international_gold_price, get_historical_gold_data
from gold_predictor import predict_next_day_price, calculate_indicators
from gold_agent import get_exchange_rate # Re-using the exchange rate function

# Streamlit Page Configuration
st.set_page_config(layout="wide", page_title="黄金价格预测智能体")

# Initialize session state for notification cooldown
if 'last_notification_date' not in st.session_state:
    st.session_state.last_notification_date = {
        'spread_alert': None,
        'bullish_alert': None
    }

def send_notification(title, message, alert_type):
    today = datetime.now().date()
    if st.session_state.last_notification_date.get(alert_type) == today:
        # Already sent today, skip
        return

    try:
        notification.notify(
            title=title,
            message=message,
            app_name="黄金智能体",
            timeout=10  # 通知显示10秒
        )
        st.session_state.last_notification_date[alert_type] = today
    except Exception as e:
        st.warning(f"⚠️ 无法发送系统通知: {e}. 请确保您的系统支持通知，并且已安装相关依赖（如在macOS上可能需要`pyobjc`）。")

st.markdown("# 🚀 黄金价格预测智能体") # Changed to markdown with Emoji
st.write("实时监控、历史走势与智能预测，助您洞察黄金市场")

# Auto-refresh mechanism
last_update_time = st.empty()

# Main content area
placeholder = st.empty()

def update_dashboard():
    with placeholder.container():
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        last_update_time.markdown(f"**最后更新时间:** {now}")

        st.markdown("## 📈 实时黄金价格") # Changed to markdown with Emoji

        # Fetch data
        domestic = get_domestic_gold_price()
        international = get_international_gold_price()
        rate = get_exchange_rate()

        col1, col2, col3 = st.columns(3)

        # Notification flags
        should_notify_spread = False
        should_notify_bullish = False

        # Display domestic price
        with col1:
            if domestic and domestic['price'] is not None:
                st.metric("国内金价 (SGE Au99.99)", f"{domestic['price']:.2f} CNY/g", help=f"更新时间: {domestic['time']}")
                st.caption(f"最后更新: {domestic['time']}") # Added st.caption
            else:
                st.metric("国内金价 (SGE Au99.99)", "N/A", help="周末休市或暂无数据")
                st.caption("周末休市或暂无数据") # Added st.caption

        # Display international price
        with col2:
            if international and international['price'] is not None:
                st.metric("国际金价 (COMEX Gold)", f"{international['price']:.2f} USD/oz", help=f"更新时间: {international['time']}")
                st.caption(f"最后更新: {international['time']}") # Added st.caption
            else:
                st.metric("国际金价 (COMEX Gold)", "N/A", help="周末休市或暂无数据")
                st.caption("周末休市或暂无数据") # Added st.caption

        # Display exchange rate
        with col3:
            if rate is not None:
                st.metric("美元/人民币汇率", f"{rate:.4f}")
                st.caption("中国银行中间价") # Added st.caption
            else:
                st.metric("美元/人民币汇率", "N/A", help="数据无法获取")
                st.caption("数据无法获取") # Added st.caption

        st.divider() # Added divider

        st.markdown("## ⚖️ 内外盘溢价分析") # Changed to markdown with Emoji
        # Ensure domestic, international, their prices, and rate are all available before calculating spread
        if domestic and international and domestic['price'] is not None and international['price'] is not None and rate is not None:
            # Calculate international price in CNY/g
            intl_price_cny_g = (international['price'] / 31.1035) * rate
            spread = domestic['price'] - intl_price_cny_g
            
            st.write(f"内外盘溢价: {spread:.2f} CNY/g {'(国内更贵)' if spread > 0 else '(国际更贵)'}")

            # Check for spread notification condition
            if spread > 15:
                should_notify_spread = True
        else:
            st.warning("因周末休市或暂无数据，暂无法计算内外盘溢价")

        st.divider() # Added divider

        st.markdown("## 📊 历史价格走势 (近30天)") # Changed to markdown with Emoji
        hist_data = get_historical_gold_data(days=60) # Fetch more historical data to ensure enough points
        if hist_data is not None and not hist_data.empty:
            # Ensure the index is datetime for plotting
            hist_data.index = pd.to_datetime(hist_data.index)
            
            fig = go.Figure(data=[go.Scatter(
                x=hist_data.index,
                y=hist_data['Close'],
                mode='lines',
                line=dict(width=2, color='gold'),
                fill='tozeroy',
                fillcolor='rgba(255,215,0,0.2)', # Light gold fill
                name='COMEX Gold Close'
            )])

            fig.update_layout(
                title_text='COMEX Gold 近30天收盘价走势',
                title_x=0.5,
                xaxis_title='日期',
                yaxis_title='价格 (USD/oz)',
                hovermode='x unified'
            )
            st.plotly_chart(fig, use_container_width=True) # Used st.plotly_chart
        else:
            st.warning("⚠️ 无法获取历史数据，无法绘制走势图。")

        st.divider() # Added divider

        st.markdown("## 🧠 智能预测分析") # Changed to markdown with Emoji
        if hist_data is not None:
            prediction_res = predict_next_day_price(hist_data)
            indicators = calculate_indicators(hist_data)
            
            if prediction_res and indicators:
                col4, col5 = st.columns(2)
                with col4:
                    st.info(f"**下一交易日预测价:** {prediction_res['prediction']:.2f} USD/oz")
                    st.caption(f"基于过去20天数据线性回归预测，趋势: {prediction_res['trend']}") # Added st.caption
                with col5:
                    st.success(f"**趋势分析:** {prediction_res['trend']}")
                    st.caption(f"预测置信度: {prediction_res['confidence_score']:.2f} (仅供参考)") # Added st.caption
                
                st.write(f"技术指标: MA5={indicators['ma5']:.2f}, MA20={indicators['ma20']:.2f}")
                if indicators['rsi'] is not None:
                    st.write(f"RSI: {indicators['rsi']:.2f}")
                if indicators['macd'] is not None:
                    st.write(f"MACD: {indicators['macd']:.2f}, Signal: {indicators['macd_signal']:.2f}, Hist: {indicators['macd_hist']:.2f}")
                
                if indicators['signal'] == "强烈看多":
                    st.success(f"**操作建议: {indicators['signal']}**")
                    should_notify_bullish = True
                elif indicators['signal'] == "强烈看空":
                    st.error(f"**操作建议: {indicators['signal']}**")
                elif "看多" in indicators['signal']:
                    st.info(f"**操作建议: {indicators['signal']}**")
                elif "看空" in indicators['signal']:
                    st.warning(f"**操作建议: {indicators['signal']}**")
                else:
                    st.write(f"**操作建议: {indicators['signal']}**")

            else:
                st.warning("⚠️ 预测结果或技术指标计算失败。")
        else:
            st.warning("⚠️ 无法获取历史数据，暂无法进行预测。")

        st.caption("提示: 数据仅供参考，投资有风险。")

        # Send notifications if conditions met
        if should_notify_spread:
            send_notification("黄金溢价警报", f"内外盘溢价已超过15元/克！当前溢价: {spread:.2f} CNY/g", 'spread_alert')
        if should_notify_bullish:
            send_notification("黄金看多警报", f"系统检测到强烈看多信号！当前操作建议: {indicators['signal']}", 'bullish_alert')

# Initial run and auto-refresh loop
if __name__ == "__main__":
    update_dashboard()
    # Streamlit will rerun the script from top to bottom on each interaction.
    # To achieve auto-refresh, we can use time.sleep and st.rerun().
    # This will cause the script to re-execute after 60 seconds.
    time.sleep(60)
    st.rerun()