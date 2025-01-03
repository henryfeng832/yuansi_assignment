import akshare as ak
import pandas as pd
from datetime import datetime
import time

def download_stock_data():
    # 定义要下载的股票代码（这里选择了5只大盘股票作为示例）
    stock_codes = [
        "600519",  # 贵州茅台
        "601318",  # 中国平安
        "600036",  # 招商银行
        "600276",  # 恒瑞医药
        "601398"   # 工商银行
    ]
    
    # 设定固定的开始和结束日期
    end_date = "20241231"    # 2024年12月31日
    start_date = "20200101"  # 2020年1月1日（5年数据）
    
    # 遍历每只股票下载数据
    for stock_code in stock_codes:
        try:
            # 使用akshare获取股票数据
            df = ak.stock_zh_a_hist(
                symbol=stock_code,
                period="daily",
                start_date=start_date,
                end_date=end_date,
                adjust="qfq"  # 前复权
            )
            
            print(f"股票 {stock_code} 的原始列名: {df.columns.tolist()}")
            
            # 根据实际返回的列名重命名
            column_map = {
                '日期': '日期',
                '开盘': '开盘价',
                '收盘': '收盘价',
                '最高': '最高价',
                '最低': '最低价',
                '成交量': '成交量',
                '成交额': '成交额',
                '振幅': '振幅',
                '涨跌幅': '涨跌幅',
                '涨跌额': '涨跌额',
                '换手率': '换手率'
            }
            
            # 只重命名存在的列
            rename_dict = {k: v for k, v in column_map.items() if k in df.columns}
            df = df.rename(columns=rename_dict)
            
            # 保存为CSV文件，文件名中包含日期范围
            filename = f'stock_{stock_code}_2020_2024.csv'
            df.to_csv(filename, index=False, encoding='utf-8-sig')
            print(f"成功下载股票 {stock_code} 的数据并保存到 {filename}")
            
            # 添加延时，避免请求过于频繁
            time.sleep(1)
            
        except Exception as e:
            print(f"下载股票 {stock_code} 数据时出错: {str(e)}")
            print(f"尝试重新下载...")
            time.sleep(5)  # 出错时多等待几秒再重试
            try:
                df = ak.stock_zh_a_hist(
                    symbol=stock_code,
                    period="daily",
                    start_date=start_date,
                    end_date=end_date,
                    adjust="qfq"
                )
                # 重复上述处理逻辑
                rename_dict = {k: v for k, v in column_map.items() if k in df.columns}
                df = df.rename(columns=rename_dict)
                filename = f'stock_{stock_code}_2020_2024.csv'
                df.to_csv(filename, index=False, encoding='utf-8-sig')
                print(f"重试成功：下载股票 {stock_code} 的数据并保存到 {filename}")
            except Exception as e:
                print(f"重试失败：下载股票 {stock_code} 数据时出错: {str(e)}")

if __name__ == "__main__":
    download_stock_data()
