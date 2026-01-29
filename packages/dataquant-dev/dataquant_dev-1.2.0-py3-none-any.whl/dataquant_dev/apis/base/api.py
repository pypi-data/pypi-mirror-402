# -*- coding: utf-8 -*-

__all__ = [
    "init",
    "environ",
    "load_conf",
    "get_data",
    "get_qdata"
]

from dataquant_dev.utils.config import read_config
from dataquant_dev.utils.decorators import retry

global QUOTE_FORMAT


def load_conf():
    global QUOTE_FORMAT
    CONFIG = read_config()['system']
    QUOTE_FORMAT = CONFIG.get('quote_format')


load_conf()


def init(**kwargs):
    """
    :param str username: 用户名，license模式下为'license'
    :param str password: 用户密码，license模式下为下发的license
    :param str protocol：传输协议，默认HTTP
    :param str url: 数据服务的URL
    :param int connect_timeout: 连接建立超时时间,默认5秒
    :param int timeout: 数据传输超时时间，默认30秒
    :param str compressor: 数据传输过程中的压缩算法，默认不使用
    :param int max_pool_size: 连接池大小，默认10
    :param int page_size: 数据请求分页大小，默认100000
    :return:
    """
    from dataquant_dev.utils.client import init as _init

    _init(**kwargs)
    return


def environ():
    """
    获取环境配置信息
    :return:
    """
    from dataquant_dev.utils.client import environ as _environ
    return _environ()


def get_data(method, **kwargs):
    """
    共用获取数据接口
    :param method:    接口名称
    :param kwargs:    接口参数
    """
    from dataquant_dev.utils.client import get_client
    result = get_client().send(method, **kwargs)
    if result['result_code'] == '0' or result['result_code'] == 0:
        return result['data']
    else:
        raise Exception('异常代码[%s], 异常信息[%s]' % (result['result_code'], result['result_msg']))


@retry(3, exp_name=Exception,time_delta=1.0)
def get_qdata(method, **kwargs):
    """
    共用获取行情数据接口
    :param method:    接口名称
    :param kwargs:    接口参数
    """
    from dataquant_dev.utils.client import get_client
    global QUOTE_FORMAT
    kwargs.setdefault('format', QUOTE_FORMAT)  # TabSeparatedWithNames Parquet Arrow
    try:
        ret = get_client().send(method, **kwargs)
        # if ret['data']['scr_num'][0] == '600570.XSHG':
        #     raise (Exception(f"data error"))
    except Exception as ex:
        raise (Exception(f"error={ex}|func={method}|kwargs={str(kwargs)}"))
    return ret
