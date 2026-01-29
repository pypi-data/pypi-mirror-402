# -*- coding: UTF-8 -*-

import time
import gevent
import warnings
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor
from dataquant_dev.utils.config import read_config

from dataquant_dev.utils.datetime_func import get_current_date
from dataquant_dev.apis.quote.api import wait_until_bind,get_exchange_calendar
from dataquant_dev.apis.quote.api import convert_result_data,_async_get_hf_data,quote_single_part

__all__ = [
    # XBond 数据查询接口
    "get_xbond_deal", #XBond逐笔成交数据
    # "get_xbond_deal_partial", #XBond逐笔成交数据(批量)
    "get_xbond_tick", #XBond报价行情快照数据
    # "get_xbond_tick_partial", #XBond报价行情快照数据(批量)
]


# 请求服务端URL，XBond 相关URL
URL_GET_XBOND_DEAL = 'get_xbond_deal'#XBond成交数据
URL_GET_XBOND_TICK = 'get_xbond_tick'#XBond报价行情数据


global CONFIG_PAGE_SIZE, PARALLEL_NUM, PARALLEL_MODE, EXECUTOR, EXECUTOR_INNER, \
    HF_SORT_COLS


def load_conf():
    global CONFIG_PAGE_SIZE, PARALLEL_NUM, PARALLEL_MODE, EXECUTOR, EXECUTOR_INNER, \
        HF_SORT_COLS
    CONFIG = read_config()['system']
    CONFIG_PAGE_SIZE = CONFIG.get('page_size')
    PARALLEL_NUM = CONFIG.get("quote_parallel")
    PARALLEL_MODE = CONFIG.get("parallel_mode")
    if PARALLEL_MODE == 'Thread':
        EXECUTOR = ThreadPoolExecutor(max_workers=PARALLEL_NUM)
        EXECUTOR_INNER = ThreadPoolExecutor(max_workers=PARALLEL_NUM)
    elif PARALLEL_MODE == 'Coroutine':
        from gevent import monkey
        monkey.patch_all()
        from gevent.pool import Pool as gPool
        EXECUTOR = gPool(PARALLEL_NUM)
        EXECUTOR_INNER = gPool(PARALLEL_NUM)
        EXECUTOR.submit = EXECUTOR.spawn
        EXECUTOR_INNER.submit = EXECUTOR_INNER.spawn
    HF_SORT_COLS = {
        'xbond': list(CONFIG.get('quote_hf_ibank_sort').split(',')),
    }



load_conf()
_config = read_config()['system']


KLINE_CODE_GROUP = 10
HF_DAY_DELTA = 1
HF_CODE_GROUP = 1
KLINE_DAY_DELTA = 90

KLINE_DAY_DELTA_CANDLE_PERIOD = {
    '1m', '1',
    '5m', '2',
    '15m', '3',
    '30m', '4',
    '1h', '5',
    '1d', '6',
    # '1w': '7',
    # '1M': '8',
    # '1y': '9',
    '2h', '11',
    '3h', '12',
    '4h', '13',
    '10m', '14'
}


CANDLE_PERIOD_MAP = {
    '1m': '1',
    '5m': '2',
    '15m': '3',
    '30m': '4',
    '1h': '5',
    '1d': '6',
    '1w': '7',
    '1M': '8',
    '1y': '9',
    '2h': '11',
    '3h': '12',
    '4h': '13',
    '10m': '14'
}


CANDLE_MODE_MAP = {
    None: '0',
    'pre': '1',
    'post': '2'
}

#20250106 新增银行间债券查询api
@wait_until_bind()
def get_xbond_deal(symbols, start_time:str=None, end_time:str=None,category:str=None,type:str=None, cols=None, rslt_type=0):
    """
    获取XBond逐笔成交数据
    对应表：ck_ibank_xbond_deal.sql (xbond_deal)
    """
    if symbols is None:
        warnings.warn("函数[get_xbond_deal]的参数(symbols)为必填项")
        return None

    if isinstance(symbols, str):
        symbol_list = symbols.split(',')
    else:
        symbol_list = symbols

    start_time,end_time = get_default_time(start_time, end_time)

    xbond_result = None
    if len(symbol_list) > 0:
        xbond_result = get_xbond_deal_partial(symbol_list, start_time, end_time, cols, rslt_type)
        # xbond_result = _async_get_hf_data(
        #     get_xbond_deal_partial, symbol_list, start_time, end_time,
        #     cols, 'ibank',code_name='symbols'
        # )

    final_result = xbond_result
    # concat_list = []
    # if xbond_result is not None:
    #     concat_list.append(xbond_result)
    #
    # if len(concat_list) > 1:
    #     final_result = pd.concat(
    #         concat_list,
    #         axis=0, sort=False, ignore_index=True
    #     )
    # elif len(concat_list) == 1:
    #     final_result = concat_list[0]

    final_result = convert_result_data(final_result, rslt_type)

    return final_result


def get_default_time(start_time,end_time):
    day_end_time = '235959'
    day_start_time = '000000'
    current_date = get_current_date()
    if start_time is None and end_time is None:
        df = get_exchange_calendar('IB', end_date=current_date, trdy_flag=1)
        if df.shape[0] > 2:
            trade_date = df['busi_date'].tolist()[-2]
        else:
            trade_date = current_date
        start_time = trade_date + day_start_time
        end_time = trade_date + day_end_time
    elif start_time is None:
        if len(end_time) == 8:
            end_time = end_time + day_end_time
        end_date = end_time[: 8]
        start_time = end_date + day_start_time
    elif end_time is None:
        if len(start_time) == 8:
            start_time = start_time + day_start_time
        start_date = start_time[: 8]
        end_time = start_date + day_end_time
    return start_time,end_time


def get_xbond_deal_partial(symbols, strt_time=None, end_time=None, cols=None, rslt_type=0):
    """
    批量获取XBond逐笔成交数据
    对应表：ck_ibank_xbond_deal.sql (xbond_deal)
    """

    int_param = [
        'total_num', 'page_num', 'total_pages',
        'settle_type', 'pre_publish_bond', 'last_side', 'last_method',
        'total_volume', 'std_total_volume',
        'listenerType', 'is_stale'
    ]
    float_param = [
        'preclose_clean_price', 'preclose_yield', 'pre_weighted_clean_price', 'pre_weighted_yield',
        'last', 'open', 'high', 'low', 'weighted_clean_price', 'last_yield', 'open_yield', 
        'high_yield', 'low_yield', 'weighted_yield', 'change_yield', 'price_limit'
    ]
    if cols:
        fix_cols = \
            ['symbol', 'date_time', 'arrive_time']
        if isinstance(cols, str):
            cols = cols.split(',')
        tmp_cols = fix_cols + cols
        cols = list(set(tmp_cols))
        cols.sort(key=tmp_cols.index)

        int_param = list(set(int_param).intersection(set(cols)))
        float_param = list(set(float_param).intersection(set(cols)))

        if isinstance(cols, list):
            cols = ','.join(cols)

    if symbols:
        params = {
            "symbols": ",".join(symbols),
            "strt_time": strt_time,
            "end_time": end_time,
            "cols": cols,
            "page_num": 1,
            "page_size": CONFIG_PAGE_SIZE,
            "rslt_type": rslt_type,
            "api_type": "quote",
            "int_param": int_param,
            "float_param": float_param
        }
        quote_data =None
        try:
            quote_data = quote_single_part(URL_GET_XBOND_DEAL, params)['data']
        except Exception as ex:
            warn_str = "获取数据异常，异常函数[%s]" % URL_GET_XBOND_DEAL
            warnings.warn(warn_str)
        return quote_data

    else:
        warnings.warn("函数[get_xbond_deal_partial]的参数(symbols)为必填项")
        return None


@wait_until_bind()
def get_xbond_tick(symbols, start_time:str=None, end_time:str=None,category:str=None,type:str=None, cols=None, rslt_type=0):
    """
    获取XBond报价行情快照数据
    对应表：ck_ibank_xbond_snapshot.sql (xbond_snapshot)
    """
    if symbols is None:
        warnings.warn("函数[get_xbond_tick]的参数(symbols)为必填项")
        return None

    if isinstance(symbols, str):
        symbol_list = symbols.split(',')
    else:
        symbol_list = symbols

    start_time,end_time = get_default_time(start_time, end_time)

    xbond_result = None
    if len(symbol_list) > 0:
        xbond_result = get_xbond_tick_partial(symbol_list, start_time, end_time,cols,rslt_type)
        # xbond_result = _async_get_hf_data(
        #     get_xbond_tick_partial, symbol_list, start_time, end_time,
        #     cols, 'ibank',code_name='symbols'
        # )

    final_result = xbond_result
    # concat_list = []
    # if xbond_result is not None:
    #     concat_list.append(xbond_result)
    #
    # if len(concat_list) > 1:
    #     final_result = pd.concat(
    #         concat_list,
    #         axis=0, sort=False, ignore_index=True
    #     )
    # elif len(concat_list) == 1:
    #     final_result = concat_list[0]

    final_result = convert_result_data(final_result, rslt_type)

    return final_result


def get_xbond_tick_partial(symbols, strt_time=None, end_time=None, cols=None, rslt_type=0):
    """
    批量获取XBond报价行情快照数据
    对应表：ck_ibank_xbond_snapshot.sql (xbond_snapshot)
    """

    int_param = [
        'total_num', 'page_num', 'total_pages',
        'category', 'book_type', 'settle_type',
        'listenerType', 'is_sanity', 'is_stale', 'is_spike'
    ]
    float_param = [
        'bid_size0', 'std_bid_size0', 'bid_clean_price0', 'bid_yield0', 'bid_unmatch_qty0',
        'bid_size1', 'std_bid_size1', 'bid_clean_price1', 'bid_yield1', 'bid_unmatch_qty1',
        'bid_size2', 'std_bid_size2', 'bid_clean_price2', 'bid_yield2', 'bid_unmatch_qty2',
        'bid_size3', 'std_bid_size3', 'bid_clean_price3', 'bid_yield3', 'bid_unmatch_qty3',
        'bid_size4', 'std_bid_size4', 'bid_clean_price4', 'bid_yield4', 'bid_unmatch_qty4',
        'bid_size5', 'std_bid_size5', 'bid_clean_price5', 'bid_yield5', 'bid_unmatch_qty5',
        'offer_size0', 'std_offer_size0', 'offer_clean_price0', 'offer_yield0', 'offer_unmatch_qty0',
        'offer_size1', 'std_offer_size1', 'offer_clean_price1', 'offer_yield1', 'offer_unmatch_qty1',
        'offer_size2', 'std_offer_size2', 'offer_clean_price2', 'offer_yield2', 'offer_unmatch_qty2',
        'offer_size3', 'std_offer_size3', 'offer_clean_price3', 'offer_yield3', 'offer_unmatch_qty3',
        'offer_size4', 'std_offer_size4', 'offer_clean_price4', 'offer_yield4', 'offer_unmatch_qty4',
        'offer_size5', 'std_offer_size5', 'offer_clean_price5', 'offer_yield5', 'offer_unmatch_qty5'
    ]
    if cols:
        fix_cols = \
            ['symbol', 'date_time', 'arrive_time']
        if isinstance(cols, str):
            cols = cols.split(',')
        tmp_cols = fix_cols + cols
        cols = list(set(tmp_cols))
        cols.sort(key=tmp_cols.index)

        int_param = list(set(int_param).intersection(set(cols)))
        float_param = list(set(float_param).intersection(set(cols)))

        if isinstance(cols, list):
            cols = ','.join(cols)

    if symbols:
        params = {
            "symbols": ",".join(symbols),
            "strt_time": strt_time,
            "end_time": end_time,
            "cols": cols,
            "page_num": 1,
            "page_size": CONFIG_PAGE_SIZE,
            "rslt_type": rslt_type,
            "api_type": "quote",
            "int_param": int_param,
            "float_param": float_param
        }

        quote_data =None
        try:
            quote_data = quote_single_part(URL_GET_XBOND_TICK, params)['data']
        except Exception as ex:
            warn_str = "获取数据异常，异常函数[%s]" % URL_GET_XBOND_TICK
            warnings.warn(warn_str)
        return quote_data

    else:
        warnings.warn("函数[get_xbond_tick_partial]的参数(symbols)为必填项")
        return None

