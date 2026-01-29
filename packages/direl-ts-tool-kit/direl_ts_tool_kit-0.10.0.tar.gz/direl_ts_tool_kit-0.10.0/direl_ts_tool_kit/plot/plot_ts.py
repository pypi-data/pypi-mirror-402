import numpy as np
import pandas as pd
from .plot_style import *
from scipy.stats import pearsonr
from scipy.signal import periodogram


def plot_time_series(
    df_ts,
    variable,
    units="",
    color="BLUE_LINES",
    time_unit="Year",
    rot=90,
    auto_format_label=True,
):
    """
    Plots a time series with custom styling and dual-level grid visibility.

    This function automatically sets major and minor time-based locators
    on the x-axis based on the specified time unit, and formats the y-axis
    to use scientific notation.

    Parameters
    ----------
    df_ts : pd.DataFrame
        The DataFrame containing the time series data. Must have a DatetimeIndex.
    variable : str
        The name of the column to plot. The label is automatically formatted
        (e.g., 'total_sales' becomes 'Total Sales').
    units : str, optional
        Units to display next to the variable name on the y-axis (e.g., 'USD').
        Defaults to "".
    color : str, optional
        Key corresponding to the line color in the global 'paper_colors' dictionary.
        Defaults to "BLUE_LINES".
    time_unit : str, optional
        The time granularity of the data to define x-axis tick locators.
        Options include 'Year', 'Month', 'Weekday', 'Day' or 'Hour'. Defaults to "Year".
    rot : int, optional
        Rotation angle (in degrees) for the x-axis tick labels. Defaults to 90.
    auto_format_label : bool, optional
        Used internally for label formatting logic. Defaults to True.

    Returns
    -------
    matplotlib.figure.Figure
        The generated matplotlib figure object.

    Notes
    -----
    Major grid lines are displayed with a dashed line ('--'), and minor grid
    lines are displayed with a dotted line (':') for detailed temporal analysis.

        Available Colors
    ----------------
    The 'color' parameter accepts any key from the 'paper_colors' dictionary.

    Lines: 'BLUE_LINES', 'ORANGE_LINES', 'GREEN_LINES', 'RED_LINES',
           'GRAY_LINES', 'PURPLE_LINES', 'MAROON_LINES', 'GOLD_LINES'.

    Bars:  'BLUE_BARS', 'ORANGE_BARS', 'GREEN_BARS', 'RED_BARS',
           'GRAY_BARS', 'PURPLE_BARS', 'MAROON_BARS', 'GOLD_BARS'.
    """

    fig, ax = plt.subplots()
    ax.plot(df_ts.index, df_ts[variable], linewidth=3, color=paper_colors[color])

    if "-" in variable:
        variable = "-".join(
            [
                j.title() if i == 0 else j.lower()
                for i, j in enumerate(variable.split("-"))
            ]
        )
    elif "_" in variable:
        variable = " ".join(
            [
                j.title() if i == 0 else j.lower()
                for i, j in enumerate(variable.split("_"))
            ]
        )
    else:
        variable = (
            " ".join(
                [
                    j.title() if i == 0 else j.lower()
                    for i, j in enumerate(variable.split())
                ]
            )
            if auto_format_label
            else variable
        )

    ax.set(xlabel=f"{time_unit}", ylabel=f"{variable} {units}")
    ax.ticklabel_format(style="sci", axis="y", scilimits=(0, 0))

    if time_unit == "Year":
        ax.xaxis.set_major_locator(mdates.YearLocator())
        ax.xaxis.set_minor_locator(mdates.MonthLocator())

    if time_unit == "Month":
        ax.xaxis.set_major_locator(mdates.MonthLocator())
        ax.xaxis.set_minor_locator(mdates.WeekdayLocator())

    if time_unit == "Weekday":
        ax.xaxis.set_major_locator(mdates.WeekdayLocator())
        ax.xaxis.set_minor_locator(mdates.DayLocator())

    if time_unit == "Day":
        ax.xaxis.set_major_locator(mdates.DayLocator())
        ax.xaxis.set_minor_locator(mdates.HourLocator())

    if time_unit == "Hour":
        ax.xaxis.set_major_locator(mdates.HourLocator())
        ax.xaxis.set_minor_locator(mdates.MinuteLocator())

    ax.tick_params(axis="x", rotation=rot)
    ax.grid(which="both")
    ax.grid(which="minor", alpha=0.6, linestyle=":")
    ax.grid(which="major", alpha=0.8, linestyle="--")

    return fig


def plot_forecast(
    df_hist,
    df_ts,
    variable,
    units="",
    color_hist="BLUE_LINES",
    color_forecast="RED_LINES",
    time_unit="Year",
    rot=90,
    auto_format_label=True,
):
    """
    Plots historical data alongside a forecast with a shaded confidence interval.

    This function combines a historical time series with a forecast period,
    automatically formatting axes, labels, and applying professional styling.
    It expects the forecast DataFrame to include lower and upper bound columns
    named '{variable}_lower' and '{variable}_upper'.

    Parameters
    ----------
    df_hist : pd.DataFrame
        The DataFrame containing historical data. Must have a DatetimeIndex.
    df_ts : pd.DataFrame
        The DataFrame containing the forecast data and confidence intervals.
        Must have a DatetimeIndex.
    variable : str
        The name of the column to plot in both DataFrames.
    units : str, optional
        Units to display next to the variable name on the y-axis (e.g., 'USD').
        Defaults to "".
    color : str, optional
        Key corresponding to the line color for the forecast in the
        global 'paper_colors' dictionary. Defaults to "BLUE_LINES".
    time_unit : str, optional
        The time granularity of the data to define x-axis tick locators.
        Options: 'Year', 'Month', 'Weekday', 'Day' or 'Hour'. Defaults to "Year".
    rot : int, optional
        Rotation angle for the x-axis tick labels. Defaults to 90.
    auto_format_label : bool, optional
        If True, automatically formats the Y-axis label into Title Case.
        Defaults to True.

    Returns
    -------
    matplotlib.figure.Figure
        The generated matplotlib figure object.

    Notes
    -----
    The confidence interval is shaded using 'GRAY_BARS' from the paper_colors
    palette with a transparency of 0.3.
    """

    fig, ax = plt.subplots()

    ax.plot(
        df_hist.index,
        df_hist[variable],
        linewidth=2,
        color=paper_colors[color_hist],
        label="Historical",
    )

    ax.plot(
        df_ts.index,
        df_ts[variable],
        linewidth=3,
        color=paper_colors[color_forecast],
        label="Forecast",
    )

    ax.fill_between(
        df_ts.index,
        df_ts[variable + "_lower"],
        df_ts[variable + "_upper"],
        color=paper_colors["GRAY_BARS"],
        alpha=0.3,
        edgecolor="none",
        label="Confidence Interval",
    )

    temp_variable = variable
    if auto_format_label:
        if "-" in temp_variable:
            temp_variable = "-".join(
                [
                    j.title() if i == 0 else j.lower()
                    for i, j in enumerate(temp_variable.split("-"))
                ]
            )
        elif "_" in temp_variable:
            temp_variable = " ".join(
                [
                    j.title() if i == 0 else j.lower()
                    for i, j in enumerate(temp_variable.split("_"))
                ]
            )
        else:
            temp_variable = " ".join(
                [
                    j.title() if i == 0 else j.lower()
                    for i, j in enumerate(temp_variable.split())
                ]
            )

    ax.set(xlabel=f"{time_unit}", ylabel=f"{temp_variable} {units}")
    ax.ticklabel_format(style="sci", axis="y", scilimits=(0, 0))

    locators = {
        "Year": (mdates.YearLocator(), mdates.MonthLocator()),
        "Month": (mdates.MonthLocator(), mdates.WeekdayLocator()),
        "Weekday": (mdates.WeekdayLocator(), mdates.DayLocator()),
        "Day": (mdates.DayLocator(), mdates.HourLocator()),
        "Hour": (mdates.HourLocator(), mdates.MinuteLocator()),
    }

    if time_unit in locators:
        major, minor = locators[time_unit]
        ax.xaxis.set_major_locator(major)
        ax.xaxis.set_minor_locator(minor)

    ax.tick_params(axis="x", rotation=rot)
    ax.grid(which="both")
    ax.grid(which="minor", alpha=0.6, linestyle=":")
    ax.grid(which="major", alpha=0.8, linestyle="--")
    ax.legend(loc="center left", bbox_to_anchor=(1, 0.5))

    return fig


def plot_interpolation_analysis(
    df_original,
    variable,
    units="",
    method="polynomial",
    order=2,
    imputation_se=None,
    time_unit="Year",
    rot=90,
):
    """
    Performs interpolation on missing data (NaNs) in a specified column and
    plots the result, highlighting the imputed points with confidence intervals
    if the Imputation Standard Error (SE) is provided.

    Parameters
    ----------
    df_original : pd.DataFrame
        The DataFrame containing the original time series data.
    variable : str
        The name of the column to interpolate and plot (e.g., 'LPUE').
    units : str, optional
        Units to display next to the variable name on the y-axis. Defaults to "".
    method : str, optional
        The interpolation method (e.g., 'linear', 'polynomial', 'spline').
        Defaults to 'polynomial'.
    order : int, optional
        The order of the interpolation (required for 'polynomial' or 'spline').
        Defaults to 2.
    imputation_se : pd.Series, float, or None, optional
        The Standard Error (SE) of the imputation. This must be a single value
        or a Series aligned with the DataFrame's index. If None, confidence
        intervals will NOT be plotted. Defaults to None.
    time_unit : str, optional
        The time granularity for x-axis tick locators. Defaults to "Year".
    rot : int, optional
        Rotation angle (in degrees) for the x-axis tick labels. Defaults to 90.

    Returns
    -------
    matplotlib.figure.Figure
        The generated Matplotlib figure object with the plot.
    """

    imputed_mask = df_original[variable].isnull()
    df_interpolated = df_original.copy()
    df_interpolated[variable] = df_interpolated[variable].interpolate(
        method=method, order=order
    )

    color1 = paper_colors["RED_LINES"]
    color2 = paper_colors["GREEN_LINES"]

    col = np.where(imputed_mask, color1, color2)

    fig, ax = plt.subplots()

    if imputation_se is not None:
        df_imputed_only = df_interpolated.copy()
        df_imputed_only.loc[~imputed_mask, variable] = np.nan

        Z_80 = 1.282
        Z_95 = 1.96

        error_80 = Z_80 * imputation_se
        error_95 = Z_95 * imputation_se

        ax.fill_between(
            df_imputed_only.index,
            df_imputed_only[variable] - error_95,
            df_imputed_only[variable] + error_95,
            color=paper_colors["GRAY_BARS"],
            alpha=0.2,
            edgecolor="none",
            label="95% confidence interval",
        )

        ax.fill_between(
            df_imputed_only.index,
            df_imputed_only[variable] - error_80,
            df_imputed_only[variable] + error_80,
            color=paper_colors["GRAY_BARS"],
            alpha=0.4,
            edgecolor="none",
            label="80% confidence interval",
        )

    ax.plot(
        df_interpolated[variable],
        linestyle="-.",
        linewidth=1,
        color=paper_colors["BLUE_LINES"],
    )

    ax.scatter(
        df_interpolated.index,
        df_interpolated[variable],
        color=col,
        s=10,
        linewidth=4,
    )

    ax.set(xlabel=f"{time_unit}", ylabel=f"{variable} {units}")
    ax.ticklabel_format(style="sci", axis="y", scilimits=(0, 0))

    if time_unit == "Year":
        ax.xaxis.set_major_locator(mdates.YearLocator())
        ax.xaxis.set_minor_locator(mdates.MonthLocator())

    if time_unit == "Month":
        ax.xaxis.set_major_locator(mdates.MonthLocator())
        ax.xaxis.set_minor_locator(mdates.WeekdayLocator())

    if time_unit == "Weekday":
        ax.xaxis.set_major_locator(mdates.WeekdayLocator())
        ax.xaxis.set_minor_locator(mdates.DayLocator())

    if time_unit == "Day":
        ax.xaxis.set_major_locator(mdates.DayLocator())
        ax.xaxis.set_minor_locator(mdates.HourLocator())

    if time_unit == "Hour":
        ax.xaxis.set_major_locator(mdates.HourLocator())
        ax.xaxis.set_minor_locator(mdates.MinuteLocator())

    ax.tick_params(axis="x", rotation=rot)
    ax.grid(which="both")
    ax.grid(which="minor", alpha=0.6, linestyle=":")
    ax.grid(which="major", alpha=0.8, linestyle="--")

    legend_elements = [
        Line2D(
            [0],
            [0],
            marker="o",
            color=color2,
            label="Current data",
            linestyle="none",
        ),
        Line2D(
            [0],
            [0],
            marker="o",
            color=color1,
            label="Imputed data",
            linestyle="none",
        ),
    ]
    ax.legend(handles=legend_elements, loc="upper right")

    return fig


def save_figure(
    fig,
    file_name,
    variable_name="",
    path="./",
):
    """
    Saves a Matplotlib figure in three common high-quality formats (PNG, PDF, SVG).

    The function creates a consistent file name structure:
    {path}/{file_name}_{variable_name}.{extension}.

    Parameters
    ----------
    fig : matplotlib.figure.Figure
        The Matplotlib figure object to be saved.
    file_name : str
        The primary name for the file (e.g., 'timeseries_report').
    variable_name : str, optional
        An optional secondary name, often the name of the plotted variable,
        to be appended to the file name. Defaults to "".
    path : str, optional
        The directory path where the figure files will be saved.
        Defaults to the current directory ('./').

    Returns
    -------
    None
    """

    if variable_name:
        base_name = f"{path}/{file_name}_{variable_name}"
    else:
        base_name = f"{path}/{file_name}"

    fig.savefig(f"{base_name}.png")
    fig.savefig(f"{base_name}.pdf")
    fig.savefig(f"{base_name}.svg")


def heat_map(X, y, colors="Blues"):
    """
    Generates a correlation heatmap plot for a set of features and a target variable.

    This function concatenates the feature DataFrame (X) and the target Series (y)
    to compute and visualize the full pairwise correlation matrix using Seaborn.

    Parameters
    ----------
    X : pd.DataFrame
        The DataFrame containing the feature variables.
    y : pd.Series or pd.DataFrame
        The target variable (must be concatenable with X).
    colors : str or matplotlib.colors.Colormap, optional
        The colormap to use for the heatmap, passed to the 'cmap' argument
        in seaborn.heatmap. Defaults to "Blues".

        Note: For standard correlation matrices (which include negative values),
        a diverging colormap (e.g., "coolwarm", "vlag") is usually recommended.

    Returns
    -------
    matplotlib.figure.Figure
        The generated Matplotlib figure object containing the heatmap.

    Notes
    -----
    The heatmap displays the Pearson correlation coefficient rounded to two
    decimal places and includes annotations for improved readability.
    """
    fig, ax = plt.subplots()
    Z = pd.concat([X, y], axis=1)

    ax = sns.heatmap(
        Z.corr(),
        cmap=colors,
        annot=True,
        linewidths=0.5,
        fmt=".2f",
        annot_kws={"size": 10},
    )

    return fig


def corrfunc(x, y, ax=None, **kws):
    """Plot the correlation coefficient in the top left hand corner of a plot."""
    r, _ = pearsonr(x, y)
    ax = ax or plt.gca()
    ax.annotate(f"R = {r:.2f}", xy=(0.1, 0.9), fontsize=25, xycoords=ax.transAxes)


def pair_plot(X, y):
    """
    Generates a cornered pair plot (scatterplot matrix) to visualize relationships
    between features and the target variable.

    The function combines the feature DataFrame (X) and the target Series (y)
    and uses seaborn.pairplot to create a matrix of scatter plots and histograms.
    It focuses on the lower triangular part (corner=True) and includes a
    regression line for trend visualization.

    Parameters
    ----------
    X : pd.DataFrame
        The DataFrame containing the feature variables.
    y : pd.Series or pd.DataFrame
        The target variable (must be concatenable with X).

    Returns
    -------
    matplotlib.figure.Figure
        The generated Matplotlib Figure object containing the cornered pair plot.

    Notes
    -----
    1. **Dependency:** This function requires a previously defined custom function
       `corrfunc` to be available in the local namespace, as it is used via
       `svm.map_lower()`. This custom function is typically used to display
       correlation coefficients (e.g., Pearson's r) in the lower panel.
    2. **Aesthetics:** Uses a regression line (`kind="reg"`) with custom color
       (RED_LINES) to highlight linear relationships.
    3. **Output:** The returned Figure object can be manipulated further
       or saved using methods like `fig.savefig()`.
    """
    Z = pd.concat([X, y], axis=1)
    svm = sns.pairplot(
        Z,
        corner=True,
        kind="reg",
        plot_kws={"line_kws": {"color": paper_colors["RED_LINES"]}},
    )
    svm.map_lower(corrfunc)

    fig = svm.fig

    return fig


def plot_histogram(df, variable, units="", density=True, color="BLUE_BARS", bins=30):
    """
    Generates a histogram plot for a specified numerical variable.

    The plot visualizes the distribution of the data, with the Y-axis dynamically
    labeled as 'Density' or 'Count' based on the `density` parameter.

    Parameters
    ----------
    df : pd.DataFrame
        The DataFrame containing the data to be plotted.
    variable : str
        The name of the column in 'df' whose distribution will be plotted.
    units : str, optional
        Units to display next to the variable name on the X-axis. Defaults to "".
    density : bool, optional
        If True (default), the Y-axis is scaled to a Probability Density,
        meaning the area under the bars sums to 1. If False, the Y-axis
        displays the raw count of observations per bin.
    color : str, optional
        Key corresponding to the bar color in the global 'paper_colors' dictionary
        (e.g., "BLUE_BARS"). Defaults to "BLUE_LINES".
    bins : int or sequence, optional
        The number of equal-width bins in the range to divide the data.
        Can be an integer (default is 30) or a sequence specifying the bin edges.

    Returns
    -------
    matplotlib.figure.Figure
        The generated Matplotlib Figure object containing the histogram.

    Notes
    -----
    The plot applies a fixed style (alpha=0.7, white edge-color) and grid
    for visual consistency.
    """
    fig, ax = plt.subplots()

    ax.hist(
        df[variable],
        bins=bins,
        density=density,
        alpha=0.7,
        color=paper_colors[color],
        edgecolor="white",
    )

    ax.set_xlabel(f"{variable} {units}")

    if density:
        ax.set_ylabel("Density")
    else:
        ax.set_ylabel("Count")

    ax.grid(alpha=0.8, linestyle="--")

    return fig


def plot_data_boxplot(
    df, variable=None, x_label="", y_label="", grid=False, notch=False
):
    """
    Generates a boxplot visualization, either for all numerical columns in the
    DataFrame or for a single specified variable.

    The function applies consistent styling for the boxes, outliers, and median
    lines using predefined colors from 'paper_colors'.

    Parameters
    ----------
    df : pd.DataFrame
        The input DataFrame containing the data to be plotted.
    variable : str, optional
        The column name of the variable to plot.
        - If None (default), boxplots for all numerical columns in the DataFrame
          are generated side-by-side.
        - If a string, a single boxplot for that column is generated.
    x_label : str, optional
        The label for the X-axis. Defaults to "".
    y_label : str, optional
        The label for the Y-axis. Defaults to "".
    grid : bool, optional
        If True, display the grid lines on the plot. This parameter is only
        effective when plotting **all** variables (when `variable` is None).
        Defaults to False.
    notch : bool, optional
        If True, draw a notch around the median. This parameter is only
        effective when plotting **all** variables (when `variable` is None).
        Defaults to False.

    Returns
    -------
    matplotlib.figure.Figure
        The generated Matplotlib Figure object containing the boxplot(s).

    Notes
    -----
    The boxplot uses the following fixed style parameters:
    - **Box Line Color:** BLUE_LINES
    - **Outlier Marker:** 'o' (marker size 12)
    - **Median Line Color:** GREEN_LINES

    When plotting a single variable (`variable` is set), the `grid` and
    `notch` parameters are internally forced to **False**.
    """
    boxprops = dict(linewidth=4, color=paper_colors["BLUE_LINES"])
    flierprops = dict(marker="o", markersize=12)
    medianprops = dict(linewidth=4, color=paper_colors["GREEN_LINES"])

    fig, ax = plt.subplots()

    if not variable:
        ax = df.boxplot(
            grid=grid,
            notch=notch,
            boxprops=boxprops,
            flierprops=flierprops,
            medianprops=medianprops,
        )
    else:
        ax = df[[variable]].boxplot(
            grid=False,
            notch=False,
            boxprops=boxprops,
            flierprops=flierprops,
            medianprops=medianprops,
        )

    ax.set_xlabel(f"{x_label}")
    ax.set_ylabel(f"{y_label}")
    ax.tick_params(axis="x")

    return fig


def plot_periodogram(
    ts,
    detrend="linear",
    ax=None,
    fs=365.0,
    color="BLUE_LINES",
):
    """
    Plots the power spectrum (periodogram) of a time series to identify
    dominant frequencies (periodicity).

    Parameters
    ----------
    ts : pd.Series or np.ndarray
        The time series data to analyze.
    detrend : str, optional
        Method to remove the linear trend ('linear' or 'constant'). Defaults to 'linear'.
    ax : matplotlib.axes.Axes, optional
        Existing Axes to draw the plot on. If None, a new figure and axes are created.
    fs : float, optional
        The sampling frequency of the time series (cycles per unit of time).
        Default value 365.0 assumes daily data, leading to frequencies in cycles/year.
    color : str, optional
        Key corresponding to the line color in the global 'paper_colors' dictionary.
        Defaults to "BLUE_LINES".

    Returns
    -------
    matplotlib.figure.Figure
        The generated Matplotlib Figure object.

    Notes
    -----
    The X-axis labels are hardcoded to common periodicities (Annual, Monthly, Weekly)
    and assume a sampling frequency of 365.0 (daily data).
    """

    freqencies, spectrum = periodogram(
        ts,
        fs=fs,
        detrend=detrend,
        window="boxcar",
        scaling="spectrum",
    )

    if ax is None:
        fig, ax = plt.subplots()
    else:
        fig = ax.figure

    ax.step(freqencies, spectrum, linewidth=3, color=paper_colors[color])
    ax.set_xscale("log")
    ax.set_xticks([1, 2, 4, 6, 12, 26, 52, 104])

    ax.set_xticklabels(
        [
            "Annual (1)",
            "Semiannual (2)",
            "Quarterly (4)",
            "Bimonthly (6)",
            "Monthly (12)",
            "Biweekly (26)",
            "Weekly (52)",
            "Semiweekly (104)",
        ],
        rotation=90,
    )

    ax.ticklabel_format(axis="y", style="sci", scilimits=(0, 0))
    ax.set_ylabel("Variance")
    ax.grid(alpha=0.8, linestyle="--")

    return fig
