# -*- coding: utf-8 -*-
"""
财务数据读取器

从 StarRocks DWD 层读取 stock_finance 表。
"""
import pandas as pd
from typing import List, Dict, Optional, Union
from loguru import logger
import pymysql
from dbutils.persistent_db import PersistentDB


class FinanceReader:
    """
    财务数据读取器
    
    从 DWD 层读取 stock_finance 表（财务宽表）。
    """
    
    # 默认返回字段
    DEFAULT_FIELDS = [
        "ann_date", "symbol", "exchange", "end_date", "report_type",
        # 利润表
        "revenue", "n_income", "n_income_attr_p", "basic_eps",
        # 资产负债表
        "total_assets", "total_liab", "total_hldr_eqy",
        # 现金流量表
        "n_cashflow_act",
        # 财务指标
        "roe", "roa", "grossprofit_margin", "netprofit_margin",
        "revenue_yoy", "profit_yoy", "current_ratio", "debt_to_assets", "bps"
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
    
    def get_finance(
        self,
        symbols: Union[str, List[str]] = None,
        end_date: str = None,
        report_type: str = None,
        fields: List[str] = None
    ) -> pd.DataFrame:
        """
        获取财务数据
        
        Args:
            symbols: 股票代码
            end_date: 报告期，格式 "YYYY-MM-DD"
            report_type: 报告类型
            fields: 返回字段列表
        
        Returns:
            pd.DataFrame，包含财务数据
        """
        symbols = self._normalize_symbols(symbols)
        fields = fields or self.DEFAULT_FIELDS
        
        # 构建 SQL
        field_str = ", ".join(fields)
        conditions = ["1=1"]
        
        if symbols:
            symbol_list = ", ".join([f"'{s}'" for s in symbols])
            conditions.append(f"symbol IN ({symbol_list})")
        if end_date:
            conditions.append(f"end_date = '{end_date}'")
        if report_type:
            conditions.append(f"report_type = '{report_type}'")
        
        where_clause = " AND ".join(conditions)
        
        sql = f"""
        SELECT {field_str}
        FROM stock_finance
        WHERE {where_clause}
        ORDER BY symbol, end_date DESC, ann_date DESC
        """
        
        logger.debug(f"查询财务数据: symbols={symbols}, end_date={end_date}")
        result = self._query(sql, db="dwd")
        
        if not result:
            return pd.DataFrame()
        
        df = pd.DataFrame(result)
        
        # 转换日期列
        for col in ['ann_date', 'end_date']:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col])
        
        return df
    
    def get_latest_finance(
        self,
        symbols: Union[str, List[str]] = None,
        fields: List[str] = None
    ) -> pd.DataFrame:
        """
        获取最新一期财务数据
        
        每只股票只返回最新公告的一条记录。
        
        Args:
            symbols: 股票代码
            fields: 返回字段列表
        
        Returns:
            pd.DataFrame
        """
        symbols = self._normalize_symbols(symbols)
        fields = fields or self.DEFAULT_FIELDS
        
        field_str = ", ".join(fields)
        conditions = []
        
        if symbols:
            symbol_list = ", ".join([f"'{s}'" for s in symbols])
            conditions.append(f"symbol IN ({symbol_list})")
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        # 使用窗口函数获取每只股票最新一期
        sql = f"""
        SELECT {field_str}
        FROM (
            SELECT *,
                   ROW_NUMBER() OVER (PARTITION BY symbol, exchange ORDER BY ann_date DESC) as rn
            FROM stock_finance
            WHERE {where_clause}
        ) t
        WHERE rn = 1
        ORDER BY symbol
        """
        
        logger.debug(f"查询最新财务数据: symbols={symbols}")
        result = self._query(sql, db="dwd")
        
        if not result:
            return pd.DataFrame()
        
        df = pd.DataFrame(result)
        
        # 移除辅助列
        if 'rn' in df.columns:
            df = df.drop(columns=['rn'])
        
        # 转换日期列
        for col in ['ann_date', 'end_date']:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col])
        
        return df
