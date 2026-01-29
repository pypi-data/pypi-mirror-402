# -*- coding: utf-8 -*-
"""
Quant Data SDK

为量化研究员提供便捷的数据查询接口，支持：
- DWD 层日线/分钟线/财务数据查询
- DIM 层维度数据查询
- 自动前复权/后复权计算

使用示例:
    from quant_data import QuantDataClient
    
    client = QuantDataClient(
        host="",
        port=9030,
        user="",
        password=""
    )
    
    # 获取日线数据（前复权）
    df = client.get_daily(
        symbols=["000001", "600519"],
        start_date="2024-01-01",
        adjust="qfq"
    )
"""
from .client import QuantDataClient

__version__ = "0.2"
__all__ = ["QuantDataClient"]
