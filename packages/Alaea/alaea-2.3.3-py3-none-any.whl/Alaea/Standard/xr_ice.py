#!/Users/christmas/opt/anaconda3/bin/python3
# -*- coding: utf-8 -*-
#  日期 : 2025/10/23 16:59
#  作者 : Christmas
#  邮箱 : 273519355@qq.com
#  项目 : Project
#  版本 : python 3
#  摘要 :
"""

"""
from datetime import datetime
from typing import List, Union

import numpy as np
import pandas as pd
import xarray as xr

from .. import Ttime
from .xr_attrs import (add_ice_attrs, add_lat_attrs, add_lon_attrs,
                       add_time_attrs, add_TIME_attrs, fixed_encoding)


def xr_ice_dateset(_lon: np.ndarray,
                   _lat: np.ndarray,
                   _time: Union[List, str, np.ndarray, datetime, np.datetime64, pd.Timestamp],
                   **kwargs):
    """
    生成海冰数据的xarray.Dataset
    :param _lon: 经度
    :param _lat: 纬度
    :param _time: 时间
    :param kwargs: aice, tive
                    engine, dtype, complevel, zlib, shuffle, fletcher32, contiguous,
                    product_name, source, start
        aice: sea ice concentration (%) 海冰密集度
        tice: sea ice thickness (m) 海冰厚度
        engine: h5netcdf(default), netcdf4, scipy
        dtype: float32(default), float64
        complevel: 4(default) 0-9
        zlib: True(default)
        shuffle: True(default)
        fletcher32: True(default)
        contiguous: True(default)
        product_name: None(default) 产品名称
        source: Alaea(default) 数据来源
        start: None(default) 数据起始时间
    :return: xarray.Dataset
    """
    program_version = 'V1.0'
    history = 'Created by Python' + ' at ' + datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if _time[0].__class__ == str:
        Ttimes = Ttime(TIME=_time)
    elif _time[0].__class__ == datetime or _time[0].__class__ == np.datetime64 or _time[0].__class__ == pd.Timestamp:
        Ttimes = Ttime(Times=_time)
    else:
        raise ValueError(_time[0].__class__)
    
    xr_ice = xr.Dataset(
        data_vars={
            "TIME": ("time", Ttimes.TIME)},
        coords={
            "longitude": _lon,
            "latitude": _lat,
            "time": Ttimes.time,
        },
        attrs={
            "product_name": kwargs.get('product_name', 'None'),
            "source": kwargs.get('source', 'Alaea'),
            "start": kwargs.get('start', 'None'),
            "history": history,
            "program_version": program_version,
        }
    )
    xr_ice = add_lon_attrs(xr_ice, lon_name='longitude')
    xr_ice = add_lat_attrs(xr_ice, lat_name='latitude')
    xr_ice = add_time_attrs(xr_ice, time_name='time')
    xr_ice = add_TIME_attrs(xr_ice, TIME_name='TIME', dim_name='DateStr')
    
    if 'aice' in kwargs:
        _aice = kwargs.get('aice')
        xr_ice['aice'] = (("time", "latitude", "longitude"), _aice)
    
    if 'tice' in kwargs:
        _tice = kwargs.get('tice')
        xr_ice['tice'] = (("time", "latitude", "longitude"), _tice)

    xr_ice = add_ice_attrs(xr_ice)
    
    # 去掉上面用过的key
    for key in ['aice', 'tice',
                'product_name', 'source', 'start']:
        if key in kwargs:
            kwargs.pop(key)
    xr_ice = fixed_encoding(xr_ice, **kwargs)
    
    # 排序
    ordered_vars = ['longitude', 'latitude', 'time', 'TIME',
                    'aice', 'tice']
    existing_vars = [var for var in ordered_vars if var in xr_ice.variables]
    xr_ice = xr_ice[existing_vars]
    
    return xr_ice
