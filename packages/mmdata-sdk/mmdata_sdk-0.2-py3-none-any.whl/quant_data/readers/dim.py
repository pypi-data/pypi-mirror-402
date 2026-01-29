# -*- coding: utf-8 -*-
"""
维度数据读取器

从 StarRocks DIM 层读取 stock_basic、trade_cal、industry 表。
"""
import pandas as pd
from typing import List, Dict, Optional, Union
from loguru import logger
import pymysql
from dbutils.persistent_db import PersistentDB


class DimReader:
    """
    维度数据读取器
    
    从 DIM 层读取股票基础信息、交易日历等维度表。
    """
    
    # stock_basic 默认字段
    DEFAULT_STOCK_BASIC_FIELDS = [
        "symbol", "exchange", "ts_code", "name",
        "area", "industry", "market",
        "list_date", "delist_date", "list_status",
        "is_hs", "is_st"
    ]
    
    # trade_cal 默认字段
    DEFAULT_TRADE_CAL_FIELDS = [
        "cal_date", "exchange", "is_open",
        "pre_trade_date", "next_trade_date",
        "is_month_end", "is_quarter_end", "is_year_end"
    ]
    
    def __init__(self, conn_params: Dict):
        """
        初始化读取器
        
        Args:
            conn_params: 数据库连接参数
        """
        self._conn_params = conn_params
    
    def _get_pool(self, db: str) -> PersistentDB:
        """获取连接池"""
        return PersistentDB(
            creator=pymysql,
            maxusage=None,
            ping=1,
            host=self._conn_params["host"],
            port=self._conn_params["port"],
            user=self._conn_params["user"],
            passwd=self._conn_params["passwd"],
            db=db,
            cursorclass=pymysql.cursors.DictCursor,
            connect_timeout=10,
            charset='utf8mb4'
        )
    
    def _query(self, sql: str, db: str = "dim") -> List[Dict]:
        """执行 SQL 查询"""
        pool = self._get_pool(db)
        conn = pool.connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                return cursor.fetchall()
        finally:
            conn.close()
    
    def _normalize_symbols(self, symbols: Union[str, List[str], None]) -> Optional[List[str]]:
        """标准化股票代码"""
        if symbols is None:
            return None
        if isinstance(symbols, str):
            return [symbols]
        return list(symbols)
    
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
            symbols: 股票代码
            list_status: 上市状态 (L/D/P)
            exchange: 交易所 (SZ/SH/BJ)
            market: 市场类型
            fields: 返回字段列表
        
        Returns:
            pd.DataFrame
        """
        symbols = self._normalize_symbols(symbols)
        fields = fields or self.DEFAULT_STOCK_BASIC_FIELDS
        
        field_str = ", ".join(fields)
        conditions = ["1=1"]
        
        if symbols:
            symbol_list = ", ".join([f"'{s}'" for s in symbols])
            conditions.append(f"symbol IN ({symbol_list})")
        if list_status:
            conditions.append(f"list_status = '{list_status}'")
        if exchange:
            conditions.append(f"exchange = '{exchange}'")
        if market:
            conditions.append(f"market = '{market}'")
        
        where_clause = " AND ".join(conditions)
        
        sql = f"""
        SELECT {field_str}
        FROM stock_basic
        WHERE {where_clause}
        ORDER BY symbol
        """
        
        logger.debug(f"查询股票基础信息: list_status={list_status}")
        result = self._query(sql, db="dim")
        
        if not result:
            return pd.DataFrame()
        
        df = pd.DataFrame(result)
        
        # 转换日期列
        for col in ['list_date', 'delist_date']:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col])
        
        return df
    
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
            exchange: 交易所
            is_open: 是否交易日 (0/1/None)
        
        Returns:
            pd.DataFrame
        """
        fields = self.DEFAULT_TRADE_CAL_FIELDS
        field_str = ", ".join(fields)
        
        conditions = []
        if exchange:
            conditions.append(f"exchange = '{exchange}'")
        if start_date:
            conditions.append(f"cal_date >= '{start_date}'")
        if end_date:
            conditions.append(f"cal_date <= '{end_date}'")
        if is_open is not None:
            conditions.append(f"is_open = {is_open}")
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        sql = f"""
        SELECT {field_str}
        FROM trade_cal
        WHERE {where_clause}
        ORDER BY cal_date
        """
        
        logger.debug(f"查询交易日历: {start_date}~{end_date}")
        result = self._query(sql, db="dim")
        
        if not result:
            return pd.DataFrame()
        
        df = pd.DataFrame(result)
        
        # 转换日期列
        for col in ['cal_date', 'pre_trade_date', 'next_trade_date']:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col])
        
        return df
    
    def get_industry(self, src: str = None) -> pd.DataFrame:
        """
        获取行业分类
        
        Args:
            src: 分类来源
        
        Returns:
            pd.DataFrame
        """
        conditions = []
        if src:
            conditions.append(f"src = '{src}'")
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        sql = f"""
        SELECT *
        FROM industry
        WHERE {where_clause}
        ORDER BY industry_name
        """
        
        logger.debug(f"查询行业分类: src={src}")
        result = self._query(sql, db="dim")
        
        if not result:
            return pd.DataFrame()
        
        return pd.DataFrame(result)
