import pandas as pd
from k2pipe.features.feature_utils import (
    series_current,
    series_smooth,
    series_sen_slope,
    series_linear_slope,
    series_diff,
    series_bias,
    series_strict_trend,
    series_soft_trend, series_max, series_min, series_dmax, series_dmin, series_count, series_q05, series_q95,
    series_median,
    series_mean
)

pd.Series.series_current = series_current
pd.Series.series_smooth = series_smooth
pd.Series.series_sen_slope = series_sen_slope
pd.Series.series_linear_slope = series_linear_slope
pd.Series.series_diff = series_diff
pd.Series.series_bias = series_bias
pd.Series.series_strict_trend = series_strict_trend
pd.Series.series_soft_trend = series_soft_trend
pd.Series.series_max = series_max
pd.Series.series_min = series_min
pd.Series.series_dmax = series_dmax
pd.Series.series_dmin = series_dmin
pd.Series.series_count = series_count
pd.Series.series_q05 = series_q05
pd.Series.series_q95 = series_q95
pd.Series.series_median = series_median
pd.Series.series_mean = series_mean

print('K2Pipe feature functions loaded')
