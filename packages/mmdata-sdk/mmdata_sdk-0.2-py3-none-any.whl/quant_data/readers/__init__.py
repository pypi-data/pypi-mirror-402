# -*- coding: utf-8 -*-
"""
数据读取器模块
"""
from .daily import DailyReader
from .finance import FinanceReader
from .dim import DimReader

__all__ = ["DailyReader", "FinanceReader", "DimReader"]
