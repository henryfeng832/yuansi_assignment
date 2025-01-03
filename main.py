import streamlit as st
import mysql.connector
from mysql.connector import Error
import uuid
from datetime import datetime, timedelta
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
from pathlib import Path

# 配置页面
st.set_page_config(page_title="登录系统", layout="centered")

# 数据库连接函数
def get_database_connection():
    try:
        connection = mysql.connector.connect(
            host='dbconn.sealoshzh.site',
            port='36452',
            database='yuansi_assignment',
            user='root',
            password='t7d4j8m9'
        )
        return connection
    except Error as e:
        st.error(f"数据库连接错误：{e}")
        return None

# 创建新会话
def create_session(username):
    session_id = str(uuid.uuid4())
    connection = get_database_connection()
    if connection is not None:
        try:
            cursor = connection.cursor()
            # 删除该用户的旧会话
            cursor.execute("DELETE FROM sessions WHERE username = %s", (username,))
            # 创建新会话，设置1小时后过期
            expire_time = datetime.now() + timedelta(hours=1)
            cursor.execute("""
                INSERT INTO sessions (session_id, username, expire_time) 
                VALUES (%s, %s, %s)
            """, (session_id, username, expire_time))
            connection.commit()
            return session_id
        except Error as e:
            st.error(f"创建会话错误：{e}")
            return None
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    return None

# 验证会话是否有效
def verify_session(session_id):
    if not session_id:
        return None
    connection = get_database_connection()
    if connection is not None:
        try:
            cursor = connection.cursor()
            cursor.execute("""
                SELECT username FROM sessions 
                WHERE session_id = %s AND expire_time > NOW()
            """, (session_id,))
            result = cursor.fetchone()
            return result[0] if result else None
        except Error as e:
            st.error(f"验证会话错误：{e}")
            return None
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    return None

# 验证用户登录
def verify_login(username, password):
    connection = get_database_connection()
    if connection is not None:
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", 
                         (username, password))
            user = cursor.fetchone()
            return user is not None
        except Error as e:
            st.error(f"查询错误：{e}")
            return False
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    return False

# 删除会话
def delete_session(session_id):
    connection = get_database_connection()
    if connection is not None:
        try:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM sessions WHERE session_id = %s", (session_id,))
            connection.commit()
        except Error as e:
            st.error(f"删除会话错误：{e}")
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

# 加载股票数据
@st.cache_data
def load_stock_data(stock_code):
    file_path = f'stock_{stock_code}_2020_2024.csv'
    if Path(file_path).exists():
        df = pd.read_csv(file_path)
        df['日期'] = pd.to_datetime(df['日期'])
        return df
    return None

# 计算收益率和风险指标
def calculate_metrics(df):
    # 计算日收益率
    daily_returns = df['收盘价'].pct_change()
    
    # 计算日均收益率
    avg_daily_return = daily_returns.mean()
    
    # 计算月均收益率（按自然月）
    df['月份'] = df['日期'].dt.to_period('M')
    monthly_returns = df.groupby('月份')['收盘价'].apply(
        lambda x: (x.iloc[-1] / x.iloc[0] - 1)
    )
    avg_monthly_return = monthly_returns.mean()
    
    # 计算累计收益率
    cumulative_returns = (1 + daily_returns).cumprod() - 1
    
    # 计算最大回撤
    rolling_max = df['收盘价'].expanding().max()
    drawdowns = df['收盘价'] / rolling_max - 1
    max_drawdown = drawdowns.min()
    
    # 计算夏普比率（假设无风险利率为3%）
    risk_free_rate = 0.03
    annual_return = daily_returns.mean() * 252
    annual_volatility = daily_returns.std() * np.sqrt(252)
    sharpe_ratio = (annual_return - risk_free_rate) / annual_volatility
    
    # 计算今年以来收益率
    current_year = datetime.now().year - 1
    ytd_data = df[df['日期'].dt.year == current_year]
    ytd_return = (ytd_data['收盘价'].iloc[-1] / ytd_data['收盘价'].iloc[0] - 1) if not ytd_data.empty else 0
    
    return {
        'daily_returns': daily_returns,
        'avg_daily_return': avg_daily_return,
        'monthly_returns': monthly_returns,
        'avg_monthly_return': avg_monthly_return,
        'cumulative_returns': cumulative_returns,
        'max_drawdown': max_drawdown,
        'sharpe_ratio': sharpe_ratio,
        'ytd_return': ytd_return
    }

# 绘制股票走势图
def plot_stock_price(df, stock_code):
    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=df['日期'],
        open=df['开盘价'],
        high=df['最高价'],
        low=df['最低价'],
        close=df['收盘价'],
        name=stock_code
    ))
    fig.update_layout(
        title=f'{stock_code} 股票价格走势',
        yaxis_title='价格',
        xaxis_title='日期'
    )
    return fig

# 绘制累计收益率图
def plot_cumulative_returns(df, metrics, stock_code):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['日期'],
        y=metrics['cumulative_returns'],
        mode='lines',
        name='累计收益率'
    ))
    fig.update_layout(
        title=f'{stock_code} 累计收益率',
        yaxis_title='收益率',
        xaxis_title='日期'
    )
    return fig

def main():
    # 检查会话状态
    if 'session_id' not in st.session_state:
        st.session_state['session_id'] = None
    
    # 验证现有会话
    username = verify_session(st.session_state['session_id'])
    
    if not username:
        st.title("系统登录页")
        # 显示登录表单
        with st.form("login_form"):
            input_username = st.text_input("用户名")
            password = st.text_input("密码", type="password")
            submit_button = st.form_submit_button("登录")
            
            if submit_button:
                if input_username.strip() == "" or password.strip() == "":
                    st.warning("请输入用户名和密码")
                else:
                    if verify_login(input_username, password):
                        # 创建新会话
                        session_id = create_session(input_username)
                        if session_id:
                            st.session_state['session_id'] = session_id
                            st.success("登录成功！")
                            st.rerun()
                    else:
                        st.error("用户名或密码错误")
    else:
        st.title("股票数据分析系统")
        st.write(f"### 欢迎回来，{username}！")

        # 退出登录按钮
        if st.button("退出登录"):
            delete_session(st.session_state['session_id'])
            st.session_state['session_id'] = None
            st.rerun()
        
        # 股票代码列表
        stock_codes = [
            "600519",  # 贵州茅台
            "601318",  # 中国平安
            "600036",  # 招商银行
            "600276",  # 恒瑞医药
            "601398"   # 工商银行
        ]
        
        # 选择股票
        selected_stock = st.selectbox(
            "选择要分析的股票",
            stock_codes,
            format_func=lambda x: f"{x} - {get_stock_name(x)}"
        )
        
        # 加载股票数据
        df = load_stock_data(selected_stock)
        
        if df is not None:
            # 计算指标
            metrics = calculate_metrics(df)
            
            # 显示主要指标
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(f"今年以来收益率({datetime.now().year - 1})", f"{metrics['ytd_return']:.2%}")
                st.metric("日均收益率", f"{metrics['avg_daily_return']:.2%}")
            with col2:
                st.metric("最大回撤", f"{metrics['max_drawdown']:.2%}")
                st.metric("月均收益率", f"{metrics['avg_monthly_return']:.2%}")
            with col3:
                st.metric("夏普比率", f"{metrics['sharpe_ratio']:.2f}")
            
            # 添加收益率统计图表
            st.subheader("收益率统计")
            tab1, tab2 = st.tabs(["日收益率分布", "月收益率趋势"])
            
            with tab1:
                # 绘制日收益率分布直方图
                fig_daily = go.Figure()
                fig_daily.add_trace(go.Histogram(
                    x=metrics['daily_returns'],
                    nbinsx=50,
                    name="日收益率分布"
                ))
                fig_daily.update_layout(
                    title="日收益率分布图",
                    xaxis_title="收益率",
                    yaxis_title="频次"
                )
                st.plotly_chart(fig_daily)
                
            with tab2:
                # 绘制月收益率趋势图
                fig_monthly = go.Figure()
                fig_monthly.add_trace(go.Bar(
                    x=metrics['monthly_returns'].index.astype(str),
                    y=metrics['monthly_returns'].values,
                    name="月收益率"
                ))
                fig_monthly.update_layout(
                    title="月收益率趋势图",
                    xaxis_title="月份",
                    yaxis_title="收益率",
                    xaxis_tickangle=-45
                )
                st.plotly_chart(fig_monthly)
            
            # 显示K线图
            st.plotly_chart(plot_stock_price(df, selected_stock))
            
            # 显示累计收益率图
            st.plotly_chart(plot_cumulative_returns(df, metrics, selected_stock))
            
            # 显示月度收益率热力图
            df['月度收益率'] = df.groupby(df['日期'].dt.to_period('M'))['收盘价'].transform(
                lambda x: (x.iloc[-1] / x.iloc[0] - 1)
            )
            monthly_returns_pivot = df.pivot_table(
                values='月度收益率',
                index=df['日期'].dt.year,
                columns=df['日期'].dt.month,
                aggfunc='first'
            )
            
            fig = px.imshow(
                monthly_returns_pivot,
                labels=dict(x="月份", y="年份", color="收益率"),
                x=[f"{i}月" for i in range(1, 13)],
                y=monthly_returns_pivot.index,
                aspect="auto",
                color_continuous_scale="RdYlGn"
            )
            fig.update_layout(title="月度收益率热力图")
            st.plotly_chart(fig)
        
        else:
            st.error("无法加载股票数据，请确保数据文件存在")

def get_stock_name(code):
    stock_names = {
        "600519": "贵州茅台",
        "601318": "中国平安",
        "600036": "招商银行",
        "600276": "恒瑞医药",
        "601398": "工商银行"
    }
    return stock_names.get(code, code)

if __name__ == "__main__":
    main()

