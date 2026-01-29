import pandas as pd
from k2pipe.features.feature_utils import (
    series_current,
    series_smooth,
    series_sen_slope,
    series_linear_slope,
    series_diff,
    series_bias,
    series_strict_trend,
    series_soft_trend
)

pd.Series.series_current = series_current
pd.Series.series_smooth = series_smooth
pd.Series.series_sen_slope = series_sen_slope
pd.Series.series_linear_slope = series_linear_slope
pd.Series.series_diff = series_diff
pd.Series.series_bias = series_bias
pd.Series.series_strict_trend = series_strict_trend
pd.Series.series_soft_trend = series_soft_trend

print('K2Pipe feature functions loaded')