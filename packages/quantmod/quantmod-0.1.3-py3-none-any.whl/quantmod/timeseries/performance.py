import numpy as np
import pandas as pd


def periodReturn(
    data: pd.DataFrame | pd.Series, period: str = None
) -> pd.DataFrame | pd.Series:
    """
    Calculates periodic log returns. 
    Updated for 2026 pandas frequency aliases (ME, QE, YE).
    
    Parameters
    ----------
    data : pd.DataFrame | pd.Series
        price data
    period : str, optional
        None, defaults to daily frequency
        Specify W, M, Q, or A for weekly, monthly, quarterly, and annual frequency

    Returns
    -------
    pd.Series or pd.DataFrame
    Log returns at the specified frequency. If period="all",
    returns a single-row DataFrame summarizing multiple horizons.
    """
    if not isinstance(data, (pd.DataFrame, pd.Series)):
        raise ValueError("Input must be a pandas DataFrame or Series")
    
    # Resampling requires a time-based index
    if period is not None and period != "all":
        if not isinstance(data.index, (pd.DatetimeIndex, pd.PeriodIndex)):
            raise ValueError(
                "Data must have a DatetimeIndex or PeriodIndex for resampling"
            )

    # Mapping of input period to pandas frequency aliases
    # Using 'ME', 'QE', 'YE' to follow modern pandas standards
    freq_map = {"W": "W", "M": "ME", "Q": "QE", "A": "YE", "Y": "YE"}

    if period is None:
        # Standard daily log return
        return np.log(data).diff()

    elif period in freq_map:
        # Resample to the end of the period, then calculate log return
        resampled_data = data.resample(freq_map[period]).last()
        return np.log(resampled_data).diff()

    elif period == "all":
        if not isinstance(data, pd.Series):
            raise ValueError("Please pass a Series for period 'all'")
        
        # Construct summary using recursive calls or defined helpers
        return pd.DataFrame({
            "daily": periodReturn(data).iloc[-1],
            "weekly": periodReturn(data, "W").iloc[-1],
            "monthly": periodReturn(data, "M").iloc[-1],
            "quarterly": periodReturn(data, "Q").iloc[-1],
            "annual": periodReturn(data, "A").iloc[-1],
        }, index=[data.index[-1]])

    else:
        raise ValueError(f"Invalid period '{period}' provided.")
    

def dailyReturn(data: pd.DataFrame | pd.Series) -> pd.DataFrame | pd.Series:
    """Calculates daily log returns."""
    return periodReturn(data)


def weeklyReturn(data: pd.DataFrame | pd.Series) -> pd.DataFrame | pd.Series:
    """Calculates weekly log returns."""
    return periodReturn(data, period="W")


def monthlyReturn(data: pd.DataFrame | pd.Series) -> pd.DataFrame | pd.Series:
    """Calculates monthly log returns."""
    return periodReturn(data, period="M")


def quarterlyReturn(data: pd.DataFrame | pd.Series) -> pd.DataFrame | pd.Series:
    """Calculates quarterly log returns."""
    return periodReturn(data, period="Q")


def annualReturn(data: pd.DataFrame | pd.Series) -> pd.DataFrame | pd.Series:
    """Calculates annual log returns."""
    return periodReturn(data, period="A")


def allReturn(data: pd.Series) -> pd.DataFrame:
    """Returns a snapshot of latest log returns across multiple horizons."""
    return periodReturn(data, period="all")


def rollingReturn(
    data: pd.DataFrame | pd.Series, window: int = 10
) -> pd.DataFrame | pd.Series:
    """Calculates rolling log returns over the specified window."""
    return dailyReturn(data).rolling(window).sum()


def cagr(returns: pd.Series, intra_period: int = 1, is_log: bool = False) -> float:
    """
    Compounded Annual Growth Rate (CAGR) is the annual rate of return

    Parameters
    ----------
    returns : pd.Series
        price series
    intra_period : int, optional
        period of intra-period returns, defaults to 1 for annual timeframe
    is_log : bool, optional
        defaults to False if its simple return

    Returns
    -------
    float
        returns CAGR for the specified period

    Notes
    -----
        CAGR = (Ending Value / Starting Value)^(1/n) - 1

            Ending Value = Begging Value
            Starting Value = Ending Value
            n = period of intra-period returns
    """

    if is_log:
        cumulative_returns = np.exp(returns.sum())  # for log returns
        years = len(returns) / (252 * intra_period)
        return (cumulative_returns.iloc[-1]) ** (1 / years) - 1
    else:
        cumulative_returns = (1 + returns).cumprod()  # for simple returns

    years = len(returns) / (252 * intra_period)
    return (cumulative_returns.iloc[-1]) ** (1 / years) - 1


def volatility(returns: pd.Series, intra_period: int = 1) -> float:
    """
    Annualized volatility is key risk metrics

    Parameters
    ----------
    returns : pd.Series
        price series
    intra_period : int, optional
        period of intra-period returns, defaults to 1 for annual timeframe

    Returns
    -------
    float
        returns annualized volatility

    Notes
    -----
        Annualization is achieved by multiplying volatility with square root of
        a) 252 to annualize daily volatility
        b) 52 to annualize weekly volatility
        c) 12 to annualize monthly volatility
    """
    return returns.std() * np.sqrt(252 * intra_period)


def sharpe(returns: pd.Series, is_log: bool = False, rf: float = 0.0) -> float:
    """
    Sharpe ratio is the average return earned in excess of the risk free return
    for every unit of volatility. This is one of the most widely used meausre of
    risk adjusted return. Sharpe ration greater than 1 is considered to be good.

    Parameters
    ----------
    returns : pd.Series
        price series
    is_log : bool, optional
        defaults to False if its simple return
    rf : float, optional
        RiskFree rate of return, defaults to 0.

    Returns
    -------
    float
        returns sharpe ratio

    Notes
    -----
        Sharpe Ratio = (Expected Return - RiskFree Return) / Volatility of Returns
    """
    return (cagr(returns, is_log=False) - rf) / volatility(returns)


def maxdd(returns: pd.Series, is_log: bool = False) -> float:
    """
    A maximum drawdown (MDD) is an indicator of downside risk and measures the
    largest percentage drop of the cumulative return over a specified time period.

    Parameters
    ----------
    returns : pd.Series
        price series
    is_log : bool, optional
        defaults to False if its simple return

    Returns
    -------
    float
        returns MDD for the specified period in percentage

    Notes
    -----
        It observes the maximum loss from a peak to a trough of a portfolio before
        a new peak is attained.

        MDD = (Peak Value - Lowest Value) / Peak Value

            Peak Value = Highest Value of the cumulative return
            Lowest Value = Lowest Value of the cumulative return
    """
    if is_log:
        cumulative_returns = np.exp(returns.sum())  # for log returns
    else:
        cumulative_returns = (1 + returns).cumprod()  # for simple returns

    drawdown_percentage = (
        cumulative_returns.cummax() - cumulative_returns
    ) / cumulative_returns.cummax()
    return drawdown_percentage.max()


def calmar(returns: pd.Series, is_log: bool = False) -> float:
    """
    Ratio of compounded annual growth rate and maximum drawdown. It is a measure
    of risk adjusted return. Lower the ratio, the worse the performance on a
    risk-adjusted basis.

    Parameters
    ----------
    returns : pd.Series
        price series
    is_log : bool, optional
        defaults to False if its simple return

    Returns
    -------
    float
        returns calmar ratio

    Notes
    -----
        Calmar Ratio = CAGR / MDD

        CAGR = (Ending Value / Starting Value)^(1/n) - 1
        MDD = (Peak Value - Lowest Value) - Peak Value
    """
    return cagr(returns, is_log=False) / maxdd(returns, is_log=False)
