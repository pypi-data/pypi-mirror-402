import numpy as np
import pandas as pd


def parse_datetime_index(df_raw, date_column="date", format=None):
    """
    Parses a specified column into datetime objects and sets it as the DataFrame index.

    This function prepares raw data for time series analysis by ensuring the
    DataFrame is indexed by the correct datetime type.

    Parameters
    ----------
    df_raw : pd.DataFrame
        The raw DataFrame containing the data, including the column with date strings.
    date_column : str, optional
        The name of the column in 'df_raw' that contains the date/time information.
        Defaults to "date".
    format : str, optional
        The explicit format string (e.g., '%Y%m%d', '%Y-%m-%d %H:%M:%S')
        to parse the dates, passed to `pd.to_datetime`. If None (default),
        Pandas attempts to infer the format automatically.

    Returns
    -------
    df_ts : pd.DataFrame
        A copy of the original DataFrame with the specified date column removed
        and set as the DatetimeIndex. The returned DataFrame is ready for
        time series operations.
    """
    if not format:
        date_parsed = pd.to_datetime(df_raw[date_column])
    else:
        date_parsed = pd.to_datetime(df_raw[date_column], format=format)

    df_ts = df_raw.copy()
    df_ts.drop(columns=[date_column], inplace=True)
    df_ts.set_index(date_parsed, inplace=True)

    return df_ts


def generate_dates(df_ts, freq="MS"):
    """
    Generates a continuous DatetimeIndex covering the time span of the input DataFrame.

    The function determines the start and end dates from the existing DataFrame index
    and creates a new, regular date sequence based on the specified frequency.

    Parameters
    ----------
    df_ts : pd.DataFrame
        The time series DataFrame whose index determines the start and end of the
        new date range.
    freq : str, optional
        The frequency of the generated dates (e.g., 'D' for daily, 'MS' for Month Start).
        Defaults to "MS" (Month Start).

    Returns
    -------
    pd.DatetimeIndex
        A new DatetimeIndex spanning from the first index entry to the last index entry
        of 'df_ts', using the specified frequency.

    Notes
    -----
    The function relies on the index of 'df_ts' to find the boundaries. It explicitly
    sorts the index first to ensure the earliest and latest dates are correctly identified,
    regardless of the current DataFrame order.
    """
    df_ts.sort_index(inplace=True)
    start_date = df_ts.index[0]
    end_date = df_ts.index[-1]

    dates = pd.date_range(start=start_date, end=end_date, freq=freq)

    return dates


def reindex_and_aggregate(df_ts, column_name, freq="MS"):
    """
    Re-indexes a time series DataFrame to a regular frequency, aggregates values,
    and introduces NaN for missing time steps.

    This function first identifies the time range from the original (potentially irregular)
    index, aggregates data if necessary (e.g., if multiple entries exist per time step),
    and then merges the data onto a complete date range, effectively filling gaps
    with NaN values.

    Parameters
    ----------
    df_ts : pd.DataFrame
        The input DataFrame. It is assumed that the index contains the date information
        (though the function currently resets and uses a 'date' column name internally
        due to the line `groupby(["date"])`).
    column_name : str
        The name of the column containing the values to be aggregated and re-indexed.

    Returns
    -------
    pd.DataFrame
        A new DataFrame with a complete, regular DatetimeIndex (set by the
        frequency used in generate_dates, typically 'MS'), and the aggregated
        values, where missing time steps are represented by NaN.

    Notes
    -----
    1. **Dependency:** This function relies on the external function `generate_dates()`
       to create the target date sequence.
    2. **Aggregation:** The use of `.groupby(["date"]).sum()` implies that if
       multiple entries share the same date, their values will be summed.
    3. **Index Handling:** For the merge operation to work, the original index
       is temporarily converted to a column named 'date' (via `reset_index`
       implicitly after the `groupby`).
    """

    date_aux = generate_dates(df_ts, freq=freq)
    df_date = pd.DataFrame({"date_aux": date_aux})
    df_ts = df_ts.groupby(["date"]).sum().reset_index()

    result = pd.merge(df_ts, df_date, left_on="date", right_on="date_aux", how="outer")
    df_ts_new = result[["date_aux", column_name]]
    df_ts_new = df_ts_new.rename(columns={"date_aux": "date"})
    df_ts_new.set_index(df_ts_new["date"], inplace=True)
    df_ts_new.drop(columns=[df_ts_new.index.name], inplace=True)
    df_ts_new.notnull().apply(pd.Series.value_counts)

    return df_ts_new


def remove_outliers_by_threshold(df_ts, column_name, lower_bound, upper_bound):
    """
    Replaces values in a specified column with NaN if they fall outside
    a defined range (outlier removal).

    This function identifies data points that are either below the lower
    bound or above the upper bound and treats them as missing data.

    Parameters
    ----------
    df_ts : pd.DataFrame
        The time series DataFrame (must have a DatetimeIndex).
    column_name : str
        The name of the column where outlier detection will be performed (e.g., 'Temperature').
    lower_bound : float or int
        The minimum acceptable value. Values strictly below this bound are replaced by NaN.
    upper_bound : float or int
        The maximum acceptable value. Values strictly above this bound are replaced by NaN.

    Returns
    -------
    pd.DataFrame
        The DataFrame with outlier values in the specified column replaced by np.nan.
    """
    df_out = df_ts.copy()

    outlier_index = df_out[
        (df_out[column_name] < lower_bound) | (df_out[column_name] > upper_bound)
    ].index

    df_out.loc[outlier_index, column_name] = np.nan

    return df_out
