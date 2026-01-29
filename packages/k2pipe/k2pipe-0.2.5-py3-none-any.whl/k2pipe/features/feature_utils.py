import pandas as pd
import numpy as np
from loguru import logger
from typing import Tuple


def series_current(self: pd.Series) -> pd.Series:
    """当前值（前向填充）"""
    return self.sort_index().ffill()


def series_smooth(self: pd.Series,
                  period: int = 30,
                  method: str = 'mean') -> pd.Series:
    s_raw = self.sort_index()
    """平滑值（移动平均）"""
    if method == 'mean':
        return self.sort_index().rolling(window=period, min_periods=1).mean()
    elif method == 'median':
        return self.sort_index().rolling(window=period, min_periods=1).median()
    else:
        raise ValueError(f"平滑方法错误：{method}，仅支持 mean 和 median")


def series_diff(self: pd.Series,
                period: int = 1) -> pd.Series:
    """差值特征：当前值与前一值的差值"""
    return self.sort_index().diff(periods=period)


def series_bias(self: pd.Series,
                period: int = 0,
                base_window: int = 30,
                method: str = 'mean') -> pd.Series:
    """偏差值：当前窗口均值与基准均值的差值"""

    # TODO: 目前先拒绝控制填充，通过min_periods保证非空值至少和period-1一样
    s_raw = self.sort_index()
    # STEP 1: 计算基准均值
    if len(s_raw) <= base_window:
        logger.warning(f"偏差特征计算时：当前窗口长度: {len(s_raw)} < 基准窗口长度: {base_window}")
        if method == 'mean':
            baseline = s_raw.mean()
        elif method == 'median':
            baseline = s_raw.median()
        else:
            raise ValueError(f"偏差方法错误：{method}，仅支持 mean 和 median")
    else:
        if method == 'mean':
            baseline = s_raw.rolling(window=base_window, min_periods=base_window - 1).mean()
        elif method == 'median':
            baseline = s_raw.rolling(window=base_window, min_periods=base_window - 1).median()
        else:
            raise ValueError(f"偏差方法错误：{method}，仅支持 mean 和 median")
    # STEP 2: 计算偏差值返回
    if period == 0:
        return s_raw - baseline
    else:
        if method == 'mean':
            return s_raw.rolling(window=period, min_periods=period - 1).mean() - baseline
        elif method == 'median':
            return s_raw.rolling(window=period, min_periods=period - 1).median() - baseline
        else:
            raise ValueError(f"偏差方法错误：{method}，仅支持 mean 和 median")


def series_linear_slope(self: pd.Series,
                        period: int = 3) -> pd.Series:
    """斜率特征：使用线性拟合方法"""
    s_raw = self.sort_index()
    return s_raw.rolling(window=period, min_periods=period).apply(lambda x: np.polyfit(range(len(x)), x, 1)[0])


def series_sen_slope(self: pd.Series,
                     period: int = 5,
                     alpha: float = 0.75,
                     p_thre: float = 0.25) -> pd.Series:
    """斜率特征：使用 Sen's slope 方法"""
    from scipy.stats import theilslopes, norm

    def mann_kendall_test(np_arr: np.ndarray) -> Tuple[float, float]:
        """
        Mann-Kendall trend test for a given data sequence x.
        Args:
            x: numpy array of data sequence.
        Returns:
            trend: The calculated trend (positive, negative or no trend).
            p_value: The p-value of the test.
        """
        n = len(np_arr)
        i, j = np.triu_indices(n, k=1)  # Create meshgrid of indices

        # Sum up signs of differences as test statistic
        s = np.sum(np.sign(np_arr[j] - np_arr[i]))

        # Calculate the variance of the test statistic.
        var_s = (n * (n - 1) * (2 * n + 5)) / 18

        # Calculate the standardized test statistic.
        z = np.sign(s) * (np.abs(s) - 1) / np.sqrt(var_s)

        # Calculate the p-value of the test.
        p_value = 2 * (1 - norm.cdf(abs(z)))

        return z, p_value

    def cal_sen_slope(np_arr: np.ndarray, alpha: float, p_thre: float) -> float:
        # 斜率计算
        slope, intercept, low_slope, high_slope = theilslopes(y=np_arr, x=None, alpha=alpha)

        # 特殊情况的斜率修正：对于四天一次的分子比测量，如[2.15,2.15,2.15,2.15,2.25], 此时slope=0, 但存在趋势
        if slope == 0 and low_slope * high_slope >= 0:
            slope = (low_slope + high_slope) / 2

        # 趋势显著性检验
        z, p_value = mann_kendall_test(np_arr)

        # 结合sen_slope自身的显著性结果，和 man_kendall_test 的显著性结果，综合判断是否存在趋势
        if low_slope * high_slope >= 0 and p_value < p_thre:
            return slope
        else:
            return 0

    # TODO: 目前Sen's Slope特征先强制填充，避免计算错误
    s_raw = self.sort_index().ffill()
    return s_raw.rolling(window=period, min_periods=2).apply(cal_sen_slope, args=(alpha, p_thre), raw=True)


def series_strict_trend(self: pd.Series,
                        period: int = 3) -> pd.Series:
    """趋势特征：严格趋势判断"""

    def cal_strict_trend(np_arr: np.ndarray) -> float:
        np_diff = np.diff(np_arr)
        if np.all(np_diff > 0):
            return 1
        elif np.all(np_diff < 0):
            return -1
        else:
            return 0

    # TODO: 目前严格趋势特征先强制填充，避免计算错误
    s_raw = self.sort_index().ffill()
    if period < 3:
        raise ValueError(f"严格趋势特征计算时：当前窗口长度: {period} < 最小窗口长度: 3")
    else:
        return s_raw.rolling(window=period, min_periods=period).apply(cal_strict_trend, raw=True)


def series_soft_trend(self: pd.Series,
                      period: int = 3) -> pd.Series:
    """趋势特征：软趋势判断"""

    def cal_soft_trend(np_arr: np.ndarray) -> float:
        np_diff = np.diff(np_arr)
        if np.all(np_diff >= 0) and np_diff[-1] > 0:
            return 1
        elif np.all(np_diff <= 0) and np_diff[-1] < 0:
            return -1
        else:
            return 0

    # TODO: 目前严格趋势特征先强制填充，避免计算错误
    s_raw = self.sort_index().ffill()
    if period < 3:
        raise ValueError(f"软趋势特征计算时：当前窗口长度: {period} < 最小窗口长度: 3")
    else:
        return s_raw.rolling(window=period, min_periods=period).apply(cal_soft_trend, raw=True)




def series_max(self: pd.Series, period: int = 3) -> pd.Series:
    """最大值特征：指定窗口内的最大值"""
    return self.sort_index().rolling(window=period, min_periods=period).max()


def series_min(self: pd.Series, period: int = 3) -> pd.Series:
    """最小值特征：指定窗口内的最小值"""
    return self.sort_index().rolling(window=period, min_periods=period).min()


def series_dmax(self: pd.Series, period: int = 3) -> pd.Series:
    """差分后最大值特征：对差分序列取最大值"""
    return self.sort_index().diff(periods=1).rolling(window=period, min_periods=period).max()


def series_dmin(self: pd.Series, period: int = 3) -> pd.Series:
    """差分后最小值特征：对差分序列取最小值"""
    return self.sort_index().diff(periods=1).rolling(window=period, min_periods=period).min()


def series_count(self: pd.Series, period: int = 3) -> pd.Series:
    """计数特征：指定窗口内的非空值数量"""
    return self.sort_index().rolling(window=period, min_periods=period).count()


def series_q05(self: pd.Series, period: int = 3) -> pd.Series:
    """5%分位数特征：指定窗口内的5%分位数值"""
    return self.sort_index().rolling(window=period, min_periods=period).quantile(0.05)


def series_q95(self: pd.Series, period: int = 3) -> pd.Series:
    """95%分位数特征：指定窗口内的95%分位数值"""
    return self.sort_index().rolling(window=period, min_periods=period).quantile(0.95)


def series_median(self: pd.Series, period: int = 3) -> pd.Series:
    """中位数特征：指定窗口内的中位数"""
    return self.sort_index().rolling(window=period, min_periods=period).median()


def series_mean(self: pd.Series, period: int = 3) -> pd.Series:
    """均值特征：指定窗口内的均值"""
    return self.sort_index().rolling(window=period, min_periods=period).mean()

