# -*- coding: utf-8 -*-
"""
Quant Data 核心客户端

提供 DWD/DIM 层数据的便捷查询接口。
"""
import pandas as pd
from typing import List, Optional, Union
from loguru import logger

from .readers.daily import DailyReader
from .readers.finance import FinanceReader
from .readers.dim import DimReader


class QuantDataClient:
    """
    量化数据查询客户端
    
    提供 DWD/DIM 层数据查询，支持自动复权。
    
    Args:
        host: StarRocks FE 地址
        port: StarRocks FE Query 端口（默认 9030）
        user: 用户名
        password: 密码
        database: 默认数据库（可选，各接口会自动切换）
    
    Example:
        >>> client = QuantDataClient(host="", port=9030, user="xxx", password="xxx")
        >>> df = client.get_daily(symbols=["000001"], start_date="2024-01-01", adjust="qfq")
    """
    
    def __init__(
        self,
        host: str,
        port: int = 9030,
        user: str = None,
        password: str = None,
        database: str = None
    ):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        
        # 连接参数字典，供 Reader 使用
        self._conn_params = {
            "host": host,
            "port": port,
            "user": user,
            "passwd": password,
        }
        
        # 初始化各数据读取器
        self._daily_reader = DailyReader(self._conn_params)
        self._finance_reader = FinanceReader(self._conn_params)
        self._dim_reader = DimReader(self._conn_params)
        
        logger.info(f"QuantDataClient 初始化完成: {host}:{port}")
    
    # ========================================
    # DWD 层数据接口
    # ========================================
    
    def get_daily(
        self,
        symbols: Union[str, List[str]] = None,
        start_date: str = None,
        end_date: str = None,
        adjust: str = None,
        fields: List[str] = None
    ) -> pd.DataFrame:
        """
        获取股票日线数据
        
        Args:
            symbols: 股票代码，如 "000001" 或 ["000001", "600519"]
            start_date: 开始日期，格式 "YYYY-MM-DD"
            end_date: 结束日期，格式 "YYYY-MM-DD"
            adjust: 复权类型
                - None: 不复权（原始价格）
                - "qfq": 前复权（以最新价格为基准）
                - "hfq": 后复权（以上市首日为基准）
            fields: 返回字段列表（可选，默认返回常用字段）
        
        Returns:
            pd.DataFrame，包含日线数据
        
        Example:
            >>> df = client.get_daily(symbols=["000001"], start_date="2024-01-01", adjust="qfq")
        """
        return self._daily_reader.get_daily(
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            adjust=adjust,
            fields=fields
        )
    
    def get_mins(
        self,
        symbols: Union[str, List[str]] = None,
        start_date: str = None,
        end_date: str = None,
        freq: str = "5min",
        adjust: str = None,
        fields: List[str] = None
    ) -> pd.DataFrame:
        """
        获取股票分钟线数据
        
        Args:
            symbols: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            freq: 数据频率，支持 "1min", "5min", "15min", "30min", "60min"
            adjust: 复权类型（同 get_daily）
            fields: 返回字段列表
        
        Returns:
            pd.DataFrame，包含分钟线数据
        """
        return self._daily_reader.get_mins(
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            freq=freq,
            adjust=adjust,
            fields=fields
        )
    
    def get_finance(
        self,
        symbols: Union[str, List[str]] = None,
        end_date: str = None,
        report_type: str = None,
        fields: List[str] = None
    ) -> pd.DataFrame:
        """
        获取股票财务数据
        
        Args:
            symbols: 股票代码
            end_date: 报告期，格式 "YYYY-MM-DD"（如 "2024-09-30"）
            report_type: 报告类型（可选）
            fields: 返回字段列表
        
        Returns:
            pd.DataFrame，包含财务数据
        """
        return self._finance_reader.get_finance(
            symbols=symbols,
            end_date=end_date,
            report_type=report_type,
            fields=fields
        )
    
    # ========================================
    # DIM 层数据接口
    # ========================================
    
    def get_stock_basic(
        self,
        symbols: Union[str, List[str]] = None,
        list_status: str = None,
        exchange: str = None,
        market: str = None,
        fields: List[str] = None
    ) -> pd.DataFrame:
        """
        获取股票基础信息
        
        Args:
            symbols: 股票代码（可选）
            list_status: 上市状态，"L"上市/"D"退市/"P"暂停
            exchange: 交易所，"SZ"/"SH"/"BJ"
            market: 市场类型，"主板"/"创业板"/"科创板"/"北交所"
            fields: 返回字段列表
        
        Returns:
            pd.DataFrame，包含股票基础信息
        """
        return self._dim_reader.get_stock_basic(
            symbols=symbols,
            list_status=list_status,
            exchange=exchange,
            market=market,
            fields=fields
        )
    
    def get_trade_cal(
        self,
        start_date: str = None,
        end_date: str = None,
        exchange: str = "SSE",
        is_open: int = None
    ) -> pd.DataFrame:
        """
        获取交易日历
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            exchange: 交易所，"SSE"上交所/"SZSE"深交所/"BSE"北交所
            is_open: 是否交易日，0休市/1交易/None全部
        
        Returns:
            pd.DataFrame，包含交易日历
        """
        return self._dim_reader.get_trade_cal(
            start_date=start_date,
            end_date=end_date,
            exchange=exchange,
            is_open=is_open
        )
    
    def get_industry(self, src: str = None) -> pd.DataFrame:
        """
        获取行业分类
        
        Args:
            src: 分类来源（可选）
        
        Returns:
            pd.DataFrame，包含行业分类信息
        """
        return self._dim_reader.get_industry(src=src)
    
    # ========================================
    # 便捷方法
    # ========================================
    
    def get_trade_dates(
        self,
        start_date: str,
        end_date: str,
        exchange: str = "SSE"
    ) -> List[str]:
        """
        获取指定范围内的交易日列表
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            exchange: 交易所
        
        Returns:
            交易日列表，格式 ["2024-01-02", "2024-01-03", ...]
        """
        df = self.get_trade_cal(
            start_date=start_date,
            end_date=end_date,
            exchange=exchange,
            is_open=1
        )
        if df.empty:
            return []
        return df['cal_date'].dt.strftime('%Y-%m-%d').tolist()
    
    def get_all_symbols(self, list_status: str = "L") -> List[str]:
        """
        获取全部股票代码
        
        Args:
            list_status: 上市状态，默认 "L" 在市股票
        
        Returns:
            股票代码列表，如 ["000001", "000002", ...]
        """
        df = self.get_stock_basic(list_status=list_status, fields=["symbol"])
        if df.empty:
            return []
        return df['symbol'].tolist()
