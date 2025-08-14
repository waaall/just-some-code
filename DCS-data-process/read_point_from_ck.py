#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ClickHouse数据点读取器
=====================

功能:
    - 从ClickHouse数据库读取指定数据点在指定时间范围内的数据
    - 支持命令行参数指定点名、起止时间（格式: YYYY-MM-DD HH:MM:SS）、输出Excel文件名
    - 查询结果保存为Excel文件

用法示例:
    python read_point_from_ck.py --point "20MCS-UNITMW" --start "2025-07-22 22:00:00" --end "2025-07-22 23:00:00" --output "2025070222_20MCS-UNITMW.xlsx"

作者: zhengxu
创建: 2025-08-14
"""

import argparse
import pandas as pd
import requests
from datetime import datetime


class ClickHousePointReader:
    def __init__(self, host='192.168.50.30', port=8123, database='ezhou', user='default', password='er3HsdSE2dQIS^VI'):
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.base_url = f"http://{host}:{port}"
        self.auth = (user, password)

    def test_connection_and_data(self):
        """测试连接并查看数据库信息"""
        try:
            # 测试连接
            sql = "SELECT 1"
            resp = requests.post(self.base_url, data=sql, auth=self.auth, timeout=30)
            print(f"[DEBUG] Connection test: {resp.status_code}")
            
            # 查看总记录数
            sql = f"SELECT COUNT(*) FROM {self.database}.points_data"
            resp = requests.post(self.base_url, data=sql, auth=self.auth, timeout=30)
            print(f"[DEBUG] Total records: {resp.text.strip()}")
            
            # 查看时间范围
            sql = f"SELECT MIN(date_time), MAX(date_time) FROM {self.database}.points_data"
            resp = requests.post(self.base_url, data=sql, auth=self.auth, timeout=30)
            print(f"[DEBUG] Time range: {resp.text.strip()}")
            
        except Exception as e:
            print(f"[ERROR] Test failed: {e}")

    def query_point_data(self, point_name, start_time, end_time):
        # 使用 toDateTime 函数确保时间格式正确，并指定数据库名
        sql = f"""SELECT date_time, point_value 
                  FROM {self.database}.points_data 
                  WHERE point_code = '{point_name}' 
                  AND date_time >= toDateTime('{start_time}') 
                  AND date_time <= toDateTime('{end_time}')"""
        try:
            resp = requests.post(self.base_url, data=sql, auth=self.auth, timeout=30)
            resp.raise_for_status()
            result_text = resp.text.strip()
            
            if not result_text:
                return pd.DataFrame(columns=["date_time", "point_value"])
                
            lines = result_text.split('\n')
            data = [line.split('\t') for line in lines if line.strip()]
            
            df = pd.DataFrame(data, columns=["date_time", "point_value"])
            if not df.empty:
                df["date_time"] = pd.to_datetime(df["date_time"])
                df["point_value"] = pd.to_numeric(df["point_value"], errors='coerce')
                df = df.sort_values("date_time")
            return df
        except Exception as e:
            print(f"[ERROR] 查询ClickHouse失败: {e}")
            return pd.DataFrame(columns=["date_time", "point_value"])

    def save_to_excel(self, df, point_name, start_time, output=None):
        if output is None:
            # 默认文件名: point+start_time(YYYYMMDDHHMMSS).xlsx
            tstr = start_time.replace('-', '').replace(':', '').replace(' ', '')
            output = f"{tstr}_{point_name}.xlsx"
        df.to_excel(output, index=False)
        return output


def main():
    parser = argparse.ArgumentParser(description="ClickHouse数据点读取器")
    parser.add_argument('--point', '-p', help='数据点名称 (如: 20MCS-UNITMW)')
    parser.add_argument('--start', help='起始时间 (格式: YYYY-MM-DD HH:MM:SS)')
    parser.add_argument('--end', help='结束时间 (格式: YYYY-MM-DD HH:MM:SS)')
    parser.add_argument('--output', '-o', help='输出Excel文件名 (默认自动生成)')
    parser.add_argument('--host', default='192.168.50.30', help='ClickHouse服务器地址')
    parser.add_argument('--port', type=int, default=8123, help='ClickHouse端口')
    parser.add_argument('--database', default='ezhou', help='数据库名称')
    parser.add_argument('--user', default='default', help='用户名')
    parser.add_argument('--password', default='er3HsdSE2dQIS^VI', help='密码')
    parser.add_argument('--test', action='store_true', help='测试数据库连接和数据')
    args = parser.parse_args()

    reader = ClickHousePointReader(
        host=args.host,
        port=args.port,
        database=args.database,
        user=args.user,
        password=args.password
    )
    
    if args.test:
        reader.test_connection_and_data()
        return

    if not args.point or not args.start or not args.end:
        print("[ERROR] --point, --start, --end 参数是必需的（除非使用 --test）")
        return

    # 限制时间范围不超过1小时
    t_start = datetime.strptime(args.start, "%Y-%m-%d %H:%M:%S")
    t_end = datetime.strptime(args.end, "%Y-%m-%d %H:%M:%S")
    if (t_end - t_start).total_seconds() > 3600:
        print("[ERROR] 时间范围不能超过1小时！")
        return

    df = reader.query_point_data(
        point_name=args.point,
        start_time=args.start,
        end_time=args.end
    )
    if df.empty:
        print("[INFO] 查询无数据，未生成Excel文件。")
        return
    output_file = args.output or reader.save_to_excel(df, args.point, args.start)
    if not args.output:
        print(f"[OK] 数据已保存到: {output_file}")
    else:
        print(f"[OK] 数据已保存到: {args.output}")

if __name__ == "__main__":
    main()
