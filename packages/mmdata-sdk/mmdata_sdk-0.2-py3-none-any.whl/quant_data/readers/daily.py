# -*- coding: utf-8 -*-
"""
日线/分钟线数据读取器

支持从 StarRocks DWD 层读取行情数据，并提供复权计算。
"""
import pandas as pd
from typing import List, Dict, Optional, Union
from loguru import logger
import pymysql
from dbutils.persistent_db import PersistentDB


class DailyReader:
    """
    日线/分钟线数据读取器
    
    从 DWD 层读取 stock_daily 和 stock_mins_* 表。
    """
    
    # 日线默认返回字段
    DEFAULT_DAILY_FIELDS = [
        "trade_date", "symbol", "exchange", "ts_code",
        "open", "high", "low", "close", "pre_close",
        "vol", "amount", "adj_factor", "pct_chg",
        "turnover_rate", "turnover_rate_f",
        "pe_ttm", "pb", "total_mv", "circ_mv",
        "trade_status", "is_st"
    ]
    
    # 分钟线默认返回字段
    DEFAULT_MINS_FIELDS = [
        "trade_time", "symbol", "exchange",
        "open", "high", "low", "close",
        "vol", "amount", "adj_factor"
    ]
    
    # 分钟线频率映射到表名
    FREQ_TABLE_MAP = {
        "1min": "stock_mins_1min",
        "5min": "stock_mins_5min",
        "15min": "stock_mins_15min",
        "30min": "stock_mins_30min",
        "60min": "stock_mins_60min",
    }
    
    def __init__(self, conn_params: Dict):
        """
        初始化读取器
        
        Args:
            conn_params: 数据库连接参数 {host, port, user, passwd}
        """
        self._conn_params = conn_params
        self._pool = None
    
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
    
    def _query(self, sql: str, db: str = "dwd") -> List[Dict]:
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
    
    def get_daily(
        self,
        symbols: Union[str, List[str]] = None,
        start_date: str = None,
        end_date: str = None,
        adjust: str = None,
        fields: List[str] = None
    ) -> pd.DataFrame:
        """
        获取日线数据
        
        Args:
            symbols: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            adjust: 复权类型 (None/qfq/hfq)
            fields: 返回字段列表
        
        Returns:
            pd.DataFrame
        """
        symbols = self._normalize_symbols(symbols)
        fields = fields or self.DEFAULT_DAILY_FIELDS
        
        # 确保复权计算需要的字段存在
        required_for_adjust = ["open", "high", "low", "close", "pre_close", "adj_factor"]
        if adjust:
            for f in required_for_adjust:
                if f not in fields:
                    fields.append(f)
        
        # 构建 SQL
        field_str = ", ".join(fields)
        conditions = ["1=1"]
        
        if symbols:
            symbol_list = ", ".join([f"'{s}'" for s in symbols])
            conditions.append(f"symbol IN ({symbol_list})")
        if start_date:
            conditions.append(f"trade_date >= '{start_date}'")
        if end_date:
            conditions.append(f"trade_date <= '{end_date}'")
        
        where_clause = " AND ".join(conditions)
        
        sql = f"""
        SELECT {field_str}
        FROM stock_daily
        WHERE {where_clause}
        ORDER BY symbol, trade_date
        """
        
        logger.debug(f"查询日线数据: symbols={symbols}, 日期={start_date}~{end_date}")
        result = self._query(sql, db="dwd")
        
        if not result:
            return pd.DataFrame()
        
        df = pd.DataFrame(result)
        df['trade_date'] = pd.to_datetime(df['trade_date'])
        
        # 转换数值列为 float（StarRocks 返回 decimal.Decimal 类型）
        numeric_cols = ['open', 'high', 'low', 'close', 'pre_close', 'vol', 'amount',
                        'adj_factor', 'pct_chg', 'turnover_rate', 'turnover_rate_f',
                        'pe_ttm', 'pb', 'total_mv', 'circ_mv']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # 复权处理
        if adjust:
            df = self._apply_adjust(df, adjust)
        
        return df
    
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
        获取分钟线数据
        
        Args:
            symbols: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            freq: 频率 (1min/5min/15min/30min/60min)
            adjust: 复权类型
            fields: 返回字段列表
        
        Returns:
            pd.DataFrame
        """
        symbols = self._normalize_symbols(symbols)
        fields = fields or self.DEFAULT_MINS_FIELDS
        
        # 获取表名
        table_name = self.FREQ_TABLE_MAP.get(freq)
        if not table_name:
            raise ValueError(f"不支持的频率: {freq}，支持: {list(self.FREQ_TABLE_MAP.keys())}")
        
        # 确保复权计算需要的字段存在
        required_for_adjust = ["open", "high", "low", "close", "adj_factor"]
        if adjust:
            for f in required_for_adjust:
                if f not in fields:
                    fields.append(f)
        
        # 构建 SQL
        field_str = ", ".join(fields)
        conditions = ["1=1"]
        
        if symbols:
            symbol_list = ", ".join([f"'{s}'" for s in symbols])
            conditions.append(f"symbol IN ({symbol_list})")
        if start_date:
            conditions.append(f"trade_date >= '{start_date}'")
        if end_date:
            conditions.append(f"trade_date <= '{end_date}'")
        
        where_clause = " AND ".join(conditions)
        
        sql = f"""
        SELECT {field_str}
        FROM {table_name}
        WHERE {where_clause}
        ORDER BY symbol, trade_time
        """
        
        logger.debug(f"查询分钟线数据: symbols={symbols}, freq={freq}")
        result = self._query(sql, db="dwd")
        
        if not result:
            return pd.DataFrame()
        
        df = pd.DataFrame(result)
        if 'trade_time' in df.columns:
            df['trade_time'] = pd.to_datetime(df['trade_time'])
        
        # 转换数值列为 float（StarRocks 返回 decimal.Decimal 类型）
        numeric_cols = ['open', 'high', 'low', 'close', 'vol', 'amount', 'adj_factor']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # 复权处理
        if adjust:
            df = self._apply_adjust(df, adjust, time_col='trade_time')
        
        return df
    
    def _apply_adjust(
        self,
        df: pd.DataFrame,
        adjust: str,
        time_col: str = 'trade_date'
    ) -> pd.DataFrame:
        """
        应用复权计算
        
        Args:
            df: 原始数据
            adjust: 复权类型 (qfq/hfq)
            time_col: 时间列名
        
        Returns:
            复权后的 DataFrame
        """
        if df.empty or 'adj_factor' not in df.columns:
            return df
        
        price_cols = ['open', 'high', 'low', 'close']
        if 'pre_close' in df.columns:
            price_cols.append('pre_close')
        
        if adjust == "qfq":
            # 前复权: 价格 * 复权因子 / 最新复权因子
            # 以每只股票最新的复权因子为基准
            for symbol in df['symbol'].unique():
                mask = df['symbol'] == symbol
                sub_df = df.loc[mask]
                
                if sub_df['adj_factor'].notna().any():
                    # 获取最新的复权因子
                    latest_idx = sub_df[time_col].idxmax()
                    latest_factor = sub_df.loc[latest_idx, 'adj_factor']
                    
                    if latest_factor and latest_factor > 0:
                        for col in price_cols:
                            if col in df.columns:
                                df.loc[mask, col] = (
                                    df.loc[mask, col] * df.loc[mask, 'adj_factor'] / latest_factor
                                ).round(4)
        
        elif adjust == "hfq":
            # 后复权: 价格 * 复权因子
            # 以上市首日复权因子（通常为1）为基准
            for col in price_cols:
                if col in df.columns:
                    df[col] = (df[col] * df['adj_factor']).round(4)
        
        return df
