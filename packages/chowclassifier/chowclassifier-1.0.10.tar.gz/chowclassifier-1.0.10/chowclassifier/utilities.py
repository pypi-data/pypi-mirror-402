import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import colormaps
import seaborn as sns
from typing import Union
from datetime import datetime

TREND_COLORS = ["#4d4c49", "#d85e5e", "#3a668c", "#000000"]# constant, increasing,decreasing 
CI_COLORS = ["#fef5da", "#ff988c", "#b4c5f4", "#474747"]
SCATTERPARAMS = {"marker": 'o', "linewidths":0.5, "alpha":1,"s":50,"label":'_nolegend_'}
FILLPARAMS = {"linestyle":"None", "alpha":0.3,"label":'_nolegend_'}
FITPARAMS = {"label":'_nolegend_'}

def parse_cmap(cmap):
    """
    Parse and normalize colormap to dictionary format.
    
    Converts string colormap names, lists, or dictionaries to a standardized
    dictionary format with integer keys.
    
    :param cmap: Colormap as string name, list of colors, or dictionary
    :return: Dictionary mapping integers to color values
    """
    if isinstance(cmap,str):
        cmap = {i:x for i,x in enumerate(colormaps[cmap].colors)}
    elif isinstance(cmap,list):
        cmap = {i:x for i,x in enumerate(cmap)}
    elif isinstance(cmap, dict):
        if not all(isinstance(item, int) for item in cmap.keys()):
            cmap.update({i:v for i,(k,v) in enumerate(cmap.items())})
    else:
        cmap = {i:x for i,x in enumerate(colormaps['Set1'].colors)}
    return cmap

def conf_int_to_trend(ci:Union[pd.DataFrame,list], param:str='X'):
    """
    Convert confidence interval to trend classification.
    
    Returns trend code 0, 1, or 2 from the confidence interval:

    - if ci crosses 0, then returns 0 (non-significant)
    - if ci is completely below 0, then returns 2 (decreasing)
    - else returns 1 (increasing)
    
    :param ci: Confidence interval to process, either a tuple (length 2), a DataFrame, or result from conf_int given by statsmodels
    :param param: Column name to use if a DataFrame was given as ci
    :return: Integer trend code (0, 1, or 2)
    """
    if isinstance(ci, list) and len(ci)==2:
        l,u = ci
    else:
        l,u=ci.loc[param,:]
    if u<0:
        return 2 # significantly decreasing (at tested level)
    elif l>0:
        return 1 # significantly increasing (at tested level)
    else:
        return 0 # non significant (at tested level)

def infer_date_format(s_date:str):
    """
    Infer date format from a sample date string.

    :param s_date: Sample date string to infer format from
    :return: Date format string if successfully inferred, None otherwise
    """
    date_patterns = ["%d-%m-%Y","%d-%m-%Y %H:%M:%S",
                     "%Y-%m-%d","%Y-%m-%d %H:%M:%S",
                     "%y-%m-%d","%y-%m-%d %H:%M:%S",
                     "%d %b %y","%d %b %y %H:%M:%S",
                     "%d %b %Y","%d %b %Y %H:%M:%S",
                     ]

    for pattern in date_patterns:
        try:
            datetime.strptime(s_date, pattern).date()
        except:
            pass
        else:
            return pattern

def guess_timelapse_type(series:Union[list,pd.DataFrame,pd.Series], date_format:str = "%Y-%m-%d"):
    """
    Guess the time lapse unit in a time series and re-index it.
    
    Analyzes datetime differences to determine whether data is indexed by
    seconds, minutes, hours, days, or years.

    :param series: Time series data (list, DataFrame, or Series)
    :param date_format: Format string for parsing datetime values
    :return: Tuple of (indexed series, datetype string)
    """
    try:
        series = pd.to_datetime(series, format = date_format)
    except:
        pass
    start = min(series)
    series = series-start # reindex timecol from lowest one
    if all([i.seconds==0 for i in series]):
        #check if indexed by minutes
        if all([i.seconds%60 == 0 for i in series]):
            #check if indexed by hour
            if all([i.seconds%3600 == 0 for i in series]):
                #check if indexed by year
                if all([i.days%365==0 or i.days%366==0 for i in series]):
                    #index by year
                    series = [int(i.days/365) for i in series]
                    datetype = 'year'
                else:#index by day
                    series = [i.days for i in series]
                    datetype = 'day'
            else:#index by hour
                series = [i.days * 24 + i.hours for i in series]
                datetype = 'hour'
        else:#index by minute
            series = [i.days * 60 * 24 + i.minutes for i in series]
            datetype = 'minute'
    else:# index on the seconds:
        series = [i.days * 3600 * 24 + i.seconds for i in series]
        datetype = 'second'
    return series,datetype